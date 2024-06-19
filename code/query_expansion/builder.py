"""Prototype AskMe query expansion

Defines a QueryBuilder class which is initiated with query term, but which
can then be expanded using a variety of query specifications. This is to be
integrated into the code in the parent directory.

Requirements (later versions most likely also work):

$ pip install elasticsearch==8.14.0

Usage:

$ python builder.py

Run whatever is uncommented in the else clause of the main block.

$ python builder.py TERMS+

Create a QueryBuilder with a big concatenation of all the terms, add a snapshot
with query results after each step, and print all snapshots.

Examples:

$ python builder.py earthquake
$ python builder.py earthquake 'central part'

"""

import re
import json
import sys
import pprint
import textwrap
from abc import ABC, abstractmethod

import elasticsearch

from utils import dict_generator, highlight, timestamp


# Making this standalone for now so copying settings from the configuration file

ELASTIC_HOST = 'localhost'
ELASTIC_PORT = 9200
ELASTIC_INDEX = 'xdd'
ELASTIC_USER = 'askme'
ELASTIC_PASSWORD = 'pw-askme'


MAX_HITS = 100


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

    def identifiers(self) -> list:
        return list(sorted(self.hits.keys()))

    def qterms(self) -> list:
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
        self.identifier = hit['_id']
        self.score = self.hit['_score']
        self.title = self.hit['_source']['title']
        self.abstract = self.hit['_source']['abstract']
        if 'content' in self.hit['_source']:
            self.text = self.hit['_source']['content']
        if 'text' in self.hit['_source']:
            self.text = self.hit['_source']['text']
        else:
            self.text = ''

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


class QueryBuilder:

    """Top-level class that maintains all information needed when building a query.

    Instance variables:

        specifications        -  list of instances of QuerySpecification
        query                 -  instance of Query
        document_exclusions   -  list of document identifiers
        document_inclusions   -  list of document identifiers
        history               -  instance of History

    When building a query, you add to the specifications and each time you add to
    them you also update the query, the list of document exclusions or the document
    inclusions, finally you also update the history, which is a list of snapshots
    of specifications optionally associated with databse results.

    This class isself not responsible for any database interactions, but the Query
    inside of it should be able to create the ElasticSearch json that is needed
    for database access (using the query.json() method)."""

    def __init__(self, term):
        """Always initialize with a term. At the moment this is a single term, but
        this should soon be changed into a list of terms."""
        self.specifications = [QuerySpecification('query_term', QTerm(term))]
        self.query = Query(And(QTerm(term)))
        self.document_exclusions = []
        self.document_inclusions = []
        self.history = History(self)

    def __len__(self):
        return len(self.specifications)

    def __str__(self):
        return f'<{self.__class__.__name__} with {len(self)} specifications>'

    def add(self, specification: 'QuerySpecification'):
        self.specifications.append(specification)

    def exclude_documents(self, *docs):
        self.add(QuerySpecification('document_exclusion', docs))
        self.document_exclusions.extend(docs)
        self.update_history()

    def include_documents(self, *docs):
        self.add(QuerySpecification('document_inclusion', docs))
        self.document_inclusions.extend(docs)
        self.update_history()

    def include_terms(self, *terms):
        for term in terms:
            qterm = QTerm(term)
            self.add(QuerySpecification('term_inclusion', qterm))
            self.query.add_term_as_conjunction(qterm)
        self.update_history()

    def exclude_terms(self, *terms):
        for term in terms:
            qterm = QTerm(term)
            self.add(QuerySpecification('term_exclusion', qterm))
            self.query.add_term_as_conjunction(Not(qterm))
        self.update_history()

    def add_synonyms(self, term: str, synonyms: list):
        self.add(QuerySpecification('synonym', (term, synonyms)))
        self.query.add_synonyms(term, synonyms)
        self.update_history()

    def update_history(self):
        self.history.append(Snapshot(self))

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


class QuerySpecification:

    """Implements a kind of specification for building a query. There are several
    types of specifications and for each type the specification itself provides 
    distinguishing information:

    self.type           self.spec
    ---------------------------------------------------------
    query_term          an instance of QTerm
    document_exclusion  list of excluded documents
    document_inclusion  list of included documents
    term_inclusion      list of terms included
    term_exclusion      list of terms excluded
    synonyms            pair of a term and a list of synonyms

    The first specification in a Query is always of type query_term. The comment
    comes from the user and reflects user intention for the specification."""

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


class Boolean(ABC):

    """Abstract class to hold common funtionality for booleans (And, Or and Not)."""

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

    @abstractmethod
    def add_term(self):
        pass

    @abstractmethod
    def formula(self):
        pass


class And(Boolean):

    def __init__(self, *qterms):
        super().__init__()
        self.must = list(qterms)

    def __str__(self):
        return f'<Boolean must={self.must}'

    def add_term(self, qterm):
        self.must.append(qterm)

    def formula(self):
        return '(' + ' AND '.join([qterm.formula() for qterm in self.must]) + ')'


