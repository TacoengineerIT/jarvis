"""
JARVIS Flask Backend — Simple, Works
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Global state
jarvis_state = {
    "jarvis_state": "LISTENING",
    "mood": "😐",
    "mood_score": 5.0,
    "user_input": "",
    "response": "",
    "timestamp": datetime.now().isoformat(),
    "last_5_commands": [],
    "conversation_history": [],
    "api_cost_today": 0.0,
    "today_spent": 0.0,
    "next_event": None,
    "error": None
}

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

@app.route('/api/state', methods=['GET'])
def get_state():
    try:
        return jsonify(jarvis_state)
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/input', methods=['POST'])
def handle_input():
    try:
        data = request.json
        text = data.get('text', '').strip()

        if not text:
            return jsonify({"error": "Empty input"})

        mood = detect_mood(text)
        response = generate_response(text, mood)

        global jarvis_state
        jarvis_state["user_input"] = text
        jarvis_state["response"] = response
        jarvis_state["mood"] = mood
        jarvis_state["mood_score"] = mood_to_score(mood)
        jarvis_state["timestamp"] = datetime.now().isoformat()
        jarvis_state["jarvis_state"] = "LISTENING"

        jarvis_state["conversation_history"].append({
            "user": text,
            "response": response,
            "mood": mood,
            "timestamp": jarvis_state["timestamp"]
        })

        if len(jarvis_state["conversation_history"]) > 50:
            jarvis_state["conversation_history"] = jarvis_state["conversation_history"][-50:]

        jarvis_state["last_5_commands"] = jarvis_state["conversation_history"][-5:]

        return jsonify({
            "success": True,
            "response": response,
            "mood": mood,
            "mood_score": jarvis_state["mood_score"],
            "jarvis_state": "LISTENING",
            "conversation_history": jarvis_state["conversation_history"]
        })
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/wake', methods=['POST'])
def wake_word():
    global jarvis_state
    jarvis_state["jarvis_state"] = "ACTIVE"
    return jsonify({"success": True, "jarvis_state": "ACTIVE"})

def detect_mood(text):
    text_lower = text.lower()
    if any(w in text_lower for w in ['ciao', 'hello', 'grazie', 'bello']):
        return '😊'
    elif any(w in text_lower for w in ['no', 'male', 'triste']):
        return '😞'
    elif any(w in text_lower for w in ['stressato', 'arrabbiato']):
        return '😤'
    return '😐'

def mood_to_score(mood):
    return {'😊': 8.0, '😞': 3.0, '😤': 2.0}.get(mood, 5.0)

def generate_response(text, mood):
    responses = {
        'ciao':       'Buongiorno, Sir!',
        'hello':      'Hello, Sir!',
        'come stai':  'Sono operativo al 100%, grazie.',
        'che ora è':  f'Sono le {datetime.now().strftime("%H:%M")}, Sir.',
        'buongiorno': 'Buongiorno, Sir. Tutto pronto.',
        'grazie':     'Prego, Sir. A suo servizio.',
    }
    for key, resp in responses.items():
        if key in text.lower():
            return resp
    return f'Ho elaborato: "{text}". Continua pure, Sir.'

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 JARVIS v4.0 — Backend")
    print("="*60)
    print("Running on http://localhost:5000\n")
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
