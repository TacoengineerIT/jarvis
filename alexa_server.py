from flask import Flask, request, jsonify
from jarvis_brain import process_input, ask_ollama
import json

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
        request_type = data.get('request', {}).get('type', '')

        # LaunchRequest — "Alexa, apri jarvis"
        if request_type == 'LaunchRequest':
            print("[ALEXA] LaunchRequest ricevuto")
            return jsonify(build_response(
                "Buonasera Sir. Sono JARVIS. Come posso assisterla?",
                should_end_session=False
            ))

        # SessionEndedRequest
        if request_type == 'SessionEndedRequest':
            print("[ALEXA] Sessione chiusa")
            return jsonify(build_response("Arrivederci Sir.", should_end_session=True))

        intent_name = data.get('request', {}).get('intent', {}).get('name')
        slots = data.get('request', {}).get('intent', {}).get('slots', {})
        
        print(f"[ALEXA] Intent: {intent_name}")
        
        # ASSISTENT JARVIS — Il jolly che passa tutto a JARVIS Brain
        if intent_name == 'AssistenzaJarvis':
            query = slots.get('query', {}).get('value', '')
            print(f"[ALEXA] Query: {query}")
            
            if query:
                # Passa COMPLETAMENTE a jarvis_brain (che usa Ollama)
                response = process_input(query)
                print(f"[ALEXA] Response: {response}")
                return jsonify(build_response(response, should_end_session=False))
        
        # STATO SISTEMA
        elif intent_name == 'StatoSistemaIntent':
            prompt = "Dammi un briefing dello stato del sistema e del mio budget di 110€ per l'affitto in modo breve e diretto"
            response = ask_ollama(prompt)
            if not response:
                response = "Sistema online Sir. Tutti i parametri nominali."
            return jsonify(build_response(response, should_end_session=False))
        
        # LIFE MANAGEMENT
        elif intent_name == 'LifeManagementIntent':
            action = slots.get('action', {}).get('value', '')
            # Passa a JARVIS Brain
            response = process_input(action)
            return jsonify(build_response(response, should_end_session=False))
        
        # EMOTIONAL SUPPORT
        elif intent_name == 'EmotionalSupportIntent':
            prompt = "Sono stanco e scoraggiato. Dammi un incoraggiamento breve e genuino, come un amico vero"
            response = ask_ollama(prompt)
            if not response:
                response = "Lo so Sir, anche per me è stata dura. Ma è proprio quando sembra impossibile che conta di più continuare."
            return jsonify(build_response(response, should_end_session=False))
        
        # STUDY SESSION
        elif intent_name == 'StudySessionIntent':
            topic = slots.get('topic', {}).get('value', '')
            prompt = f"Spiegami brevemente (2-3 frasi) il concetto di: {topic}. Modo conversazionale."
            response = ask_ollama(prompt)
            if not response:
                response = f"Mi dispiace Sir, ma non riesco a ricordare bene {topic}. Verifichiamo insieme su un documento?"
            return jsonify(build_response(response, should_end_session=False))
        
        # FALLBACK
        print(f"[ALEXA] Intent sconosciuto: {intent_name}")
        response = ask_ollama("Un utente ha detto qualcosa che non capisco. Cosa potrei rispondere in modo gentile?")
        if not response:
            response = "Mi dispiace Sir, non ho capito. Potrebbe ripetere?"
        return jsonify(build_response(response, should_end_session=False))
    
    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify(build_response(f"Errore: {str(e)}", should_end_session=False)), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
