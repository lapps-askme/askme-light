# Basic ElasticSearch information, edit as needed.
ELASTIC_HOST = 'localhost'
ELASTIC_PORT = 9200
ELASTIC_INDEX = 'xdd'

# Edit as needed. The askme user should at least have the viewer role.
ELASTIC_USER = 'askme'
ELASTIC_PASSWORD = 'pw-askme'

# Number of tokens we allow in the summary, set to a number that keeps processing
# of a query below 0.5 seconds.
SUMMARY_SIZE = 500

# Maximum number of documents to run NLP over (for ranking). In the past 20 seemed 
# to be a good cut off, with benefits in evaluation most pronounced over the first
# 20 documents.
MAX_DOCUMENTS_FOR_NLP = 20

# maximum number of results to print
MAX_RESULTS = 20

# maximum number of pages allowed for pagination
# elastic sets a default maxiumum of 10,000 document offset allowed
# set this as limit for now (need to decide on max pages wanted for performance reasons)
MAX_PAGES = 40

# Fields to search when doing a basic text search
SEARCH_FIELDS = ('title', 'abstract', 'text')

# List of fields to be included in the document when the API requests it
# This is used when multiple documents are returned.
FIELDS_FOR_MULTIPLE_DOCS = (
	'identifier', 'score', 'nscore', 'domain', 'year', 'title', 'url',
	'authors', 'summary')

# List of all fields to includes when you request a single document. The scores
# become irrelevant, but terms and entities are added.
FIELDS_FOR_SINGLE_DOC = (
	'identifier', 'domain', 'year', 'title', 'url',
	'authors', 'summary', 'terms', 'entities')
