"""
JARVIS Alexa Server - Flask API for Amazon Echo integration
Permette a JARVIS di rispondere ai comandi da Alexa

Usage:
    python alexa_server.py

Oppure con Flask:
    flask run --host=0.0.0.0 --port=5000

Con ngrok per esposizione:
    ngrok http 5000
    # Usa l'URL HTTPS in Alexa Developer Console
"""
import os
import json
import logging
from flask import Flask, request, jsonify
from datetime import datetime

# Import JARVIS modules
from jarvis_brain import smart_answer, load_system_prompt
from jarvis_control import open_app, get_system_info
from finance_engine import check_gap

# ============================================================================
# SETUP
# ============================================================================

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(name)s - %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = load_system_prompt()

# ============================================================================
# ALEXA REQUEST/RESPONSE MODELS
# ============================================================================

class AlexaRequest:
    """Rappresenta una richiesta di Alexa."""
    
    def __init__(self, request_json):
        self.json = request_json
        self.intent_name = None
        self.slots = {}
        self.session_id = None
        
        self._parse()
    
    def _parse(self):
        """Parsa la richiesta Alexa."""
        try:
            request_obj = self.json.get('request', {})
            intent = request_obj.get('intent', {})
            
            self.intent_name = intent.get('name')
            self.slots = intent.get('slots', {})
            
            session = self.json.get('session', {})
            self.session_id = session.get('sessionId')
            
        except Exception as e:
            logger.error(f"Error parsing Alexa request: {e}")


class AlexaResponse:
    """Crea una risposta di Alexa."""
    
    def __init__(self, message, end_session=False):
        self.message = message
        self.end_session = end_session
    
    def to_json(self):
        """Converte a JSON format di Alexa."""
        return {
            "version": "1.0",
            "sessionAttributes": {},
            "response": {
                "outputSpeech": {
                    "type": "PlainText",
                    "text": self.message
                },
                "shouldEndSession": self.end_session,
                "card": {
                    "type": "Simple",
                    "title": "JARVIS",
                    "content": self.message
                }
            }
        }


# ============================================================================
# REQUEST HANDLERS
# ============================================================================

def handle_launch_request():
    """Handler per skill launch."""
    return AlexaResponse(
        "Buonasera, Tony. Sono JARVIS. Come posso assisterla?",
        end_session=False
    )


def handle_intent_request(alexa_req: AlexaRequest):
    """Handler per intent request."""
    intent = alexa_req.intent_name
    slots = alexa_req.slots
    
    logger.info(f"Intent: {intent}, Slots: {slots}")
    
    # Extract query from slots
    query = None
    if 'query' in slots:
        query = slots['query'].get('value', '')
    elif 'question' in slots:
        query = slots['question'].get('value', '')
    else:
        # Fallback: tutti gli slot
        query = " ".join([s.get('value', '') for s in slots.values() if s.get('value')])
    
    if not query:
        return AlexaResponse("Non ho capito la domanda. Puoi ripetere?")
    
    logger.info(f"Query: {query}")
    
    # Finanze
    if any(w in query.lower() for w in ["finanze", "gap", "manca", "110"]):
        gap, message = check_gap()
        return AlexaResponse(message, end_session=False)
    
    # App launch
    if any(w in query.lower() for w in ["apri", "lancia"]):
        for app in ["chrome", "spotify", "notepad"]:
            if app in query.lower():
                open_app(app)
                return AlexaResponse(f"{app.title()} avviato.", end_session=False)
    
    # Sistema
    if any(w in query.lower() for w in ["sistema", "cpu", "ram", "memoria"]):
        sys_info = get_system_info()
        return AlexaResponse(sys_info, end_session=False)
    
    # Default: usa AI
    answer, source = smart_answer(query, SYSTEM_PROMPT)
    logger.info(f"Response (source={source}): {answer[:100]}...")
    
    return AlexaResponse(answer, end_session=False)


def handle_session_ended_request():
    """Handler per session end."""
    return AlexaResponse("Arrivederci, Tony.", end_session=True)


# ============================================================================
# ALEXA ENDPOINT
# ============================================================================

