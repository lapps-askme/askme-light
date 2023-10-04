# AskMe Python

Experiments with getting AskMe components into Python.

Components that we had in Java:

- Interface to ElasticSearch, including Stanford CoreNLP
- Query component
- Ranking component
- AskMe API (the old website)

In addition there is the React web site, which will probably not be ported.


## Requirements

Python requirements:

```bash
$ pip install spacy
$ python -m spacy download en_core_web_sm
$ pip install elasticsearch
$ pip install fastapi uvicorn
```

Having ElasticSearch set up:

```bash
$ docker run -d --rm -p 9200:9200 \
	-v /Users/Shared/data/elasticsearch/data/:/data \
	--user elasticsearch elastic:v1
```

## Running

Running the API:

```bash
$ uvicorn api:app --reload
```



