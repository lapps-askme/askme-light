# AskMe Light

A light-weight API and Flask application for AskMe. This is not fully replacing the Java code in the askme-elastic, askme-query, askme-ranking, askme-web and  askme-web-next repositories in [https://github.com/lappsgrid-incubator](https://github.com/lappsgrid-incubator). In particular, the ranking part is barely implemented yet (but we do run the basic NLP needed for ranking just to make fairer comparisons in performance speed) and the Flask site will never replace the Node.js code in askme-web-next. However, the idea is that askme-web-next will in the future use the API in this repository. See the last section on some motivations for doing this.


### Requirements

Python requirements:

```bash
$ pip install spacy
$ python -m spacy download en_core_web_sm
$ pip install elasticsearch
$ pip install fastapi uvicorn flask
```

Starting ElasticSearch:

```bash
$ docker run -d --rm -p 9200:9200 \
	-v /Users/Shared/data/elasticsearch/data/:/data \
	--user elasticsearch elastic:v1
```
See notes below on ElasticSearch on how to create the Elastic image and how to populate the database.


### Running

Running the API on [http://localhost:8000/](http://localhost:8000/):

```bash
$ uvicorn api:app --reload
```

Running the Flask application on [http://localhost:8000/](http://localhost:8000/):

```bash
$ python app.py
```


### Setting up ElasticSearch

With the following Dockerfile (included in `code/docker/Dockerfile-elastic`)

```docker
FROM docker.elastic.co/elasticsearch/elasticsearch:7.17.13

RUN mkdir /data \
	&& chown elasticsearch /data \
	&& echo "path.data: /data" >> /usr/share/elasticsearch/config/elasticsearch.yml \
	&& echo "discovery.type: single-node" >> /usr/share/elasticsearch/config/elasticsearch.yml

CMD bin/elasticsearch
```

You can create the image needed and run it as follows:

```bash
$ docker build -t elastic:v1 -f code/docker/Dockerfile-elastic .
```

Since no files are copied into the image you can run this from anywhere, as long as the path to the Dockerfile is correct. We are assuming that we have (or will build) an ElasticSearch index at `/Users/Shared/data/elasticsearch/data/`. To start the container you use the command already introduced above:

```bash
$ docker run -d --rm -p 9200:9200 -v /Users/Shared/data/elasticsearch/data/:/data --user elasticsearch elastic
```

Notice the --user option, it is a common error (for me) to forget this, which will not do because ElasticSearch cannot run as root.

One time database population:

```bash
$ curl http://localhost:9200/xdd-bio/_doc/_bulk -o /dev/null \
    -H "Content-Type: application/json" -X POST --data-binary @elastic-biomedical.json
$ curl http://localhost:9200/xdd-geo/_doc/_bulk -o /dev/null \
    -H "Content-Type: application/json" -X POST --data-binary @elastic-geoarchive.json
$ curl http://localhost:9200/xdd-mol/_doc/_bulk -o /dev/null \
    -H "Content-Type: application/json" -X POST --data-binary @elastic-molecular_physics.json
```

This uses the data created by `prepare_elastic.py` in [https://github.com/lapps-xdd/xdd-processing](https://github.com/lapps-xdd/xdd-processing).


### Motivation

We already had a working version in Java, so why doing this? There were a few drawbacks to the original code, none of them related to code quality:

- Simplicity. The original was set up anticipating that some of the indivual components were requiring heavy lifting so the architecture was set up in a flexible way so that we could have many instances of each component all held together by a RabbitMQ server. It turns out that this was not needed.
- Easy of deployment. The original askme-elastic component required us to include the Stanford CoreNLP jar. This, and some other issues, made the Docker image created for the four basic AskMe components (askme-elastic, askme-query, askme-ranking and askme-web) rather big at 2.23GB. The image for the light version is about half the size. And that is with using the full Python image, using a smaller Python image so far seems to work fine as well and then the full AskMe Light image clocks in at 380MB.
- Speed. Partially because of the use of RabibtMQ and partially through our inability to optimize the code, a search on the Java version would take about 6-10 seconds. The light version takes less than a second.
- Maintenance issues. We simply do not deal with Java very well, any little issue took way too long to fix.
