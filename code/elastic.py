import sys, warnings

from elasticsearch import Elasticsearch, ElasticsearchWarning

import config
import document


# Suppressing the security warning
# warnings.filterwarnings("ignore", category=ElasticsearchWarning)
warnings.filterwarnings("ignore", message=open('securitywarning.txt').read().strip())


ES = Elasticsearch([{
		'host': config.ELASTIC_HOST, 
		'port': config.ELASTIC_PORT, 
		'scheme': 'http'}])


def indices(index='*'):
	return list(ES.indices.get(index=index).keys())

def settings(index='*'):
	return ES.indices.get_settings(index=index)

def get_document(index: str, doc_id: str):
	query = {'match': {'_id': doc_id}}
	result = ES.search(index=index, size=30, query=query)
	return SearchResult(result)

def search(index: str, term: str):
	query = {'multi_match': {'query': term, "fields": ["title", "abstract", "text"]}}
	result = ES.search(index=index, size=30, query=query)
	return SearchResult(result)


class SearchResult:

	"""Convenience wrapper around the response from ElasticSearch."""

	def __init__(self, elastic_response):
		# elastic_response is of type elastic_transport.ObjectApiResponse
		self.response = elastic_response
		self.took = self.response['took']
		self.timed_out = self.response['timed_out']
		self.shards = self.response['_shards']
		self.total_hits = self.response['hits']['total']['value']
		self.hits_returned = len(self.response['hits']['hits'])
		self.hits = self.response['hits']['hits']
		self.compress()

	def __str__(self):
		return f'<SearchResult with {self.hits_returned}/{self.total_hits} results>'

	def number_of_hits(self):
		return result

	def compress(self):
		"""Compress the result by returning just the abstract and text summaries and not
		the full abstract and text. This also updates the raw elastic response as a side
		effect."""
		for hit in self.hits:
			hit['_source']['abstract'] = hit['_source']['abstract_summary']
			hit['_source']['text'] = hit['_source']['text_summary']
			del(hit['_source']['abstract_summary'])
			del(hit['_source']['text_summary'])


def test(term: str):
	result = search('xdd-bio', term)
	print(len(result.hits))
	docs = [document.Document(hit) for hit in result.hits]
	for doc in docs:
		print(doc.identifier, len(doc), doc.title[:75])


if __name__ == '__main__':

	if len(sys.argv) > 1:
		term = sys.argv[1]
		test(term)
