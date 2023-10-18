import time
from flask import Flask, render_template, request

import elastic
import ranking

app = Flask(__name__)

@app.route("/")
def index():
    t0 = time.time()
    index = request.args.get("index")
    term = request.args.get("term", '')
    result = None
    docs = []
    if index and term:
        result = elastic.search(index, term)
        docs = result.hits
        docs = ranking.rerank(docs)
    print(f'Elapsed time: {time.time()-t0:.2f} seconds')
    return render_template(
        'index.html', indices=elastic.indices(),
        index=index,term=term, result=result, docs=docs)

@app.route("/document")
def get_document():
    # TODO: this gives an error if the document does not exist
    index = request.args.get("index")
    doc_id = request.args.get("doc_id")
    result = elastic.get_document(index, doc_id)
    doc = result.hits[0] if result.total_hits else None
    return render_template('document.html', index=index, doc_id=doc_id, doc=doc)

@app.route("/related", methods=['POST'])
def get_related():
    index = request.form.get("index")
    title = request.form.get("title")
    abstract = request.form.get("abstract")
    text = request.form.get("text")
    result = elastic.search(index, title)
    return render_template(
        'related.html', index=index,
        title=title, abstract=abstract, text=text, result=result)


if __name__ == '__main__':
    app.run(debug=True)

