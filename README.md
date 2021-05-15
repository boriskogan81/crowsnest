# crowsnest

## Project setup
In the main folder, run
```
npm install
```
Open the /dockerized_backend folder and run 
```
docker-compose up
```
In the local_backend folder, run server.py and capture.py

## What does Crowsnest do?
This project is being built for the needs of the Israel Dog Unit, a volunteer search and rescue group which uses trackers, dogs and drones to find and rescue missing people on a weekly basis.

A system for finding missing people in search and rescue drone footage, CrowsNest is built on RedisAI, RedisGears, RedisPubsub and RedisTimeSeries. A management console allows users to select videos (and live video feeds in the near future), and choose different TensorFlow models to process them with.

## How does Crowsnest work?
The user sets the video input and TensorFlow model in the Vue.js front end

The server publishes video and model selection to Redis Pub/Sub: 
```conn.publish('feed', json.dumps(data))```

The video loader, capture.py, previously subscribed to Redis Pub/Sub via ```pubsub.subscribe("feed")``` receives each selection from Redis Pub/Sub (```for message in pubsub.listen():```) and ingests the video into Redis frame-by-frame via ```conn.xadd(args.output, msg, maxlen=args.maxlen)```. If there is an AI model passed, the loader sets it in RedisAI via ```conn.execute_command('AI.MODELSET', 'yolo:model', 'TF', 'CPU', 'INPUTS', 'input', 'OUTPUTS', 'output', model)```
RedisGears receives the settings from Redis and passes them to RedisAI. It downsamples the stream by storing the input frames per second ( ```'TS.INCRBY', 'camera:0:in_fps', 1, 'RESET', 1```), creating a tensor (```redisAI.createTensorFromBlob('FLOAT', [1, IMG_SIZE, IMG_SIZE, 3], img_ba)```), creating a model runner (```redisAI.createModelRunner('yolo:model')```), adding inputs and outputs to it (```redisAI.modelRunnerAddInput(modelRunner, 'input', image_tensor)```/```redisAI.modelRunnerAddOutput(modelRunner, 'output')```), running it (```model_replies = redisAI.modelRunnerRun(modelRunner)```) and then creating a script runner for a PyTorch script and running it: 
```
    scriptRunner = redisAI.createScriptRunner('yolo:script', 'boxes_from_tf')
    redisAI.scriptRunnerAddInput(scriptRunner, model_output)
    redisAI.scriptRunnerAddOutput(scriptRunner)
    script_reply = redisAI.scriptRunnerRun(scriptRunner)
``` 
It gets the bounding boxes:
```
    shape = redisAI.tensorGetDims(script_reply)
    buf = redisAI.tensorGetDataAsBlob(script_reply)
``` 
and stores them back in Redis
```
    shape = redisAI.tensorGetDims(script_reply)
    buf = redisAI.tensorGetDataAsBlob(script_reply)
```
It also stores various profiler data in Redis Streams:
```
    execute('TS.ADD', 'camera:0:people', ref_msec, people)
    execute('TS.INCRBY', 'camera:0:out_fps', 1, 'RESET', 1)
    for name in prf.names:
        current = prf.data[name].current
        execute('TS.ADD', 'camera:0:prf_{}'.format(name), ref_msec, current)
```
 
The server receives the detection boxes and video frames from Redis, superimposes them and passes them to the front end
```
    people = conn.execute_command('XREVRANGE',  'camera:0:yolo', '+', '-', 'COUNT', 1)
```

All of this allows users to change video sources and models on the fly to fit mission requirements
![Diagram](./Diagram.png?raw=true "Diagram")

##Background
I used this project to start filling an ongoing mission requirement, get my feet wet with Python, the Redis stack, AI and computer vision, and compete in the 2021 Redis Hackathon. I used Ajeet Raina's demo (https://github.com/collabnix/redisedge-grafana/ )for a starting point, at his suggestion. 

##Future improvements
1) Adjust server.py to validate live feed URLs-no further changes should be required to ingest live video feeds
2) Build and try out custom TensorFlow models-the current one is not very good at recognizing humans from even a moderate overhead angle, and thermal models need to be developed from existing drone footage
3) Allow multiple video feeds
4) Add audio alerts
5) Deploy to the cloud# crowsnest

