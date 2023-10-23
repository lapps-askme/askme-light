from operator import itemgetter

from config import SUMMARY_SIZE, FIELDS


class Document():

	def __init__(self, hit: dict):
		self.identifier = hit['_id']
		self.score = hit.get('_score', 0)
		self.nscore = hit.get('_score', 0)
		self.topic = hit['_source'].get('topic')
		self.year = hit['_source'].get('year')
		self.title = hit['_source'].get('title', '')
		self.url = hit['_source'].get('url', '')
		self.authors = hit['_source'].get('authors', [])
		# take the summary of the abstract and text, to cut down the size of the
		# object returned
		full_summary = hit['_source'].get('summary', '')
		# TODO: this now assumes whitespace is always a space (no newlines) which
		# may change
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

	def as_json(self):
		return { field: getattr(self, field) for field in FIELDS }

	def display_fields(self):
		"""Return a list of fields to be displayed in the Flask application. Each field
		is a tuple of a field name and field value."""
		return [
			('document', self.identifier),
			('title', self.title),
			('year', self.year),
			('url', f'<a href="{self.url}">{self.url}</a>'),
			('authors', self.authors),
			('domain', self.topic),
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
		terms = []
		for doc in self.documents:
			for term in doc.terms:
				terms.append(term)
		return terms
