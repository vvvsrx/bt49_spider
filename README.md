# Run it

Modify this file [spider.py](src/bt49/spiders/spider.py)

Find the username and password and modify its

### Clone this project

`git clone https://github.com/vvvsrx/bt49_spider.git`

`cd bt49_spider`

### Start build docker

`docker build -t bt49_scrapyd:v1 .`

`docker-compose up -d`

### Deploy this spider

`cd src`

`scrapyd-deploy`

### Start this spider

`curl http://localhost:6800/schedule.json -d project=bt49 -d spider=bt49`
