# Notes on query expansion

### Set up and connectivity

Use the elastic:secure Docker image.

Starting the Docker container (iMac home):

```bash
$ docker run -d --rm -p 9200:9200 \
    -v /Users/Shared/data/elasticsearch/data/:/data \
    --user elasticsearch elastic:secure
```

Indexes (first is for iMac home, second for iMac work):

```bash
$ curl -u elastic:jV4w6BMpnwYu5iNQX25j localhost:9200/_cat/indices
$ curl -u elastic:3XQtE3H2ZlbA29cwTuAV localhost:9200/_cat/indices
```

Query with empty data (to showcase the header):

```bash
$ curl -u askme:pw-askme -H "Content-Type: application/json" -XGET 'localhost:9200/xdd/_search?pretty' -d '{}'
```

This gets the same results:

```bash
$ curl -u askme:pw-askme -H "Content-Type: application/json" -XGET 'localhost:9200/xdd/_search?pretty' -d '
{
  "query" : {
    "match_all" : {}
 }
}'
```


### Building complex queries

Example of complex boolean queries in this case matching a conjunction where one of the conjuncts is a disjunction ([https://stackoverflow.com/questions/48339694/combine-must-and-should](https://stackoverflow.com/questions/48339694/combine-must-and-should)).

```json
{
  "query": {
    "bool": {
      "must": [
        { "match": { "city": "x" } },
        { "match": { "school": "y" } },
        { "match": { "age": 12 } },
        {
          "bool": {
            "should": [
              { "term": { "team": "A" } },
              { "term": { "team": "B" } } ] }
        }
      ]
    }
  }
}
```

Alternatively this is portrayed as follows in
[https://stackoverflow.com/questions/25552321/or-and-and-operators-in-elasticsearch-query](https://stackoverflow.com/questions/25552321/or-and-and-operators-in-elasticsearch-query):

```json
{
  "query": {
    "bool" : {
      "must" : { 
        "term" : { "component" : "comp_1" } },
      "should" : [
        { "term" : { "userId" : "A1A1" } },
        { "term" : { "customerId" : "C1" } },
        { "term" : { "currentRole" : "ADMIN" } }
      ],
      "minimum_should_match" : 1
    }
  }
}
```

```json
{
  "query": {
    "bool": {
      "must": [
        {"bool": {
          "should": [
            {"bool": {
              "must": [
                {"match": {"description": "great"}},
                {"match": {"description": "orange"}}]}},
          {"match": {"description": "popular"}}]}},
        {"bool": {
          "must_not": [
            {"match": {"description": "poor"}}]}},
        {"bool": {
          "should": [
            {"match": {"city": "London"}},
            {"match": {"city": "Paris"}}]}}]}},
  "size": 20,
  "from": 0
}
```


### Trying some booleans

This one is to try the following boolean:

```
(earthquake OR techtonic_activity OR (shock AND ¬emotional))
```

```json
{
    "query": {
        "bool": {
            "should": [
                {"multi_match": {
                    "fields": ["title", "abstract", "text"],
                    "query": "earthquake",
                    "type": "phrase"}},
                {"multi_match": {
                    "fields": ["title", "abstract", "text"],
                    "query": "techtonic activity",
                    "type": "phrase"}},
                {"bool": {
                    "must": [
                        {"multi_match": {
                            "fields": ["title", "abstract", "text"],
                            "query": "shock",
                            "type": "phrase"}},
                        {"bool": {
                            "must_not": [
                                {"multi_match": {
                                    "fields": ["title", "abstract", "text"],
                                    "query": "emotional",
                                    "type": "phrase"}}]}}]}}
            ]
        }
    }
}
```

```json
curl -u askme:pw-askme -H "Content-Type: application/json" -XGET 'localhost:9200/xdd/_search?pretty' -d '
{"bool": {
 "should": [{"multi_match": {"fields": ["title", "abstract", "text"],
                             "query": "earthquake",
                             "type": "phrase"}},
            {"multi_match": {"fields": ["title", "abstract", "text"],
                             "query": "techtonic activity",
                             "type": "phrase"}},
            {"bool": {
             "must": [{"multi_match": {"fields": ["title", "abstract", "text"],
                                       "query": "shock",
                                       "type": "phrase"}},
                      {"bool": {},
                       "must_not": [{"multi_match": {"fields": ["title", "abstract", "text"],
                                                     "query": "emotional",
                                                     "type": "phrase"}}]}]}]}'
```


### Other references

- Using "terms" to do a disjunction<br/>[https://stackoverflow.com/questions/50287616/how-to-use-should-inside-must-in-elasticsearch6?rq=3](https://stackoverflow.com/questions/50287616/how-to-use-should-inside-must-in-elasticsearch6?rq=3)
- Boolean query documentation page<br/>[https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-bool-query.html](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-bool-query.html)
- tutorial-like
  - [https://medium.com/zefo-tech/elastic-search-from-beginner-to-intermediate-e4177c4c769f](https://medium.com/zefo-tech/elastic-search-from-beginner-to-intermediate-e4177c4c769f)
  - [https://coralogix.com/blog/42-elasticsearch-query-examples-hands-on-tutorial/](https://coralogix.com/blog/42-elasticsearch-query-examples-hands-on-tutorial/)