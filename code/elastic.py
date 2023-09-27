import sys, warnings
from pprint import pprint

from elasticsearch import Elasticsearch, ElasticsearchWarning

import document


# Suppressing the security warning
# warnings.filterwarnings("ignore", category=ElasticsearchWarning)
warnings.filterwarnings("ignore", message=open('securitywarning.txt').read().strip())

es = Elasticsearch([{'host': 'localhost', 'port': 9200, 'scheme': 'http'}])


def indices(index='*'):
	return list(es.indices.get(index=index).keys())


def settings(index='*'):
	return es.indices.get_settings(index=index)


def query(indexname: str, searchterm: str):
	query = {'match': {'text': searchterm}}
	result = es.search(index=indexname, query=query)
	return result


def test(term: str):
	result = query('xdd-bio', term)
	print(len(result['hits']['hits']), 'results')
	docs = [document.Document(hit) for hit in result['hits']['hits']]
	for doc in docs:
		print(doc)
	#pprint(result['hits']['hits'][0])


if __name__ == '__main__':

	if len(sys.argv) > 1:
		term = sys.argv[1]
		test(term)