## Project setup
In the main folder, run
```
npm install
```
Open the /dockerized_backend folder and run 
```
docker-compose up
```
In the local_backend folder, run server.py and capture.py

## What does Crowsnest do?
This project is being built for the needs of the Israel Dog Unit, a volunteer search and rescue group which uses trackers, dogs and drones to find and rescue missing people on a weekly basis.

A system for finding missing people in search and rescue drone footage, CrowsNest is built on RedisAI, RedisGears, RedisPubsub and RedisTimeSeries. A management console allows users to select videos (and live video feeds in the near future), and choose different TensorFlow models to process them with.

## How does Crowsnest work?
The user sets the video input and TensorFlow model in the Vue.js front end

The server publishes video and model selection to Redis Pub/Sub: 
```conn.publish('feed', json.dumps(data))```

The video loader, capture.py, previously subscribed to Redis Pub/Sub via ```pubsub.subscribe("feed")``` receives each selection from Redis Pub/Sub (```for message in pubsub.listen():```) and ingests the video into Redis frame-by-frame via ```conn.xadd(args.output, msg, maxlen=args.maxlen)```. If there is an AI model passed, the loader sets it in RedisAI via ```conn.execute_command('AI.MODELSET', 'yolo:model', 'TF', 'CPU', 'INPUTS', 'input', 'OUTPUTS', 'output', model)```
RedisGears receives the settings from Redis and passes them to RedisAI. It downsamples the stream by storing the input frames per second ( ```'TS.INCRBY', 'camera:0:in_fps', 1, 'RESET', 1```), creating a tensor (```redisAI.createTensorFromBlob('FLOAT', [1, IMG_SIZE, IMG_SIZE, 3], img_ba)```), creating a model runner (```redisAI.createModelRunner('yolo:model')```), adding inputs and outputs to it (```redisAI.modelRunnerAddInput(modelRunner, 'input', image_tensor)```/```redisAI.modelRunnerAddOutput(modelRunner, 'output')```), running it (```model_replies = redisAI.modelRunnerRun(modelRunner)```) and then creating a script runner for a PyTorch script and running it: 
```
    scriptRunner = redisAI.createScriptRunner('yolo:script', 'boxes_from_tf')
    redisAI.scriptRunnerAddInput(scriptRunner, model_output)
    redisAI.scriptRunnerAddOutput(scriptRunner)
    script_reply = redisAI.scriptRunnerRun(scriptRunner)
``` 
It gets the bounding boxes:
```
    shape = redisAI.tensorGetDims(script_reply)
    buf = redisAI.tensorGetDataAsBlob(script_reply)
``` 
and stores them back in Redis
```
    shape = redisAI.tensorGetDims(script_reply)
    buf = redisAI.tensorGetDataAsBlob(script_reply)
```
It also stores various profiler data in Redis Streams:
```
    execute('TS.ADD', 'camera:0:people', ref_msec, people)
    execute('TS.INCRBY', 'camera:0:out_fps', 1, 'RESET', 1)
    for name in prf.names:
        current = prf.data[name].current
        execute('TS.ADD', 'camera:0:prf_{}'.format(name), ref_msec, current)
```
 
The server receives the detection boxes and video frames from Redis, superimposes them and passes them to the front end
```
    people = conn.execute_command('XREVRANGE',  'camera:0:yolo', '+', '-', 'COUNT', 1)
```

All of this allows users to change video sources and models on the fly to fit mission requirements
![Diagram](./Diagram.png?raw=true "Diagram")

##Background
I used this project to start filling an ongoing mission requirement, get my feet wet with Python, the Redis stack, AI and computer vision, and compete in the 2021 Redis Hackathon. I used Ajeet Raina's demo (https://github.com/collabnix/redisedge-grafana/ )for a starting point, at his suggestion. 

##Future improvements
1) Adjust server.py to validate live feed URLs-no further changes should be required to ingest live video feeds
2) Build and try out custom TensorFlow models-the current one is not very good at recognizing humans from even a moderate overhead angle, and thermal models need to be developed from existing drone footage
3) Allow multiple video feeds
4) Add audio alerts
5) Deploy to the cloud