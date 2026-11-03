import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import logging
from flask import Flask, jsonify, render_template, request

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

app = Flask(__name__)
app.json.ensure_ascii = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024

@app.get('/')
def index():
    return render_template('index.html')

@app.post('/api/ask')
def ask():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(error='Geçerli bir JSON isteği gönderin.'), 400
    question = payload.get('question', '')
    if not isinstance(question, str) or not question.strip():
        return jsonify(error='Lütfen bir soru yazın.'), 400
    question = question.strip()
    if len(question) > 2000:
        return jsonify(error='Soru en fazla 2000 karakter olabilir.'), 400
    try:
        from src.answer_v4 import answer_hybrid_v4
        answer, sources = answer_hybrid_v4(question)
        public_sources = []
        for source in sources:
            public_sources.append({key: source.get(key) for key in (
                'number', 'filename', 'page', 'title', 'authors', 'journal',
                'year', 'pmid', 'pmcid', 'doi', 'pubmed_url', 'doi_url',
                'rrf_score', 'rerank_score'
            )})
        return jsonify(answer=answer, sources=public_sources)
    except Exception:
        app.logger.exception('CardioRAG soru-cevap hatası')
        return jsonify(error='Yanıt oluşturulamadı. Terminaldeki hata kaydını kontrol edin.'), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False, threaded=False)
