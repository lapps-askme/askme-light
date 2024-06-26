"""Prototype AskMe query expansion

Defines a QueryBuilder class which is initiated with query term, but which
can then be expanded using a variety of query specifications.

Requirements:

$ pip install elasticsearch

"""

import re
import json
import pprint
import textwrap
import elasticsearch
from utils import dict_generator, highlight


# Making this standalone for now so copied settings from the configuration file

ELASTIC_HOST = 'localhost'
ELASTIC_PORT = 9200
ELASTIC_INDEX = 'xdd'
ELASTIC_USER = 'askme'
ELASTIC_PASSWORD = 'pw-askme'


MAX_HITS = 20


ES = elasticsearch.Elasticsearch(
        [f'http://{ELASTIC_HOST}:{ELASTIC_PORT}'],
        basic_auth=(ELASTIC_USER, ELASTIC_PASSWORD))



class Result:

    def __init__(self, query: dict):
        self.query = query
        self.result = ES.search(index=ELASTIC_INDEX, size=MAX_HITS, query=query)
        self.hits = [Hit(hit) for hit in self.result['hits']['hits']]

    def __str__(self):
        return f'<Result query_terms={len(self.qterms())} hits={len(self)}>'

    def __len__(self):
        return len(self.hits)

    def __getitem__(self, i):
        return self.hits[i]

    def qterms(self):
        qterms = []
        for l in dict_generator(self.query):
            if l[-2] == 'query':
                qterms.append(l[-1])
        return qterms

    def pp_terms(self):
        terms = ' '.join([f'"{qt}"' for qt in self.qterms()])
        print(f'\n<QueryTerms {terms}>')

    def pp_query(self):
        print(json.dumps(self.query, indent=2))

    def pp_titles(self):
        print('\nHits with scores and titles\n')
        for n, hit in enumerate(self):
            title = highlight(hit.title[:120], self.qterms())
            print(f"{n+1:2}  {hit.score:>5.2f}  {title}")
        print()

    def pp_abstracts(self):
        for n, hit in enumerate(self):
            title = highlight(hit.title[:120], self.qterms())
            print(f"{n+1:2}  {hit.score:>5.2f}  {title}")
            hit.pp_abstract(indent='    ', skip='\n', words=self.qterms())
            if n + 1 < len(self):
                answer = input('? Hit enter for next abstract: ')
                if answer == 'q':
                    break
                print()

    def pp_all(self):
        for n, hit in enumerate(self):
            title = highlight(hit.title[:120], self.qterms())
            print(f"\n{n+1:2}  {hit.score:>5.2f}  {title}")
            hit.pp_abstract(indent='    ', skip='\n', words=self.qterms())
            hit.pp_text(indent='    ', skip='\n', words=self.qterms())
            if n + 1 < len(self):
                answer = input('? Hit enter for next abstract: ')
                if answer == 'q':
                    break
                print()


class Hit:

    def __init__(self, hit: dict):
        self.hit = hit
        self.score = self.hit['_score']
        self.title = self.hit['_source']['title']
        self.abstract = self.hit['_source']['abstract']
        self.text = self.hit['_source']['text']

    def pp_abstract(self, skip='', indent='', words=None):
        self.pp_field(self.abstract, skip=skip, indent=indent, words=words)

    def pp_text(self, skip='', indent='', words=None):
        self.pp_field(self.text, skip=skip, indent=indent, words=words)

    def pp_field(self, field, skip='', indent='', words=None):
        text = textwrap.fill(
            field, 120, initial_indent=indent, subsequent_indent=indent)
        if words is not None:
            text = highlight(text, words)
        print(f'{skip}{text}{skip}')



class QuerySpecification:

    """Implements a kind of specification for building a query. There are several
    types of specifications and for each type the specification itself provides 
    distinguishing information:

    query_term          an instance of QTerm
    document_exclusion  list of excluded documents
    document_inclusion  list of included documents
    term_inclusion      list of terms included
    term_exclusion      list of terms excluded
    synonyms            pair of a term and a list of synonyms

    The first specification in a Query is always of type es_query. The comment comes
    from the user and reflects user intention for the specification."""

    def __init__(self, query_type: str, specification, comment=None):
        self.type = query_type
        self.spec = specification
        self.comment = comment

    def __str__(self):
        spec_string = str(self.spec)
        if len(spec_string) > 60:
            spec_string = f'{spec_string[:26]} ... {spec_string[-26:]}'
        return f'<QuerySpecification {self.type}  --  {spec_string}>'

    def pp(self):
        print(self)
        print(textwrap.indent(pprint.pformat(self.spec), '    '))


