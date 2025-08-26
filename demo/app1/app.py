from flask import Flask, jsonify, request
import time, logging, os

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

_state = {"fault": False}
PORT = int(os.getenv("PORT","5001"))

@app.route("/health")
def health():
    if _state["fault"]:
        app.logger.error("ERROR: DB connection timeout - simulated")
        return jsonify({"ok": False, "reason": "db timeout"}), 500
    return jsonify({"ok": True})

@app.route("/trigger", methods=["POST"])
def trigger():
    _state["fault"] = True
    app.logger.info("FAULT triggered")
    return jsonify({"triggered": True})

@app.route("/recover", methods=["POST"])
def recover():
    _state["fault"] = False
    app.logger.info("Recovered via /recover")
    return jsonify({"recovered": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
