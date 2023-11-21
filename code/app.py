import time
from flask import Flask, render_template, request

import elastic
import ranking
import document
import config


app = Flask(__name__)

debug = False

@app.route("/")
def index():
    t0 = time.time()
    domain = request.args.get("domain", '')
    term = request.args.get("term", '')
    result = None
    docs = []
    if term:
        result = elastic.search(domain, term)
        docs = result.hits
        docs = ranking.rerank(docs)
    print(f'Elapsed time: {time.time()-t0:.2f} seconds')
    return render_template(
        'index.html', index=config.ELASTIC_INDEX, domains=config.DOMAINS,
        domain=domain, term=term, result=result, docs=docs,
        request=request, debug=debug)

@app.route("/document")
def get_document():
    # TODO: this gives an error if the document does not exist
    doc_id = request.args.get("doc_id")
    result = elastic.get_document(doc_id)
    doc = result.hits[0] if result.total_hits else None
    return render_template('document.html', doc_id=doc_id, doc=doc)

@app.route("/set")
def get_set():
    doc_ids = [identifier for identifier in request.args if not identifier == 'index']
    result = elastic.get_documents(doc_ids)
    doc_set = document.DocumentSet(result.hits)
    return render_template('set.html', docs=doc_set.documents, terms=doc_set.get_terms())
    
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