class QueryBuilder:

    def __init__(self, term):
        self.specifications = [QuerySpecification('query_term', QTerm(term))]
        self.query = Query(And(QTerm(term)))
        self.document_exclusions = []
        self.document_inclusions = []

    def __len__(self):
        return len(self.specifications)

    def __str__(self):
        return f'<{self.__class__.__name__} with {len(self)} specifications>'

    def add(self, specification: QuerySpecification):
        self.specifications.append(specification)

    def exclude_documents(self, *docs):
        self.add(QuerySpecification('document_exclusion', docs))
        self.document_exclusions.extend(docs)

    def include_documents(self, *docs):
        self.add(QuerySpecification('document_inclusion', docs))
        self.document_inclusions.extend(docs)

    def include_terms(self, *terms):
        for term in terms:
            qterm = QTerm(term)
            self.add(QuerySpecification('term_inclusion', qterm))
        self.query.include_term_as_conjunction(qterm)

    def exclude_terms(self, *terms):
        for term in terms:
            qterm = QTerm(term)
            self.add(QuerySpecification('term_exclusion', QTerm(term)))
        self.query.include_term_as_conjunction(Not(qterm))

    def add_synonyms(self, term: str, synonyms: list):
        self.add(QuerySpecification('synonym', (term, synonyms)))
        self.query.add_synonyms(term, synonyms)

    def pp(self):
        print()
        print(self)
        for q in self.specifications:
            print('   ', q)
        print()
        print(f'formula: {self.query.formula()}')
        print(f'include: {self.document_inclusions}')
        print(f'exclude: {self.document_exclusions}')
        print()


class Boolean:

    def __init__(self):
        self.must = []
        self.should = []
        self.must_not = []

    def json(self):
        obj = { "bool": {}}
        if self.must:
            obj["bool"]["must"] = [x.json() for x in self.must]
        if self.must_not:
            obj["bool"]["must_not"] = [x.json() for x in self.must_not]
        if self.should:
            obj["bool"]["should"] = [x.json() for x in self.should]
        return obj

    def formula(self):
        raise NotImplementedError


class And(Boolean):

    def __init__(self, *qterms):
        super().__init__()
        self.must = list(qterms)

    def __str__(self):
        return f'<Boolean must={self.must}'

    def include(self, qterm):
        self.must.append(qterm)

    def formula(self):
        return '(' + ' AND '.join([qterm.formula() for qterm in self.must]) + ')'


class Or(Boolean):

    def __init__(self, *qterms):
        super().__init__()
        self.should = list(qterms)

    def __str__(self):
        return f'<Boolean should={self.should}'

    def formula(self):
        return '(' + ' OR '.join([qterm.formula() for qterm in self.should]) + ')'


class Not(Boolean):

    def __init__(self, *qterms):
        super().__init__()
        self.must_not = qterms

    def __str__(self):
        return f'<Boolean should={self.should}'

    def formula(self):
        elements = ' '.join([qt.formula() for qt in self.must_not])
        return f'(NOT {elements})'


class QTerm():

    def __init__(self, query: str, match_type='exact'):
        self.query = query
        self.match_type = "phrase" if match_type == "exact" else "best_fields"

    def __str__(self):
        return f'<QTerm {self.query}>'

    def formula(self):
        return self.query

    def json(self):
        return {
            "multi_match": {
                "query": self.query, 
                "fields": ['title', 'abstract', 'text'],
                "type": self.match_type }}


class Query:

    def __init__(self, initial_boolean: Boolean):
        self.data = initial_boolean

    def formula(self):
        return self.data.formula()

    def json(self):
        return self.data.json()

    def include_term_as_conjunction(self, qterm: QTerm):
        self.data.include(qterm)

    def exclude_term(self, qterm: QTerm):
        # TODO: this is being ignored, so using another approach
        self.data.must_not.append(qterm)
        print(999, qterm, self.data.must_not)

    def add_synonyms(self, term: str, synonyms: list):
        for n, element in enumerate(self.data.must):
            if isinstance(element, QTerm) and element.query == term:
                qterms = [element]
                for synonym in synonyms:
                    qterms.append(QTerm(synonym))
                self.data.must[n] = Or(*qterms)

    def pp(self):
        print(self.formula())


def save_query(q: dict, outfile: str):
    with open(outfile, 'w') as fh:
        fh.write(json.dumps(q.json(), indent=2))


def example1():
    qb = QueryBuilder("earthquake")
    qb.exclude_documents('d1', 'd2', 'd4')
    qb.include_documents('d3', 'd6')
    qb.include_terms('techtonic activity')
    qb.exclude_terms('shock')
    #qb.include_terms('head cold')
    #qb.add_synonyms('head cold', ('Rhinitis', 'upper respiratory infection'))
    qb.pp()
    save_query(qb.query, 'example.json')
    result = Result(qb.query.json())
    print(result)


def example2():
    q = Or(
            QTerm('earthquake'),
            QTerm('techtonic activity'),
            And(
                QTerm('shock'),
                Not(QTerm('emotional'))))
    print(f'\n{q.formula()}')
    result = Result(q.json())
    print(f'\n{result}')
    #result.pp_terms()
    result.pp_titles()
    #result.pp_abstracts()
    #result.pp_all()


if __name__ == '__main__':

    example1()
    #example2()
