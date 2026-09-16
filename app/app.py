import json
import queue
import threading
from flask import Flask, Response, jsonify, render_template, request, stream_with_context
import sys
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from rag_query import rag_query


app = Flask(__name__)


@app.route("/ask", methods=["POST"])
def ask():

    data = request.get_json()

    question = data.get("question", "").strip()

    if not question:
        return jsonify({
            "error": "الرجاء إدخال سؤال."
        }), 400

    def generate():
        events = queue.Queue()

        def report(progress):
            events.put({"type": "progress", "value": progress})

        events.put({"type": "progress", "value": 0})
        outcome = {}

        def run_query():
            try:
                outcome["result"] = rag_query(question, progress_callback=report)
            except Exception as error:
                outcome["error"] = str(error)
            finally:
                events.put(None)

        threading.Thread(target=run_query, daemon=True).start()

        while True:
            event = events.get()
            if event is None:
                break
            yield json.dumps(event, ensure_ascii=False) + "\n"

        if "error" in outcome:
            yield json.dumps({"type": "error", "error": outcome["error"]}, ensure_ascii=False) + "\n"
            return

        answer, sources = outcome["result"]
        yield json.dumps({
            "type": "result",
            "answer": answer,
            "sources": sources,
        }, ensure_ascii=False) + "\n"

    return Response(
        stream_with_context(generate()),
        mimetype="application/x-ndjson",
    )


@app.route("/")
def home():

    return render_template("index.html")


if __name__ == "__main__":

    app.run(
    host="127.0.0.1",
    port=5000,
    debug=False
    )