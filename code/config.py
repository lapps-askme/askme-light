
ELASTIC_HOST = 'localhost'
ELASTIC_PORT = 9200

# Number of tokens we allow in the summary, set to a number that keeps processing
# of a query below 0.5 seconds.
SUMMARY_SIZE = 500

# Maximum number of documents to run NLP over (for ranking). In the past 20 seemed 
# to be a good cut off, with benefits in evaluation most pronounced over the first
# 20 documents.
MAX_DOCUMENTS_FOR_NLP = 20
