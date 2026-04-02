"""
JARVIS Flask Backend v4.1 — Dynamic State + Command Parser
"""

import re
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Global state — all UI fields live here
jarvis_state = {
    "jarvis_state": "LISTENING",
    "mood": "😐",
    "mood_score": 5.0,
    "mood_trend": "stable",
    "user_input": "",
    "response": "",
    "timestamp": datetime.now().isoformat(),
    "last_5_commands": [],
    "conversation_history": [],
    "api_cost_today": 0.0,
    "today_spent": 0.0,
    "next_event": None,
    "briefing": "SYSTEMS NOMINAL · JARVIS V4.1 ONLINE",
    "budget_alerts": [],
    "error": None,
    # Financial fields (modifiable via commands)
    "portfolio_balance": 2000.0,
    "rent_gap": 110.0,
    "daily_burn": 42.50,
    "runway": 14,
    "monthly_budget": 2000.0,
    "monthly_spent": 960.0,
}


# ── Command Parser ────────────────────────────────────────────────

def parse_command(text):
    """
    Try to parse a command that mutates jarvis_state.
    Returns (response_str, mutated: bool).
    """
    t = text.lower().strip()

    # ── Portfolio balance ────────────────────────────────────────
    m = re.search(
        r'(modifica|cambia|imposta|set|porta)\s+(portfolio|balance|saldo)[\w\s]*?([€$]?\s*(\d+(?:[.,]\d+)?))',
        t
    )
    if m:
        val = float(m.group(4).replace(',', '.'))
        jarvis_state['portfolio_balance'] = val
        return f"Portfolio balance aggiornato a €{val:,.2f}, Sir.", True

    # ── Rent gap ─────────────────────────────────────────────────
    m = re.search(
        r'(modifica|cambia|imposta|set)\s+(rent[\s_]?gap|affitto|gap)[\w\s]*?([€$]?\s*(\d+(?:[.,]\d+)?))',
        t
    )
    if m:
        val = float(m.group(4).replace(',', '.'))
        jarvis_state['rent_gap'] = val
        return f"Rent gap aggiornato a €{val:.2f}, Sir.", True

    # ── Daily burn ───────────────────────────────────────────────
    m = re.search(
        r'(modifica|cambia|imposta)\s+(burn|spesa\s*giornaliera|daily)[\w\s]*?([€$]?\s*(\d+(?:[.,]\d+)?))',
        t
    )
    if m:
        val = float(m.group(4).replace(',', '.'))
        jarvis_state['daily_burn'] = val
        return f"Daily burn aggiornato a €{val:.2f}, Sir.", True

    # ── Runway ───────────────────────────────────────────────────
    m = re.search(
        r'(modifica|cambia|imposta)\s+(runway|giorni)[\w\s]*?(\d+)',
        t
    )
    if m:
        val = int(m.group(3))
        jarvis_state['runway'] = val
        return f"Runway aggiornato a {val} giorni, Sir.", True

    # ── Add money to portfolio ───────────────────────────────────
    m = re.search(
        r'(aggiungi|deposita|guadagnato)\s*[€$]?\s*(\d+(?:[.,]\d+)?)\s*(euro|€|eur)?',
        t
    )
    if m:
        val = float(m.group(2).replace(',', '.'))
        jarvis_state['portfolio_balance'] = jarvis_state['portfolio_balance'] + val
        return (
            f"Aggiunto €{val:.2f} al portfolio. Nuovo saldo: €{jarvis_state['portfolio_balance']:,.2f}, Sir.",
            True
        )

    # ── Spend money ──────────────────────────────────────────────
    m = re.search(
        r'(speso|spendi|sottrai|paga[to]*)\s*[€$]?\s*(\d+(?:[.,]\d+)?)\s*(euro|€|eur)?',
        t
    )
    if m:
        val = float(m.group(2).replace(',', '.'))
        jarvis_state['portfolio_balance'] = max(0, jarvis_state['portfolio_balance'] - val)
        jarvis_state['today_spent'] = jarvis_state['today_spent'] + val
        jarvis_state['monthly_spent'] = jarvis_state['monthly_spent'] + val
        return (
            f"€{val:.2f} sottratti. Saldo residuo: €{jarvis_state['portfolio_balance']:,.2f}, Sir.",
            True
        )

    # ── Monthly budget ───────────────────────────────────────────
    m = re.search(
        r'(modifica|imposta|set)\s+(budget|mensile)[\w\s]*?([€$]?\s*(\d+(?:[.,]\d+)?))',
        t
    )
    if m:
        val = float(m.group(4).replace(',', '.'))
        jarvis_state['monthly_budget'] = val
        return f"Budget mensile impostato a €{val:,.2f}, Sir.", True

    # ── Reset finances ───────────────────────────────────────────
    if any(w in t for w in ['reset finanze', 'azzera finanze', 'reset finance']):
        jarvis_state['today_spent'] = 0.0
        jarvis_state['monthly_spent'] = 0.0
        jarvis_state['portfolio_balance'] = 2000.0
        return "Finanze resettate ai valori di default, Sir.", True

    # ── Status report ────────────────────────────────────────────
    if any(w in t for w in ['stato finanze', 'report', 'situazione', 'bilancio']):
        s = jarvis_state
        return (
            f"Situazione attuale: Portfolio €{s['portfolio_balance']:,.2f} · "
            f"Rent gap €{s['rent_gap']:.2f} · "
            f"Burn €{s['daily_burn']:.2f}/g · "
            f"Runway {s['runway']} giorni · "
            f"Budget mensile {(s['monthly_spent']/s['monthly_budget']*100):.0f}% consumato.",
            False
        )

    return None, False


