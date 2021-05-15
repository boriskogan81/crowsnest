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
1) The user sets the video input and TensorFlow model in the Vue.js front end
2) The server publishes video and model selection to Redis Pub/Sub
3) The video loader, capture.py, receives the selection from Redis Pub/Sub and ingests the video into Redis frame-by-frame
4) RedisGears receives the settings from Redis and passes them to RedisAI
5) RedisAI passes the detections back to RedisGears, which ingests them into Redis
6) The server receives the detection boxes and video frames from Redis, superimposes them and passes them to the front end
7) All of this allows users to change video sources and models on the fly to fit mission requirements
![Diagram](./Diagram.png?raw=true "Title")

##Background
I used this project to start filling an ongoing mission requirement, get my feet wet with Python, the Redis stack, AI and computer vision, and compete in the 2021 Redis Hackathon. I used Ajeet Raina's demo (https://github.com/collabnix/redisedge-grafana/ )for a starting point, at his suggestion. 

##Future improvements
1) Adjust server.py to validate live feed URLs-no further changes should be required to ingest live video feeds
2) Build and try out custom TensorFlow models-the current one is not very good at recognizing humans from even a moderate overhead angle, and thermal models need to be developed from existing drone footage
3) Allow multiple video feeds
4) Add audio alerts
5) Deploy to the cloud