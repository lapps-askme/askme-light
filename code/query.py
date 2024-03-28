
import sys, json, argparse

from elasticsearch import Elasticsearch

import config
#from document import Document


ES = Elasticsearch(
        [f'http://{config.ELASTIC_HOST}:{config.ELASTIC_PORT}'],
        basic_auth=(config.ELASTIC_USER, config.ELASTIC_PASSWORD))

INDEX = config.ELASTIC_INDEX


def search(tags: str = None, term: str = None, query: str = None, page: int = 1):
    """New search function for elastic.py."""
    # TODO: 'term' could be multiple tokens and the search is now a disjunction
    if not tags:
        query = {'multi_match': {'query': term, "fields": config.SEARCH_FIELDS}}
    else:
        # Using "must" instead of "should". With the latter, documents with scores
        # of zero were making it into the response.
        query = {
            "bool": {
                "must": {
                    "multi_match": {"query": term, "fields": config.SEARCH_FIELDS}},
                "filter": {"term": {"tags": tags} }}}
    # offset for documents returned
    skip = config.MAX_RESULTS * (page - 1)
    result = ES.search(index=INDEX, size=config.MAX_RESULTS, query=query, from_=skip)
    return SearchResult(result)


class Query:

    """This builds the kind of query that we used before.

    tags    -  a string denoting tags
    terms   -  the query terms
    phrase  -  True if the terms should be considered a phrase
    must    -  True if this is a boolean "must" query
    should  -  True if this is a boolean "should" query
    query   -  the ElasticSearch query, build from the above

    It is an open question on whether we should use match_phrase for terms or just
    a "must", in the latter case we really need some of the ranking algorithms that
    we used before.

    """

    def __init__(self, query: str, tags: str = None,
                 phrase: bool = False, must: bool = False, should: bool = False):
        self.terms = query
        self.tags = tags
        self.must = must
        self.should = should
        self.fields = config.SEARCH_FIELDS
        self.query = {"bool": {"should": [], "must": [], "filter": []}}
        self.build()

    def __str__(self):
        must = ' must' if self.must else ''
        should = ' should' if self.should else ''
        return f'<Query "{self.terms}" tags="{self.tags}"{must}{should}">'

    def is_valid(self):
        return self.query is not None

    def build(self):
        if self.tags:
            tags_filter = {"term": {"tags": self.tags}}
            self.query["bool"]["filter"].append(tags_filter)
        if self.must or self.should:
            leaf_query = {"multi_match": {"query": self.terms, "fields": self.fields}}
            # this keeps open the option that there is both a must and a should
            if self.should:
                self.query["bool"]["should"].append(leaf_query)
            else:
                self.query["bool"]["must"].append(leaf_query)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("--terms", help="the query terms")
    parser.add_argument("--tags", default=None, help="tags, None by default" )
    parser.add_argument("--must", action='store_true', help="boolean must query")
    parser.add_argument("--should", action='store_true', help="boolean should query")
    parser.add_argument("--page", default=0, type=int, help="what page of the results to show" )
    args = parser.parse_args()
    print(args)

    start_hit = args.page * 20
    query = Query(args.terms, tags=args.tags, must=args.must, should=args.should)
    print(query)
    print(json.dumps(query.query, indent=2))

    if query.is_valid():
        result = ES.search(index=INDEX, size=config.MAX_RESULTS, query=query.query, from_=start_hit)
        print(f'\nTotal hits: {result["hits"]["total"]["value"]}')
        for hit in result['hits']['hits']:
            score = f'{hit["_score"]:2.4f}'
            tags = hit["_source"]["tags"][:3]
            print(f'{hit["_id"]}  {score:>7s}  {tags}  {hit["_source"]["title"][:100]}')
