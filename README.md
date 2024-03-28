# AskMe Light

A light-weight API and Flask application for AskMe. This is replacing the Java code in the askme-elastic, askme-query, askme-ranking and askme-web repositories in [https://github.com/lappsgrid-incubator](https://github.com/lappsgrid-incubator). Some parts of the Java code, in particular the re-ranking, are not fully implemented yet.


### Requirements

Python requirements:

```bash
$ pip install spacy
$ python -m spacy download en_core_web_sm
$ pip install elasticsearch
$ pip install fastapi uvicorn flask
$ pip install pygments
```

You need an ElasticSearch database. Given an ElasticSearch image and a local data directory you can start the ElasticSearch document database as follows (this can take up to a few dozen seconds):

```bash
$ docker run -d --rm -p 9200:9200 \
	-v /Users/Shared/data/elasticsearch/data/:/data --user elasticsearch elastic
```

See below for more details on how to create the Elastic image and populate the database.


### Configuration

To change the configuration edit `code/config.py`. Most settings are just defaults that we thought make sense. But you may need to change the settings that reflect your local ElasticSearch set up:

```python
ELASTIC_HOST = 'localhost'
ELASTIC_PORT = 9200
ELASTIC_INDEX = 'xdd'
ELASTIC_USER = 'askme'
ELASTIC_PASSWORD = 'pw-askme'
```

There are also a couple of settings that make the API sensitive to what properties are in the database. Unfortunately, most of them cannot be edited without some extract work, but it is possible to edit one of them:

```python
SEARCH_FIELDS = ('title', 'abstract', 'content')
```

This defines what fields are searched when querying the database. If the 'content' field has a different name like 'text' or 'body' then you can change that here.


### Running

Running the API on [http://localhost:8000/](http://localhost:8000/):

```bash
$ uvicorn api:app --reload
```

Running the Flask application on [http://localhost:5000/](http://localhost:5000/):

```bash
$ python app.py
```

The Flask application will never look spiffy, it is just there for development purposes.

When you want to use this API from the production AskMe webpage you need to start the Next.js site implemented in [https://github.com/lappsgrid-incubator/askme-web-next](https://github.com/lappsgrid-incubator/askme-web-next).


### Running the API in Docker

To create a Dockerimage for the API do:

```bash
$ docker build -t askme-api -f docker/Dockerfile-api .
```


### Setting up ElasticSearch

With the Dockerfile in `code/docker/Dockerfile-elastic`

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
$ docker build -t elastic -f code/docker/Dockerfile-elastic .
```

Since no files are copied into the image you can run this from anywhere, as long as the path to the Dockerfile is correct. To start the container you use the command already introduced above:

```bash
$ docker run -d --rm -p 9200:9200 -v /Users/Shared/data/elasticsearch/data/:/data --user elasticsearch elastic
```

Notice the --user option, it is a common error (for me) to forget this, which will not do because ElasticSearch cannot run as root. We are assuming that we have an ElasticSearch index at `/Users/Shared/data/elasticsearch/data/`. 

Populating the "xdd" index in the database index:

```bash
$ curl -u elastic:<password> http://localhost:9200/xdd/_doc/_bulk \
    -o /dev/null -H "Content-Type: application/json" \
    -X POST --data-binary @elastic.json
```

We do this for each data drop, which historically have been focused on domains. The `elastic.json` was created by `prepare_elastic.py` in [https://github.com/lapps-xdd/xdd-processing](https://github.com/lapps-xdd/xdd-processing).