def static_response(text, mood):
    t = text.lower()
    responses = {
        'ciao':           'Buongiorno, Sir! Come posso assisterti?',
        'hello':          'Hello, Sir! What can I do for you?',
        'come stai':      'Sono perfettamente operativo, grazie per aver chiesto.',
        'che ora è':      f'Sono le {datetime.now().strftime("%H:%M:%S")}, Sir.',
        'buongiorno':     'Buongiorno, Sir. Tutto pronto.',
        'grazie':         'Prego, Sir. A suo servizio.',
        'cosa puoi fare': (
            'Posso modificare portfolio, rent gap, budget e spese. '
            'Prova: "aggiungi 500 euro", "modifica rent gap a 80", "situazione finanze".'
        ),
        'chi sei':        'Sono J.A.R.V.I.S. v4.1, il tuo assistente personale. Operativo al 100%.',
        'aiuto':          (
            'Comandi disponibili: "modifica portfolio a NNN" · "aggiungi NNN euro" · '
            '"speso NNN euro" · "modifica rent gap a NNN" · "situazione finanze" · '
            '"modifica daily burn a NNN" · "modifica runway a NNN giorni".'
        ),
    }
    for key, resp in responses.items():
        if key in t:
            return resp
    return f"Comando registrato: '{text}'. In attesa di istruzioni operative, Sir."


def detect_mood(text):
    t = text.lower()
    if any(w in t for w in ['ciao', 'hello', 'grazie', 'bello', 'ottimo', 'perfetto']):
        return '😊'
    elif any(w in t for w in ['no', 'male', 'triste', 'pessimo']):
        return '😞'
    elif any(w in t for w in ['stressato', 'arrabbiato', 'basta']):
        return '😤'
    return '😐'


def mood_to_score(mood):
    return {'😊': 8.0, '😞': 3.0, '😤': 2.0}.get(mood, 5.0)


def check_budget_alerts():
    alerts = []
    pct = (jarvis_state['monthly_spent'] / jarvis_state['monthly_budget']) * 100 if jarvis_state['monthly_budget'] else 0
    if pct > 90:
        alerts.append({"message": f"Budget mensile al {pct:.0f}% — limite critico."})
    elif pct > 75:
        alerts.append({"message": f"Budget mensile al {pct:.0f}%."})
    if jarvis_state['rent_gap'] > 0 and jarvis_state['runway'] < 7:
        alerts.append({"message": f"Runway critico: {jarvis_state['runway']} giorni rimanenti."})
    jarvis_state['budget_alerts'] = alerts


# ── Routes ────────────────────────────────────────────────────────

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "version": "4.1"})


@app.route('/api/state', methods=['GET'])
def get_state():
    check_budget_alerts()
    return jsonify(jarvis_state)


@app.route('/api/input', methods=['POST'])
def handle_input():
    try:
        data = request.json
        text = data.get('text', '').strip()
        if not text:
            return jsonify({"error": "Empty input"})

        mood = detect_mood(text)

        # Try command parser first
        cmd_response, mutated = parse_command(text)
        response = cmd_response if cmd_response else static_response(text, mood)

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
            "timestamp": jarvis_state["timestamp"],
            "mutated": mutated,
        })
        if len(jarvis_state["conversation_history"]) > 50:
            jarvis_state["conversation_history"] = jarvis_state["conversation_history"][-50:]
        jarvis_state["last_5_commands"] = jarvis_state["conversation_history"][-5:]

        check_budget_alerts()

        return jsonify({
            "success": True,
            "response": response,
            "mood": mood,
            "mood_score": jarvis_state["mood_score"],
            "jarvis_state": "LISTENING",
            "conversation_history": jarvis_state["conversation_history"],
            # Live financial state (so UI updates immediately)
            "portfolio_balance": jarvis_state["portfolio_balance"],
            "rent_gap": jarvis_state["rent_gap"],
            "daily_burn": jarvis_state["daily_burn"],
            "runway": jarvis_state["runway"],
            "monthly_budget": jarvis_state["monthly_budget"],
            "monthly_spent": jarvis_state["monthly_spent"],
            "today_spent": jarvis_state["today_spent"],
            "budget_alerts": jarvis_state["budget_alerts"],
        })
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route('/api/wake', methods=['POST'])
def wake_word():
    jarvis_state["jarvis_state"] = "ACTIVE"
    jarvis_state["timestamp"] = datetime.now().isoformat()
    return jsonify({"success": True, "jarvis_state": "ACTIVE"})


@app.route('/api/history', methods=['GET'])
def get_history():
    return jsonify({"history": jarvis_state["conversation_history"]})


@app.route('/api/reset', methods=['POST'])
def reset():
    jarvis_state["conversation_history"] = []
    jarvis_state["last_5_commands"] = []
    jarvis_state["response"] = ""
    jarvis_state["user_input"] = ""
    return jsonify({"success": True})


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("🚀 JARVIS v4.1 — Dynamic State API Server")
    print("=" * 60)
    print("\n📡 Commands you can send:")
    print("  'modifica portfolio a 500'")
    print("  'aggiungi 200 euro'")
    print("  'speso 50 euro'")
    print("  'modifica rent gap a 80'")
    print("  'modifica daily burn a 35'")
    print("  'modifica runway a 20 giorni'")
    print("  'situazione finanze'")
    print("  'aiuto'")
    print("\n🌐 Running on http://localhost:5000")
    print("=" * 60 + "\n")
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
