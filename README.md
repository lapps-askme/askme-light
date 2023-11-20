# AskMe Light

A light-weight API and Flask application for AskMe. This is replacing the Java code in the askme-elastic, askme-query, askme-ranking and askme-web repositories in [https://github.com/lappsgrid-incubator](https://github.com/lappsgrid-incubator). Some parts of the Java code, in particular the re-ranking, are not or not fully implemented yet.


### Requirements

Python requirements:

```bash
$ pip install spacy
$ python -m spacy download en_core_web_sm
$ pip install elasticsearch
$ pip install fastapi uvicorn flask
```

Starting ElasticSearch (this can take up to a few dozen seconds):

```bash
$ docker run -d --rm -p 9200:9200 \
	-v /Users/Shared/data/elasticsearch/data/:/data \
	--user elasticsearch elastic:v1
```
See below for more details on how to create the Elastic image and how to populate the database.


### Running

Running the API on [http://localhost:8000/](http://localhost:8000/):

```bash
$ uvicorn api:app --reload
```

Running the Flask application on [http://localhost:5000/](http://localhost:5000/):

```bash
$ python app.py
```

The Flask application will never look nice, it is just there for development reasons.

When you want to use this from the full AskMe webpage you need to start the Next.js site in [https://github.com/lappsgrid-incubator/askme-web-next](https://github.com/lappsgrid-incubator/askme-web-next). Note that the environment file for that site previously used a Spring Boot API running on port 8080 and that in the current context you want to use 8000.


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

You can create the image needed as follows:

```bash
$ docker build -t elastic:v1 -f code/docker/Dockerfile-elastic .
```

Since no files are copied into the image you can run this from anywhere, as long as the path to the Dockerfile is correct. We are assuming that we have (or will build) an ElasticSearch index at `/Users/Shared/data/elasticsearch/data/`. To start the container you use the command already introduced above:

```bash
$ docker run -d --rm -p 9200:9200 -v /Users/Shared/data/elasticsearch/data/:/data --user elasticsearch elastic
```

Notice the --user option, it is a common error (for me) to forget this, which will not do because ElasticSearch cannot run as root.

Database population, assuming we are calling the database index "xdd":

```bash
$ curl -u elastic:<password> http://localhost:9200/xdd/_doc/_bulk \
    -o /dev/null -H "Content-Type: application/json" \
    -X POST --data-binary @elastic.json
```

We would do this for each data drop, which historically have been focused on domains. The `elastic.json` was created by `prepare_elastic.py` in [https://github.com/lapps-xdd/xdd-processing](https://github.com/lapps-xdd/xdd-processing).
