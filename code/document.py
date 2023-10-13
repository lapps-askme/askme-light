from operator import itemgetter


class Document():

	def __init__(self, hit: dict):
		self.identifier = hit['_id']
		self.score = hit['_score']
		self.topic = hit['_source'].get('topic')
		self.year = hit['_source'].get('year')
		self.title = hit['_source'].get('title', '')
		self.authors = hit['_source'].get('authors', [])
		# take the summary of the abstract and text, to cut down the size of the
		# object returned
		self.abstract = hit['_source'].get('abstract_summary', '')
		self.text = hit['_source'].get('text_summary', '')
		self.entities = hit['_source'].get('entities')
		self.terms = hit['_source'].get('terms')
		self.restore_types()

	def __str__(self):
		return (f'<Document id={self.identifier} score={self.score:.4f}' \
				+ f' year={self.year} title={self.title[:40]}')

	def __len__(self):
		return len(self.abstract) + len(self.text)

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
		return {
			'identifier': self.identifier,
			'score': self.score,
			'topic': self.topic,
			'year': self.year,
			'title': self.title,
			'authors': self.authors,
			'abstract': self.abstract,
			'text': self.text,
			'entities': self.entities
		}
		