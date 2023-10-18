import time
import spacy

from config import MAX_DOCUMENTS_FOR_NLP


t0 = time.time()
nlp = spacy.load("en_core_web_sm", disable=["ner", "parser", "tok2vec"])

# TODO: move this to a log
# print(f'>>> spaCy loaded in {time.time() - t0: .4f} seconds')


def rerank(docs: list):
	t0 = time.time()
	for doc in docs[:MAX_DOCUMENTS_FOR_NLP]:
		parsed_doc = nlp(doc.summary)

	# TODO: move this to a log
	# print(f'>>> reranked in {time.time() - t0: .4f} seconds')
	return docs
