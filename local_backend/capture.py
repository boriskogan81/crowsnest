# RedisEdge realtime video analytics video capture script
import argparse
import cv2
import redis
import time
from urllib.parse import urlparse
import json
import multiprocessing 
import logging
import sys

class SimpleMovingAverage(object):
    ''' Simple moving average '''
    def __init__(self, value=0.0, count=7):
        self.count = int(count)
        self.current = float(value)
        self.samples = [self.current] * self.count

    def __str__(self):
        return str(round(self.current, 3))

    def add(self, value):
        v = float(value)
        self.samples.insert(0, v)
        o = self.samples.pop()
        self.current = self.current + (v-o)/self.count

class Video:
    def __init__(self, infile=0, fps=30.0):
        try: 
            self.isFile = not str(infile).isdecimal()
            print('video: self.isFile', self.isFile)
            self.ts = time.time()
            self.infile = infile
            self.cam = cv2.VideoCapture(self.infile)
            if not self.isFile:
                self.cam.set(cv2.CAP_PROP_FPS, fps)
                self.fps = fps
                # TODO: some cameras don't respect the fps directive
                self.cam.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
                self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)
            else:
                self.fps = self.cam.get(cv2.CAP_PROP_FPS)
                self.sma = SimpleMovingAverage(value=0.1, count=19)
        except error as error:
            # Output expected AssertionErrors.
            logging.error("Error occurred", exc_info=True)
 
    def __iter__(self):
        self.count = -1
        return self

    def __next__(self):
        try:
            self.count += 1
            if not self.fps:
                self.fps = 30.0
            # Respect FPS for files
            if self.isFile:
                delta = time.time() - self.ts
                self.sma.add(delta)
                time.sleep(max(0,(1 - self.sma.current*self.fps)/self.fps))
                self.ts = time.time()

            # Read image
            ret_val, img0 = self.cam.read()
            if not ret_val and self.isFile:
                self.cam.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret_val, img0 = self.cam.read()
            assert ret_val, 'Video Error'

            # Preprocess
            img = img0
            if not self.isFile:
                img = cv2.flip(img, 1)

            return self.count, img
        except AssertionError as error:
            # Output expected AssertionErrors.
            redisLog("Error occurred", exc_info=True)
        except Exception as exception:
            # Output unexpected Exceptions.
            logging.exception("Exception occurred")

    def __len__(self):
        return 0

def load(source, args):
    try:
        conn = redis.Redis(host="localhost", port="6379")
        if not conn.ping():
            raise Exception('Redis unavailable')

        loader = Video(infile=source, fps=30.0)
        for (count, img) in loader:
            _, data = cv2.imencode(args.fmt, img)
            msg = {
                'count': count,
                'image': data.tobytes()
            }
            _id = conn.xadd(args.output, msg, maxlen=args.maxlen)
            if args.verbose:
                print('frame: {} id: {}'.format(count, _id))
            if args.count is not None and count+1 == args.count:
                print('Stopping after {} frames.'.format(count))
                break
    except AssertionError:
        logging.error("Error occurred", exc_info=True)
        raise


if __name__ == '__main__':
    multiprocessing.log_to_stderr(logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument('infile', help='Input file (leave empty to use webcam)', nargs='?', type=str, default=None)
    parser.add_argument('-o', '--output', help='Output stream key name', type=str, default='camera:0')
    parser.add_argument('-u', '--url', help='Redis URL', type=str, default='redis://127.0.0.1:6379')
    parser.add_argument('-w', '--webcam', help='Webcam device number', type=int, default=0)
    parser.add_argument('-v', '--verbose', help='Verbose output', type=bool, default=False)
    parser.add_argument('--count', help='Count of frames to capture', type=int, default=None)
    parser.add_argument('--fmt', help='Frame storage format', type=str, default='.jpg')
    parser.add_argument('--fps', help='Frames per second (webcam)', type=float, default=15.0)
    parser.add_argument('--maxlen', help='Maximum length of output stream', type=int, default=10000)
    args = parser.parse_args()
    url = urlparse(args.url)
    conn = redis.Redis(host="localhost", port="6379")
    if not conn.ping():
            raise Exception('Redis unavailable')

    pubsub = conn.pubsub()
    pubsub.subscribe("feed")
    data = None
    procs = []
    logging.basicConfig(level=logging.DEBUG)

    for message in pubsub.listen():
        logging.info("received pubsub message")
        logging.info(message)
        logging.info(message['type'])
        try:
            if message['type'] == "message":
                data = json.loads(message.get("data"))
                if data: 
                    if data['model']:
                        print('Loading model - ', end='')
                        with open(data['model'], 'rb') as f:
                            model = f.read()
                            res = conn.execute_command('AI.MODELSET', 'yolo:model', 'TF', 'CPU', 'INPUTS', 'input', 'OUTPUTS', 'output', model)
                            print(res)
                    if data['source']:
                        for proc in procs:
                            if proc.is_alive():
                                proc.terminate()
                                proc.join(timeout=0)
                                procs.pop(0)
                        loaderProcess = multiprocessing.Process(target=load, args = (data.get("source"), args,))
                        procs.append(loaderProcess)
                        loaderProcess.start()
                        continue
        except Exception as e:
            logging.error("Error occurred", exc_info=True)