class Or(Boolean):

    def __init__(self, *qterms):
        super().__init__()
        self.should = list(qterms)

    def __str__(self):
        return f'<Boolean should={self.should}'

    def add_term(self, qterm):
        self.must.should(qterm)

    def formula(self):
        return '(' + ' OR '.join([qterm.formula() for qterm in self.should]) + ')'


class Not(Boolean):

    def __init__(self, *qterms):
        super().__init__()
        self.must_not = qterms

    def __str__(self):
        return f'<Boolean must_not={self.must_not}'

    def add_term(self, qterm):
        self.must_not.append(qterm)

    def formula(self):
        elements = ' '.join([qt.formula() for qt in self.must_not])
        return f'(NOT {elements})'


class QTerm:

    def __init__(self, query: str, match_type='exact'):
        self.query = query
        self.match_type = "phrase" if match_type == "exact" else "best_fields"

    def __str__(self):
        return f'<QTerm {self.query}>'

    def formula(self):
        return f'"{self.query}"'

    def json(self):
        return {
            "multi_match": {
                "query": self.query, 
                "fields": ['title', 'abstract', 'text'],
                "type": self.match_type }}


class Query:

    """Class that wraps the actual query, which is a complex boolean."""

    def __init__(self, initial_boolean: Boolean):
        self.data = initial_boolean

    def formula(self):
        return self.data.formula()

    def json(self):
        return self.data.json()

    def add_term_as_conjunction(self, qterm: QTerm):
        # Since this is about adding a term as a conjunction we only want to go
        # ahead and do this if the query is an And query.
        if type(self.data) is And:
            self.data.add_term(qterm)

    def add_synonyms(self, term: str, synonyms: list):
        for n, element in enumerate(self.data.must):
            if isinstance(element, QTerm) and element.query == term:
                qterms = [element] + [QTerm(synonym) for synonym in synonyms]
                self.data.must[n] = Or(*qterms)

    def pp(self):
        print(self.formula())


class History:

    """Keeping a history of past specifications so we can trace how changes
    to the specifications impact database query results."""

    def __init__(self, builder: QueryBuilder):
        self.snapshots = [Snapshot(builder)]

    def __len__(self):
        return len(self.snapshots)

    def __getitem__(self, i):
        return self.snapshots[i]

    def append(self, item):
        self.snapshots.append(item)

    def add_result(self, result: Result):
        self.snapshots[-1].add_result(result)


class Snapshot:

    """Each time a change is made to the specifications in the QueryBuilder we take
    a snapshot of the specifications, document inclusions, document exclusions and
    the query. Snapshots can optionally be associated with query results."""

    def __init__(self, builder: QueryBuilder):
        self.timestamp = timestamp()
        self.specifications = builder.specifications.copy()
        self.document_exclusions = builder.document_exclusions.copy()
        self.document_inclusions = builder.document_inclusions.copy()
        self.query = builder.query.formula()
        self.query_result = None

    def __str__(self):
        return f'<Snapshot {self.timestamp.isoformat()} specs={len(self)}>'

    def __len__(self):
        return len(self.specifications)

    def add_result(self, result: Result):
        self.query_result = {hit.identifier: (hit.score, hit.title) for hit in result.hits}

    def pp(self):
        print()
        print(self)
        print()
        for spec in self.specifications:
            print('   ', spec)
        print('   ', self.query, '\n')
        if self.query_result is not None:
            print(f'    number of results is {len(self.query_result)}\n')
            for identifier in list(sorted(self.query_result.keys()))[:10]:
                score, title = self.query_result[identifier]
                print(f'    {identifier}  {score:5.2f}  {title[:100]}')


def save_query(q: dict, outfile: str):
    with open(outfile, 'w') as fh:
        fh.write(json.dumps(q.json(), indent=2))


def example1():
    qb = QueryBuilder('earthquake')
    qb.exclude_documents('d1', 'd2', 'd4')
    qb.include_documents('d3', 'd6')
    qb.include_terms('techtonic activity')
    qb.history.add_result(Result(qb.query.json()))
    qb.exclude_terms('shock')
    qb.include_terms('head cold')
    qb.add_synonyms('head cold', ('Rhinitis', 'upper respiratory infection'))
    qb.include_documents('d9')
    qb.pp()
    #save_query(qb.query, 'example.json')
    result = Result(qb.query.json())
    print(result)
    for snapshot in qb.history:
        snapshot.pp()


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


def example3():

    qb = QueryBuilder('and')
    qb.history.add_result(Result(qb.query.json()))

    qb.include_terms('earthquake')
    qb.history.add_result(Result(qb.query.json()))

    qb.include_terms('shock')
    qb.history.add_result(Result(qb.query.json()))

    for snapshot in qb.history:
        snapshot.pp()
    print()


def build_with_terms(terms):
    qb = QueryBuilder(terms.pop(0))
    qb.history.add_result(Result(qb.query.json()))
    for term in terms:
        qb.include_terms(term)
        qb.history.add_result(Result(qb.query.json()))
    for snapshot in qb.history:
        snapshot.pp()


if __name__ == '__main__':

    if len(sys.argv) > 1:
        build_with_terms(sys.argv[1:])
    else:
        example1()
        #example2()
        #example3()
