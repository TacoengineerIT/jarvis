from flask import Flask, request, jsonify
from jarvis_brain import process_input
import psutil

app = Flask(__name__)

def build_response(message, should_end_session=False):
    return {
        "version": "1.0",
        "response": {
            "outputSpeech": {"type": "PlainText", "text": message},
            "shouldEndSession": should_end_session
        }
    }

@app.route('/alexa', methods=['POST'])
def alexa_endpoint():
    try:
        data = request.json
        intent_name = data.get('request', {}).get('intent', {}).get('name')
        slots = data.get('request', {}).get('intent', {}).get('slots', {})
        
        if intent_name == 'StatoSistemaIntent':
            cpu = psutil.cpu_percent(interval=1)
            ram = psutil.virtual_memory().percent
            response = f"CPU al {cpu}%, RAM al {ram}%. Come posso aiutarla Sir?"
            return jsonify(build_response(response, should_end_session=False))
        
        elif intent_name == 'AssistenzaJarvis':
            query = slots.get('query', {}).get('value', '')
            if query:
                response = process_input(query)
                return jsonify(build_response(response, should_end_session=False))
        
        elif intent_name == 'EmotionalSupportIntent':
            response = "Lo so Sir, anche per me è stata dura. Comunque mancano 34€ all'affitto."
            return jsonify(build_response(response, should_end_session=False))
        
        return jsonify(build_response("Non ho capito Sir.", should_end_session=False))
    
    except Exception as e:
        return jsonify(build_response(f"Errore: {str(e)}", should_end_session=False)), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
