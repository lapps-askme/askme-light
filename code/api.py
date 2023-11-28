"""
FastAPI interface to AskMe

Get a document or a particular field of a document:

$ curl http:/127.0.0.1:8000/api/doc/54b4324ee138239d8684aeb2
$ curl http:/127.0.0.1:8000/api/doc/54b4324ee138239d8684aeb2?pretty=true
$ curl http:/127.0.0.1:8000/api/doc/54b4324ee138239d8684aeb2/title

Get a list of documents:

$ curl http://localhost:8000/api/set?ids=5783bcafcf58f176c768f5cc,58102ca2cf58f15425a75367

Get related documents:

$ curl http:/127.0.0.1:8000/api/related/54b4324ee138239d8684aeb2
$ curl http:/127.0.0.1:8000/api/related/54b4324ee138239d8684aeb2?pretty=true

Searching for a term:

$ curl -X POST "http:/127.0.0.1:8000/api/question?query=flu"

Restricting the search to a domain:

$ curl -X POST "http:/127.0.0.1:8000/api/question?domain=biomedical&query=flu"

Getting the second page for a search:

$ curl -X POST "http:/127.0.0.1:8000/api/question?query=flu&page=2"
$ curl -X POST "http:/127.0.0.1:8000/api/question?domain=biomedical&query=flu&page=2"

"""


import json
from fastapi import FastAPI, Response

import config
import elasticsearch
import elastic
import ranking
import document
from utils import error, get_valid_pages


DEBUG = False

INDEX = config.ELASTIC_INDEX

app = FastAPI()


@app.get('/api')
def home():
    return {
        "description": "AskMe API",
        "indices": elastic.indices() }

@app.post('/api/question')
def query(domains: str = None, query: str = None, page: int=1):
    """Search endpoint for the current web interface."""
    # if page number is larger than MAX_PAGES or less than 1, default to 1
    if page > config.MAX_PAGES or page < 1:
        page = 1
    # create a list from domains string
    if domains:
        domains = domains.split(',')
    if DEBUG:
        print({"domains": domains, "question": query[:50], "page": page})
    try:
        result = elastic.search(domains, query, page)
        result.hits = ranking.rerank(result.hits)
        if DEBUG:
            print('>>>', result)
        return {
            "status": "succes",
            "query": { "question": query },
            "documents": [doc.as_json(single_doc=False) for doc in result.hits],
            "duration": result.took,
            "pages": get_valid_pages(result.total_hits, page) }
    except elasticsearch.NotFoundError as e:
        return error(
            "elasticsearch.NotFoundError",
            DEBUG)

@app.get('/api/related/{doc_id}')
def get_related(doc_id: str, pretty: bool = False):
    # first get document title and terms, then the related documents
    result = elastic.get_document(doc_id)
    doc = result.hits[0]
    query = f'{doc.title} {doc.terms_as_string()}'
    result = elastic.search(None, query)
    docs = document.DocumentSet(result.hits)
    answer = {
        "status": "success",
        "query": { "doc_id": doc_id, "terms": query },
        "documents": [d.as_json(single_doc=False) for d in docs.documents] }
    if pretty:
        json_str = json.dumps(answer, indent=2)
        answer = Response(content=json_str, media_type='application/json')
    return answer


@app.get('/api/set')
def get_set(ids: str):
    doc_ids = [identifier for identifier in ids.split(',')]
    result = elastic.get_documents(doc_ids)
    doc_set = document.DocumentSet(result.hits)
    return {
        "status": "succes",
        "query": { "index": INDEX, "ids": ids },
        "documents": doc_set.documents,
        "terms": doc_set.get_terms() }

@app.get('/api/doc/{doc_id}')
def get_document(doc_id: str, pretty: bool = False):
    """Return the document source or an empty dictionary if no such document exists."""
    result = elastic.get_document(doc_id)
    if result.total_hits:
        response = result.hits[0]
        if pretty:
            json_str = json.dumps(response.as_json(single_doc=True), indent=2)
            response = Response(content=json_str, media_type='application/json')
        return response
    else:
        return {} 

@app.get('/api/doc/{doc_id}/{field}')
def get_field(doc_id: str, field: str):
    """Return the value of the field for the document as a field:value pair. Returns
    the empty dictionary if the document does not exist, returns field:null if the
    field does not exist."""
    result = elastic.get_document(doc_id)
    if result.total_hits > 0:
        return {field: getattr(result.hits[0], field)}
    else:
        return {}