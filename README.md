# AskMe Python

Creating a light-weight API and Flask application for AskMe.


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


### Running

Running the API on [http://localhost:8000/](http://localhost:8000/):

```bash
$ uvicorn api:app --reload
```

Running the Flask application on [http://localhost:8000/](http://localhost:8000/):

```bash
$ python app.py
```