@app.route('/alexa', methods=['POST'])
def alexa_endpoint():
    """
    Endpoint principale per Alexa skill.
    Configurare in Amazon Developer Console:
    https://xxxx.ngrok.io/alexa
    """
    try:
        # Log request
        logger.info(f"Alexa request received: {request.json}")
        
        # Parse
        alexa_req = AlexaRequest(request.json)
        
        # Verify signature (opzionale in dev, obbligatorio in prod)
        # verify_alexa_request_signature(request)
        
        # Route by request type
        request_type = request.json.get('request', {}).get('type')
        
        if request_type == 'LaunchRequest':
            response = handle_launch_request()
        elif request_type == 'IntentRequest':
            response = handle_intent_request(alexa_req)
        elif request_type == 'SessionEndedRequest':
            response = handle_session_ended_request()
        else:
            response = AlexaResponse("Tipo di richiesta non riconosciuto.")
        
        # Log response
        logger.info(f"Alexa response: {response.message[:100]}...")
        
        return jsonify(response.to_json())
    
    except Exception as e:
        logger.error(f"Error handling Alexa request: {e}", exc_info=True)
        error_response = AlexaResponse("Si è verificato un errore. Riprova.")
        return jsonify(error_response.to_json()), 500


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "JARVIS Alexa Server"
    }), 200


# ============================================================================
# DIAGNOSTICS
# ============================================================================

@app.route('/debug/request', methods=['POST'])
def debug_request():
    """Debug endpoint per testare richieste."""
    try:
        alexa_req = AlexaRequest(request.json)
        
        return jsonify({
            "status": "OK",
            "intent": alexa_req.intent_name,
            "slots": alexa_req.slots,
            "session_id": alexa_req.session_id
        }), 200
    
    except Exception as e:
        return jsonify({"status": "ERROR", "error": str(e)}), 400


@app.route('/debug/skills', methods=['GET'])
def debug_skills():
    """List disponibili skills."""
    return jsonify({
        "skills": [
            {
                "name": "AssistenzaJarvis",
                "invocation": "jarvis",
                "intents": [
                    "AssistenzaJarvis",
                    "AskQuery",
                    "LaunchQuery"
                ]
            }
        ]
    }), 200


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(400)
def bad_request(error):
    """Handle 400 Bad Request."""
    logger.error(f"Bad request: {error}")
    return jsonify({"error": "Bad request"}), 400


@app.errorhandler(404)
def not_found(error):
    """Handle 404 Not Found."""
    logger.error(f"Not found: {error}")
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 Internal Server Error."""
    logger.error(f"Internal error: {error}")
    alexa_response = AlexaResponse("Errore interno del server.")
    return jsonify(alexa_response.to_json()), 500


# ============================================================================
# STARTUP
# ============================================================================

if __name__ == '__main__':
    logger.info("🚀 JARVIS Alexa Server starting...")
    logger.info("Listening on http://0.0.0.0:5000")
    logger.info("Expose with ngrok: ngrok http 5000")
    logger.info("Configure Alexa endpoint: https://xxxx.ngrok.io/alexa")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        threaded=True
    )

    logger.info("JARVIS Alexa Server shutting down...")

# ============================================================================
# SETUP INSTRUCTIONS
# ============================================================================
"""
AMAZON ALEXA SKILL SETUP

1. Go to Amazon Developer Console
   https://developer.amazon.com/console/ask

2. Create new skill
   Name: JARVIS
   Primary language: Italian
   Model: Custom
   Backend: Provision your own (self-hosted)

3. Define intents
   
   Intent: AssistenzaJarvis
   Samples:
     - assistenza jarvis
     - chiedi a jarvis
     - jarvis {query}
   
   Slots:
     - query (type: AMAZON.AlphaNumeric)

4. Set endpoint
   HTTPS endpoint:
   https://xxxx.ngrok.io/alexa
   
   (Obtain ngrok URL by running: ngrok http 5000)

5. Configure account linking (optional)
   Not required for local testing

6. Test in simulator
   "Alexa, ask jarvis quanto manca ai 110"
   → JARVIS responds with gap message

7. Deploy to Echo device
   Link same Amazon account
   Enable JARVIS skill
   Say "Alexa, open jarvis"

TESTING LOCALLY

1. Start server:
   python alexa_server.py

2. In another terminal, start ngrok:
   ngrok http 5000
   
3. Copy HTTPS URL from ngrok

4. Set endpoint in Developer Console

5. Test in simulator or on device

NGROK FREE TIER

- Limited to 40 req/min
- Session timeout after 2 hours
- For production, use stable endpoint

DEBUGGING

Check logs:
   docker logs jarvis-alexa

Test request:
   curl -X POST http://localhost:5000/debug/request \\
     -H "Content-Type: application/json" \\
     -d '{"request": {"intent": {"name": "Test"}}}'

"""
