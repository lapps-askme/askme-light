# Query Expansion

Some code to play with amending and expanding a query.

## Requirements and set up

Should definitely run on Python version 3.11 and up, probably on any version larger than 3.8.

Modules needed (earlier and later versions probably work as well):

```bash
$ pip install elasticsearch==8.14.0
```

Assumes that an ElasticSearch database is running with the following settings:

```python
ELASTIC_HOST = 'localhost'
ELASTIC_PORT = 9200
ELASTIC_INDEX = 'xdd'
ELASTIC_USER = 'askme'
ELASTIC_PASSWORD = 'pw-askme'
```

These are defined at the top of the `builder.py` file, edit these variables if your local set up is different.


## Basic query building

The idea is that you can build a random complex query like this:

```python
q = Or(
        QTerm('earthquake'),
        QTerm('techtonic activity'),
        And(
            QTerm('shock'),
            Not(QTerm('emotional'))))
```

And we can then send off this query to ElasticSearch and print some basic info (search terms and number of hits):
   

```python
>>> q.formula()
(earthquake OR techtonic activity OR (shock AND (NOT emotional)))
>>> result = Result(q.json())
>>> print(result)
<Result query_terms=4 hits=20>
```

You can also the query terms and the list of titles that matched the query.

```python
>>> result.pp_terms()
>>> result.pp_titles()
```

Or the abstracts, in which case you will get a prompt after each abstract:

```python
>>> result.pp_abstracts()
```

Or all information for each hit, also waiting for prompts:

```python
>>> result.pp_all()
```

In all cases search terms will be highlighted in the results.

There is an example in `builder.py` in the example2() function.


## Query Expansion

The core fnctionailty in building queries is in the **And**, **Or**, **Not** and **QTerm** classes. These are used by the query expansion methods that work on a slightly higher level of abstraction.