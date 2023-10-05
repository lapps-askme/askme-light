import time
import spacy

t0 = time.time()
nlp = spacy.load("en_core_web_sm", disable=["ner", "parser", "tok2vec"])
print(f'>>> spaCy loaded in {time.time() - t0: .4f} seconds')


def rerank(hits):
	t0 = time.time()
	for hit in hits:
		doc = nlp(hit['_source']['text'])

	print(f'>>> reranked in {time.time() - t0: .4f} seconds')
	return hits
