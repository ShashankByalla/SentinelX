from flask import Flask, jsonify
import logging, os
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
PORT = int(os.getenv("PORT","5002"))

@app.route("/health")
def health():
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
