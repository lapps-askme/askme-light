import sys, warnings

from elasticsearch import Elasticsearch, ElasticsearchWarning

import config
from document import Document


# Suppressing the security warning
# warnings.filterwarnings("ignore", category=ElasticsearchWarning)
warnings.filterwarnings("ignore", message=open('securitywarning.txt').read().strip())


ES = Elasticsearch([{
		'host': config.ELASTIC_HOST,
		'port': config.ELASTIC_PORT,
		'scheme': 'http'}])

INDEX = config.ELASTIC_INDEX


def indices(index='*'):
	return list(ES.indices.get(index=index).keys())

def settings(index='*'):
	return ES.indices.get_settings(index=index)

def get_document(domain: str, doc_id: str):
	# TODO: rewrite query to include the domain
	query = {'match': {'_id': doc_id}}
	result = ES.search(index=INDEX, size=config.MAX_RESULTS, query=query)
	return SearchResult(result)

def get_documents(doc_ids: list):
	result = ES.mget(
		index=INDEX,
		body={'ids': doc_ids},
		source_excludes=['abstract', 'text'])
	return SearchResult(result)

def search(domain: str, term: str, page: int=1):
	# TODO: 'term' could be multiple tokens and the search is now a disjunction
	# TODO: rewrite query to include the domain
	query = {'multi_match': {'query': term, "fields": ["title", "abstract", "text"]}}
	# offset for documents returned
	skip = config.MAX_RESULTS * (page - 1)
	result = ES.search(index=INDEX, size=config.MAX_RESULTS, query=query, from_=skip)
	return SearchResult(result)


class SearchResult:

	"""Convenience wrapper around the response from ElasticSearch. The response is
	different depending on whether we called ES.mget() or ES.search()."""

	def __init__(self, elastic_response):
		# elastic_response is of type elastic_transport.ObjectApiResponse
		self.response = elastic_response
		self.took = self.response.get('took')
		self.timed_out = self.response.get('timed_out')
		self.shards = self.response.get('_shards')
		self.hits = self._get_hits()
		self.hits_returned = len(self.hits)
		self.total_hits = self._get_total_hits()

	def __str__(self):
		return f'<SearchResult with {self.hits_returned}/{self.total_hits} hits>'

	def __len__(self):
		return self.hits_returned

	def _get_hits(self):
		if 'docs' in self.response:
			hits = self.response['docs']
		else:
			hits = self.response['hits']['hits']
		# NOTE: should perhaps return a DocumentSet
		return [Document(hit) for hit in hits]

	def _get_total_hits(self):
		if 'docs' in self.response:
			return self.hits_returned
		else:
			return self.response['hits']['total']['value']


def test(term: str):
	result = search(None, term)
	for n, doc in enumerate(result.hits):
		print(f'{n+1:2}  {doc.identifier}  {doc.score:7.4f}  {doc.domain[:3]}  {doc.title[:75]}')


if __name__ == '__main__':

	if len(sys.argv) > 1:
		term = sys.argv[1]
		test(term)
