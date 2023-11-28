import sys, warnings, argparse

from elasticsearch import Elasticsearch, ElasticsearchWarning

import config
from document import Document


# Suppressing the security warning, this is here in case you run this with an
# ElasticSearch image that does not have security enabled. Will be made obsolete
# rather soon.
# warnings.filterwarnings("ignore", category=ElasticsearchWarning)
# warnings.filterwarnings("ignore", message=open('securitywarning.txt').read().strip())


# ES = Elasticsearch([{
#        'host': config.ELASTIC_HOST,
#        'port': config.ELASTIC_PORT,
#        'scheme': 'http'}])

ES = Elasticsearch(
        [f'http://{config.ELASTIC_HOST}:{config.ELASTIC_PORT}'],
        http_auth=(config.ELASTIC_USER, config.ELASTIC_PASSWORD))


INDEX = config.ELASTIC_INDEX


def indices(index='*'):
    return list(ES.indices.get(index=index).keys())

def settings(index='*'):
    return ES.indices.get_settings(index=index)

def get_document(doc_id: str):
    query = {'match': {'_id': doc_id}}
    result = ES.search(index=INDEX, size=config.MAX_RESULTS, query=query)
    return SearchResult(result)

def get_documents(doc_ids: list):
    result = ES.mget(
        index=INDEX,
        body={'ids': doc_ids},
        source_excludes=['abstract', 'text'])
    return SearchResult(result)

def search(domains: list, term: str, page: int=1):
    # TODO: 'term' could be multiple tokens and the search is now a disjunction
    if not domains:
        query = {'multi_match': {'query': term, "fields": config.SEARCH_FIELDS}}
    else:
        # Using "must" instead of "should". With the latter, documents with scores
        # of zero were making it into the response.
        query = {
            "bool": {
                "must": {
                    "multi_match": {"query": term, "fields": config.SEARCH_FIELDS}},
                "filter": {"terms": {"topic": domains} }}}
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


def test(domain: str, term: str):
    result = search(domain, term)
    for n, doc in enumerate(result.hits):
        print(f'{n+1:2}  {doc.identifier}  {doc.score:7.4f}  {doc.domain[:3]}  {doc.title[:75]}')



if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", default=None, help="domain, None by default" )
    parser.add_argument("--query", help="query")
    args = parser.parse_args()

    if args.query:
        test(args.domain, args.query)
