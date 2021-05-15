# RedisEdge realtime video analytics web server
import argparse
import cv2
import io
import numpy as np
import redis
from urllib.parse import urlparse
from PIL import Image, ImageDraw
from flask import Flask, render_template, Response, request
from flask_cors import CORS, cross_origin
import capture
#import init
import json
import logging
import pathlib
import datetime
import glob

logging.basicConfig(level=logging.DEBUG)

class RedisImageStream(object):
    def __init__(self, conn, args):
        self.conn = conn
        self.camera = args.camera
        self.boxes = args.boxes
        self.field = args.field.encode('utf-8') 

    def get_last(self):
        ''' Gets latest from camera and model '''
        p = self.conn.pipeline()
        p.xrevrange(self.camera, count=1)  # Latest frame
        p.xrevrange(self.boxes, count=1)   # Latest boxes
        cmsg, bmsg = p.execute()
        if cmsg:
            last_id = cmsg[0][0].decode('utf-8')
            label = f'{self.camera}:{last_id}'
            data = io.BytesIO(cmsg[0][1][self.field])
            img = Image.open(data)
            if bmsg:
                boxes = np.fromstring(bmsg[0][1]['boxes'.encode('utf-8')][1:-1], sep=',')
                label += ' people: {}'.format(bmsg[0][1]['people'.encode('utf-8')].decode('utf-8'))
                for box in range(int(bmsg[0][1]['people'.encode('utf-8')])):  # Draw boxes
                    x1 = boxes[box*4]
                    y1 = boxes[box*4+1]
                    x2 = boxes[box*4+2]
                    y2 = boxes[box*4+3]
                    draw = ImageDraw.Draw(img)
                    draw.rectangle(((x1, y1), (x2, y2)), width=5, outline='red')
            arr = np.array(img)
            arr = cv2.cvtColor(arr, cv2.COLOR_BGR2RGB)
            cv2.putText(arr, label, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 1, cv2.LINE_AA)
            ret, img = cv2.imencode('.jpg', arr)
            return img.tobytes()
        else:
            with open("data/placeholder.jpg", "rb") as image:
                img = image.read()
                return img

def gen(stream):
    while True:
        try:
            frame = stream.get_last()
            if frame is not None:
                yield (b'--frame\r\n'
                    b'Pragma-directive: no-cache\r\n'
                    b'Cache-directive: no-cache\r\n'
                    b'Cache-control: no-cache\r\n'
                    b'Pragma: no-cache\r\n'
                    b'Expires: 0\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
        except Exception as exception:
            # Output unexpected Exceptions.
            logging.error("Error occurred", exc_info=True)

conn = None
args = None
app = Flask(__name__)
CORS(app, support_credentials=True)

@app.route('/video')
def video_feed():
    return Response(gen(RedisImageStream(conn, args)),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/settings', methods = ['POST'])
@cross_origin(supports_credentials=True)
def settings():
    req = json.loads(request.get_data())
    if not req['source'] and not req['model']:
        logging.error("Error occurred", exc_info=True)
        return 'Please enter a valid video source and/or model', 400


    data = {
        "source": None,
        "model": None
    }

    if('source' in req):
        source = pathlib.Path(req['source'])
        if not source.exists():
            logging.error("Error occurred", exc_info=True)
            return 'Please enter a valid video source', 400
        data['source'] = req['source']

    if('model' in req):
        model = pathlib.Path(req['model'])
        if not model.exists():
            logging.error("Error occurred", exc_info=True)
            return 'Please enter a valid model', 400
        data['model'] = req['model']

    conn.publish('feed', json.dumps(data))
    return json.dumps({'success':True}), 200, {'ContentType':'application/json'} 

@app.route('/peoplestream')
@cross_origin(supports_credentials=True)
def peoplestream():
    people = conn.execute_command('XREVRANGE',  'camera:0:yolo', '+', '-', 'COUNT', 1)
    timestamp =people[0][0].decode('utf-8')
    numberOfPeople = people[0][1][b'people'].decode('utf-8')
    response = {
        "timestamp": timestamp,
        "numberOfPeople": numberOfPeople
    }
    return json.dumps(response), 200, {'ContentType':'application/json'}
    
@app.route('/videos')
@cross_origin(supports_credentials=True)
def videos():
    files = glob.glob("./data/*.mp4")
    return json.dumps(files), 200, {'ContentType':'application/json'}

@app.route('/models')
@cross_origin(supports_credentials=True)
def models():
    files = glob.glob("./models/*.pb")
    return json.dumps(files), 200, {'ContentType':'application/json'}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('camera', help='Input camera stream key', nargs='?', type=str, default='camera:0')
    parser.add_argument('boxes', help='Input model stream key', nargs='?', type=str, default='camera:0:yolo')
    parser.add_argument('--field', help='Image field name', type=str, default='image')
    parser.add_argument('--fmt', help='Frame storage format', type=str, default='.jpg')
    parser.add_argument('-u', '--url', help='Redis URL', type=str, default='redis://127.0.0.1:6379')
    args = parser.parse_args()

    # Set up Redis connection
    url = urlparse(args.url)
    conn = redis.Redis(host="localhost", port="6379")
    if not conn.ping():
        raise Exception('Redis unavailable')
    
    app.run(host='0.0.0.0')
