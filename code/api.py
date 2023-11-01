"""
FastAPI interface to AskMe

Original API:

$ curl http:/127.0.0.1:8000/api
$ curl http:/127.0.0.1:8000/api/doc/xdd-bio/54b4324ee138239d8684aeb2
$ curl http:/127.0.0.1:8000/api/doc/xdd-bio/54b4324ee138239d8684aeb2/abstract
$ curl http:/127.0.0.1:8000/api/search/xdd-bio/particle

Additions for the AskMe website:

$ curl http:/127.0.0.1:8000/api/search?c=xdd-bio&q=flu
$ curl -X POST "http:/127.0.0.1:8000/api/question?domain=xdd-bio&query=flu"
$ curl http://localhost:8000/api/set?index=xdd-bio&ids=5783bcafcf58f176c768f5cc,58102ca2cf58f15425a75367

"""


import json
from fastapi import FastAPI
import elasticsearch
import elastic
import ranking
import document
from utils import error


DEBUG = False


app = FastAPI()


@app.get('/api')
def home():
    return {
        "description": "AskMe API",
        "indices": elastic.indices() }

@app.post('/api/question')
def query(domain: str, query: str):
    """Intended as an endpoint for the current web interface."""
    print({"domain": domain, "query": query[:50]})
    try:
        result = elastic.search(domain, query)
        print('>>>', result)
        return {
            "status": "succes",
            "query": { "question": query },
            "documents": [doc.as_json() for doc in result.hits],
            "duration": result.took }
    except elasticsearch.NotFoundError as e:
        return error(
            "elasticsearch.NotFoundError",
            f"Index {domain} does not exist",
            DEBUG)

@app.get('/api/search')
def search(c: str, q: str):
    """Intended as an endpoint for the current web interface. But note that
    some magic in that site makes sure that only the /api/question endpoint is
    used, this one is probably deprecated."""
    try:
        result = elastic.search(c, q)
        return {
            "status": "success",
            "query": { "index": c, "question": q },
            "documents": result.hits,
            "duration": result.took }
    except Exception as e:
        return error(e.__class__.__name__, e.message, DEBUG)

@app.get('/api/set')
def get_set(index: str, ids: str):
    doc_ids = [identifier for identifier in ids.split(',')]
    print(index, doc_ids)
    result = elastic.get_documents(index, doc_ids)
    doc_set = document.DocumentSet(result.hits)
    return {
        "status": "succes",
        "query": { "index": index, "ids": ids },
        "documents": doc_set,
        "terms": doc_set.get_terms() }

@app.get('/api/doc/{index}/{doc_id}')
def get_document(index: str, doc_id: str):
    """Return the document source or an empty dictionary if no such document exists."""
    result = elastic.get_document(index, doc_id)
    if result.total_hits:
        return result.hits[0].as_json()
    else:
        return {} 

@app.get('/api/doc/{index}/{doc_id}/{field}')
def get_field(index: str, doc_id: str, field: str):
    """Return the value of the field for the document as a field:value pair. Returns
    the empty dictionary if the document does not exist, returns field:null if the
    field does not exist."""
    result = elastic.get_document(index, doc_id)
    if result.total_hits > 0:
        return {field: getattr(result.hits[0], field)}
    else:
        return {}