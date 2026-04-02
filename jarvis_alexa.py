"""
jarvis_alexa.py — JARVIS v4.0 Alexa Skill Bridge (optional)

Exposes a Flask endpoint that Alexa calls via ngrok tunnel.
Alexa sends the transcript → JarvisCore processes it → returns speech response.

Usage: python jarvis_alexa.py (runs standalone on port 5000)
Or: import and call start_alexa_server(core) in main.py

Alexa intent schema (configure in Alexa Developer Console):
  JarvisCommand: "JARVIS {utterance}"
  AMAZON.StopIntent, AMAZON.CancelIntent
"""

import asyncio
import json
import logging
import threading
from typing import Optional

logger = logging.getLogger("jarvis.alexa")

try:
    from flask import Flask, request, jsonify
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    logger.warning("flask not installed — Alexa bridge disabled")


def _build_alexa_response(speech_text: str, end_session: bool = True) -> dict:
    return {
        "version": "1.0",
        "response": {
            "outputSpeech": {
                "type": "PlainText",
                "text": speech_text,
            },
            "shouldEndSession": end_session,
        },
    }


def create_alexa_app(core) -> Optional[object]:
    """Create Flask app with JARVIS Alexa skill endpoint."""
    if not FLASK_AVAILABLE:
        return None

    app = Flask(__name__)

    @app.route("/alexa", methods=["POST"])
    def alexa_endpoint():
        body = request.get_json(force=True)
        req_type = body.get("request", {}).get("type", "")

        if req_type == "LaunchRequest":
            return jsonify(_build_alexa_response(
                "JARVIS operativo, Sir. Come posso aiutarla?",
                end_session=False
            ))

        if req_type == "IntentRequest":
            intent_name = body["request"]["intent"]["name"]

            if intent_name in ("AMAZON.StopIntent", "AMAZON.CancelIntent"):
                return jsonify(_build_alexa_response("Arrivederci, Sir."))

            if intent_name == "JarvisCommand":
                slots = body["request"]["intent"].get("slots", {})
                utterance = slots.get("utterance", {}).get("value", "")
                if not utterance:
                    return jsonify(_build_alexa_response(
                        "Non ho capito, Sir. Può ripetere?", end_session=False
                    ))

                # Run async core in sync Flask context
                try:
                    loop = asyncio.new_event_loop()
                    result = loop.run_until_complete(core.process(utterance))
                    loop.close()
                    response_text = result["response"]
                except Exception as e:
                    logger.error("Alexa core error: %s", e)
                    response_text = "Si è verificato un errore, Sir."

                return jsonify(_build_alexa_response(response_text))

        if req_type == "SessionEndedRequest":
            return jsonify({"version": "1.0", "response": {}})

        return jsonify(_build_alexa_response("Tipo di richiesta non supportato."))

    return app


def start_alexa_server(core, port: int = 5000):
    """Start Alexa skill server in a daemon thread."""
    app = create_alexa_app(core)
    if not app:
        logger.warning("Cannot start Alexa server — Flask not available")
        return

    def _run():
        logger.info("Alexa bridge listening on port %d", port)
        app.run(host="0.0.0.0", port=port, debug=False)

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    logger.info("Alexa bridge started (thread)")
    return t


if __name__ == "__main__":
    # Standalone test mode with mock core
    import os
    import sys

    class MockCore:
        async def process(self, text, audio_bytes=None):
            return {"response": f"Mock response for: {text}", "mood": {"label": "neutral", "emoji": "😐"}}

    core = MockCore()
    app = create_alexa_app(core)
    if app:
        print("Alexa bridge test server on http://localhost:5000/alexa")
        app.run(host="0.0.0.0", port=5000, debug=True)
    else:
        print("Install flask: pip install flask")
