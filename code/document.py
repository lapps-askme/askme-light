from operator import itemgetter

from config import SUMMARY_SIZE, FIELDS_FOR_MULTIPLE_DOCS, FIELDS_FOR_SINGLE_DOC


class Document():

	"""Object created from a hit in the ElasticSearch response."""

	def __init__(self, hit: dict):
		self.identifier = hit['_id']
		self.score = hit.get('_score', 0)
		self.nscore = hit.get('_score', 0)
		# TODO: database should not have topic but domain field
		self.domain = hit['_source'].get('topic')
		self.year = hit['_source'].get('year')
		self.title = hit['_source'].get('title', '')
		self.url = hit['_source'].get('url', '')
		self.authors = hit['_source'].get('authors', [])
		# take the summary of the abstract and text, to cut down the size of the
		# object returned
		full_summary = hit['_source'].get('summary', '')
		# TODO: this now assumes whitespace is always a space (no newlines or tabs),
		# which may change at any time
		self.summary = ' '.join(full_summary.split()[:SUMMARY_SIZE])
		self.entities = hit['_source'].get('entities', {})
		self.terms = hit['_source'].get('terms', [])
		self.restore_types()

	def __str__(self):
		return (f'<Document id={self.identifier} score={self.score:.4f}' \
				+ f' year={self.year} title={self.title[:40]}')

	def restore_types(self):
		"""For terms the frequency and tfidf were stored as strings, here we
		restore them back to integers and floats."""
		for term_triple in self.terms:
			term_triple[1] = int(term_triple[1])
			term_triple[2] = float(term_triple[2])

	def pp(self):
		print(f'Document {self.identifier} score=={self.score:.4f} year={self.year}')
		print(f'   title={self.title}')
		print(f'   authors={self.authors}')
		print()

	def sorted_terms(self):
		return sorted(self.terms, key=itemgetter(2), reverse=True)

	def terms_as_string(self):
		return ' '.join([term[0] for term in self.terms])

	def as_json(self, single_doc=True):
		"""Fields that are included are different depending whether we are returning
		the JSON of a single document or wether this document is part of a list."""
		fields = FIELDS_FOR_SINGLE_DOC if single_doc else FIELDS_FOR_MULTIPLE_DOCS
		return { field: getattr(self, field) for field in fields }

	def display_fields(self):
		"""Return a list of basic fields to be displayed in the Flask application.
		Each field is a pair of a field name and field value."""
		return [
			('document', self.identifier),
			('title', self.title),
			('year', self.year),
			('url', f'<a href="{self.url}">{self.url}</a>'),
			('authors', self.authors),
			('domain', self.domain),
			('summary', self.summary) ]



class DocumentSet:

	"""A list of documents."""

	# TODO: should probably emulate a list

	def __init__(self, documents):
		self.documents = documents

	def __len__(self):
		return len(self.documents)

	def __str__(self):
		return f'<DocumentSet with {len(self)} documents>'

	def get_terms(self):
		"""To get the terms of a set, with their frequencies and TFIDF scores, we
		just collect all of them and sum the frequencies and TFIDF scores. This
		definitely makes sense for the frequencies, but for the TFIDF scores we do
		end up with something that is not really a TFIDF score. The resulting list
		of (TFIDF, frequency, term) tuple is sorted on TFIDF scores."""
		terms = {}
		for doc in self.documents:
			for term in doc.terms:
				if not term[0] in terms:
					terms[term[0]] = [0,0]
					terms[term[0]][0] += term[1]
					terms[term[0]][1] += term[2]
		return list(reversed(sorted(
				[(tfidf, freq, term) for term, (freq, tfidf) in terms.items()])))
