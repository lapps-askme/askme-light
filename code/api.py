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

import elasticsearch
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse

import config
import document
import elastic
import ranking
from utils import get_valid_pages, prettify
from exceptions import AskmeException, handle_askme_exception
from exceptions import handle_python_exception, handle_elastic_exception

DEBUG = False

INDEX = config.ELASTIC_INDEX

app = FastAPI()


@app.exception_handler(Exception)
async def python_exception_handler(request: Request, exc: Exception):
    return handle_python_exception(request, exc)

@app.exception_handler(AskmeException)
async def askme_exception_handler(request: Request, exc: Exception):
    return handle_askme_exception(request, exc)

@app.exception_handler(elasticsearch.ApiError)
async def elastic_exception_handler(request: Request, exc: Exception):
    return handle_elastic_exception(request, exc)


@app.get('/api')
def home():
    return {
        "description": "AskMe API",
        "help": "Ping the /api/help endpoint for help" }

@app.get('/api/help', response_class=PlainTextResponse)
def home():
    return __doc__

@app.get('/api/error')
def error():
    raise AskmeException(message="The endpoint /api/error always raises an exception")

@app.post('/api/question')
def query(domains: str=None, query: str=None, type=None, page: int=1):
    """Search endpoint for the current web interface."""
    # if page number is larger than MAX_PAGES or less than 1, default to 1
    if page > config.MAX_PAGES or page < 1:
        page = 1
    # create a list from domains string
    if domains:
        domains = domains.split(',')
    if DEBUG:
        print({"domains": domains, "question": query[:50], "page": page})
    result = elastic.search(domains, query, type, page)
    result.hits = ranking.rerank(result.docs)
    if DEBUG:
        print('>>>', result)
    return {
        "query": { "question": query },
        "documents": [doc.as_json(single_doc=False) for doc in result.hits],
        "pages": get_valid_pages(result.total_hits, page) }

@app.get('/api/related/{doc_id}')
def get_related(doc_id: str, pretty: bool = False):
    result = elastic.get_document(doc_id)
    doc = result.first_doc()
    query = f'{doc.title} {doc.terms_as_string()}'
    result = elastic.search(None, query)
    docs = document.DocumentSet(result.docs)
    answer = {
        "query": { "doc_id": doc_id, "terms": query },
        "documents": [d.as_json(single_doc=False) for d in docs.documents] }
    if pretty:
        answer = prettify(answer)
    return answer

@app.get('/api/set')
def get_set(ids: str):
    doc_ids = [identifier for identifier in ids.split(',')]
    result = elastic.get_documents(doc_ids)
    if result.error:
        if DEBUG:
            result.error_details.pp()
        raise AskmeException(
            result.error_details.reason(),
            details=result.error_details.details)
    doc_set = document.DocumentSet(result.docs)
    return {
        "query": { "index": INDEX, "ids": ids },
        "documents": doc_set.documents,
        "terms": doc_set.sorted_terms() }

@app.get('/api/doc/{doc_id}')
def get_document(doc_id: str, pretty: bool = False):
    """Return the document source or an empty dictionary if no such document exists."""
    result = elastic.get_document(doc_id)
    if result.total_hits:
        response = result.docs[0]
        response.terms = response.sorted_terms()
        if pretty:
            response = prettify(response.as_json(single_doc=True))
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
