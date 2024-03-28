import sys, warnings, argparse, pprint

from elasticsearch import Elasticsearch, ElasticsearchWarning
from elastic_transport import ObjectApiResponse

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

def get_raw_document(doc_id: str):
    query = {'match': {'_id': doc_id}}
    return ES.search(index=INDEX, size=config.MAX_RESULTS, query=query)

def get_documents(doc_ids: list):
    result = ES.mget(
        index=INDEX,
        body={'ids': doc_ids},
        source_excludes=['abstract', 'text'])
    return SearchResult(result)

def search(tags: list, term: str, type: str=None, page: int=1):
    # TODO: 'term' could be multiple tokens and the search is now a disjunction
    # Using "must" instead of "should". With the latter, documents with scores
    # of zero were making it into the response.
    query = {
        "bool": {
            "must": {
                "multi_match": {
                    "query": term,
                    "fields": config.SEARCH_FIELDS,
                    "type": "phrase" if type == "exact" else "best_fields"}},
            "filter": {
                "terms": {"tags": tags} } if tags else None}}
    # offset for documents returned
    skip = config.MAX_RESULTS * (page - 1)
    result = ES.search(index=INDEX, size=config.MAX_RESULTS, query=query, from_=skip)
    return SearchResult(result)


class SearchResult:

    """Convenience wrapper around the response from ElasticSearch."""

    def __init__(self, elastic_response: ObjectApiResponse):
        """The response is different depending on whether we called ES.mget() or
        ES.search(). While in both cases the response is an ObjectApiResponse, in
        the former case it just has a 'docs' property while in the latter there are
        'took', 'timed_out', '_shards' and 'hits' properties."""
        self.response = elastic_response
        self.error = False
        if 'docs' in self.response:
            docs = self.response['docs']
            if docs and (len(docs) == 1) and 'error' in docs[0]:
                self.error = True
                self.error_details = ElasticErrorDetails(elastic_response)
                self.docs = []
                self.total_hits = 0
            else:
                self.docs = self.docs_from_hits(docs)
                self.total_hits = len(self)
        else:
            self.docs = self.docs_from_hits(self.response['hits']['hits'])
            self.total_hits = self.response['hits']['total']['value']

    def __str__(self):
        return f'<SearchResult hits={self.total_hits} succes={not self.error}>'

    def __len__(self):
        return len(self.docs)

    def __getitem__(self, i):
        return self.docs[i]

    def first_doc(self):
        try:
            return self.docs[0]
        except IndexError:
            return None

    @staticmethod
    def docs_from_hits(hits: list):
        return [Document(hit) for hit in hits]


class ElasticErrorDetails:

    """Class to deal with the errors you get when using ES.mget(), where no
    exception will be raised but the error is hidden in the first element of
    the docs list that is returned in the JSON response."""

    def __init__(self, elastic_response: ObjectApiResponse):
        self.response = elastic_response
        self.details = elastic_response.get('docs', [None])[0]

    def reason(self):
        return self.details.get('error', {}).get('reason')

    def pp(self):
        print(self)
        simplified = dict(self.details)
        del simplified['root_cause']
        pprint.pprint(simplified, indent=2)


def test(tags: str, term: str):
    result = search(tags, term)
    for n, doc in enumerate(result.hits):
        print(f'{n+1:2}  {doc.identifier}  {doc.score:7.4f}  {doc.tags[:3]}  {doc.title[:75]}')



if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("--tags", default=None, help="tags, None by default" )
    parser.add_argument("--query", help="query")
    args = parser.parse_args()

    if args.query:
        test(args.tags, args.query)
