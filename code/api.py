"""
FastAPI interface to AskMe

$ curl http:/127.0.0.1:8000/search?c=xdd-bio&q=flu
$ curl http:/127.0.0.1:8000/api
$ curl http:/127.0.0.1:8000/api/doc/xdd-bio/54b4324ee138239d8684aeb2
$ curl http:/127.0.0.1:8000/api/doc/xdd-bio/54b4324ee138239d8684aeb2/abstract
$ curl http:/127.0.0.1:8000/api/search/xdd-bio/particle

"""

# TODO:
# - should check the Elastic response for errors


import json
from fastapi import FastAPI
import elastic
import ranking

app = FastAPI()


# The first two were intended to hook up with the Node.js site, but note that the
# some magic in that site makes sure that only the /question endpoint is used.

@app.get('/search')
def search(c: str, q: str):
	print('SEARCH')
	result = elastic.search(c, q)
	return {
		"query": { "question": q },
		"documents": result.hits,
		"duration": result.took }

@app.post('/question')
def search(domain: str, question: str):
	print('QUESTION')
	print({"domain": domain, "question": question[:50]})
	result = elastic.search(domain, question)
	# We cannot just return the hits as we get them because the client has some
	# expectations that I did not want to change yet.
	adapted_hits = []
	for hit in result.hits:
		adapted_hits.append({
			"id": hit.identifier,
			"title": {"text": hit.title},
			"articleAbstract": {"text": hit.summary},
			"score": hit.score,
			"nscore": hit.score,
			"url": hit.url
			})
	return {
		"query": { "question": question },
		"documents": adapted_hits,
		"duration": result.took }


# More general ones, may want to merge the above into here, but requires some 
# changes to askme-web-next

@app.get('/api')
def home():
	return {
		"description": "AskMe API",
		"indices": elastic.indices() }

@app.get('/api/search/{index}/{term}')
def search(index: str, term: str):
	"""Returns the the documents as JSON objects."""
	result = elastic.search(index, term)
	return ranking.rerank(result.hits)

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