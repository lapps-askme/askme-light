# AskMe Query Expansion

The current implementation has no sense of state, queries are all fixed depending on what part of the AskMe GUI they came from (document, document set, query page).

Queries are just Eleasticsearch queries:

```json
{
	"bool": {
		"must": {
			"multi_match": {
				"query": "minerals", 
				"fields": ('title', 'abstract', 'text'),
				"type": "phrase" if type == "exact" else "best_fields"
			}
		},
		"filter": {
			"terms": {
				"topic": ['biomedical', 'geoarchive']
			}
		}
	}
}
```


### Queries as dynamic objects

A query is now a list of specifications. Typically this will start out with a query like the above:

```python
[
	('query', initial_query),
]
```

When we want to run this query we simply take the initial query and send it off.

But then other specifications can be added, depending on user choices. One would be to exclude or include doduments:

```python
[
	('query', initial_query),
	('include', [id1, id2, id3]),
	('exclude', [id4, id5, id9])
]
```

Now we cannot just run the query anymore, instead we build a more complex query from the three specifications above and send it off to ES. However, there is no need that everything in the specifications needs to be entered in the query. ES is embedded in some Python code and that code could for example deal with the exclusions.

Next thing to add is to expand the query with related terms or synonyms. The related terms we have available for each document or document set and we will allow the user to add them. The synonyms we plan to pull from ChatGPT, the latter by  using term lists for each domain and sending off targeted queries like *What are synonyms for X in domain Y?*.

```python
[
	('query', initial_query),
	('include', [id1, id2, id3]),
	('exclude', [id4, id5, id9]),
	('add_synonym', [term1, [term2, term3, term4]),
	('add_terms', [term5, term6, term7, term8]),
	('add_term', [term9, [term10, term11, term12]])
]
```

We should also allow negations:

```python
[
	...,
	('add_terms', [term5, term6, term7, term8]),
	('add_term', [term9, [term10, term11, term12]])
	('exclude_terms', [term13, term14],
	('exclude_term', [term15, [term16]])
]
```

This query object will live in the AskMe client and will be constantly updated, but it will also be stored in the a separate index in the database.

