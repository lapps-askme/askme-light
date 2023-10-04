
class Document():

	def __init__(self, hit: dict):
		self.identifier = hit['_id']
		self.score = hit['_score']
		self.topic = hit['_source'].get('topic')
		self.year = hit['_source'].get('year')
		self.title = hit['_source'].get('title', '')
		self.authors = hit['_source'].get('authors', [])
		self.abstract = hit['_source'].get('abstract', '')[:250]
		self.text = hit['_source'].get('text', '')[:250]

	def __str__(self):
		return f'<Document id={self.identifier} score={self.score:.4f} year={self.year} title={self.title[:40]}'

	def __len__(self):
		return len(self.abstract) + len(self.text)

	def pp(self):
		print(f'Document {self.identifier} score=={self.score:.4f} year={self.year}')
		print(f'   title={self.title}')
		print(f'   authors={self.authors}')
		print()

	def as_json(self):
		pass
		