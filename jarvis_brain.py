"""
JARVIS Brain — Command routing, Ollama LLM, tool use.
Triple logic router: Action verbs → Questions → Conversation.
"""
import json
import subprocess
import webbrowser
import requests
import random
from pathlib import Path
from thefuzz import fuzz

from finance_engine import check_gap, get_report, load_finances
from survival_recipes import get_budget_recipe, get_super_cheap_recipe
from jarvis_home import get_bridge as get_ha_bridge
from jarvis_system_eye import get_eye

# ========== CONFIG ==========

def load_commands_schema():
    schema_file = Path("config") / "commands_schema.json"
    if schema_file.exists():
        try:
            with open(schema_file, "r", encoding="utf-8-sig") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}

COMMANDS_SCHEMA = load_commands_schema()
OLLAMA_URL = "http://localhost:11434"
LOCAL_MODEL = "llama3.1:8b"

JARVIS_SYSTEM_PROMPT = (
    "Sei JARVIS, l'assistente AI personale di Tony. "
    "Parli in italiano con tono da maggiordomo britannico, ironico ma rispettoso. "
    "Chiami l'utente 'Tony' o 'Sir'. Rispondi in modo conciso (2-3 frasi max). "
    "Sei spiritoso come il JARVIS di Iron Man."
)

# ========== OLLAMA FUNCTIONS ==========

def is_ollama_available():
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        return response.status_code == 200
    except Exception:
        return False

def _build_system_prompt() -> str:
    """Build dynamic system prompt with context awareness."""
    try:
        context = get_eye().get_summary()
        return f"{JARVIS_SYSTEM_PROMPT}\n\nContesto attuale: {context}"
    except Exception:
        return JARVIS_SYSTEM_PROMPT


def ask_ollama(prompt: str, system: str = ""):
    """Chiede a Ollama una risposta con JARVIS persona."""
    try:
        payload = {
            "model": LOCAL_MODEL,
            "prompt": prompt,
            "system": system or _build_system_prompt(),
            "temperature": 0.7,
            "stream": False
        }
        response = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=30)
        if response.status_code == 200:
            return response.json().get("response", "").strip()
    except Exception:
        pass
    return None

# ========== TOOL USE FUNCTIONS ==========

def open_app_tool(app_name):
    """Apre un'app reale"""
    apps = {
        "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "notepad": "notepad.exe",
        "calc": "calc.exe",
        "youtube": lambda: webbrowser.open("https://youtube.com"),
        "google": lambda: webbrowser.open("https://google.com"),
        "spotify": lambda: webbrowser.open("https://spotify.com"),
    }

    app_name = app_name.lower().strip()
    if app_name in apps:
        try:
            if callable(apps[app_name]):
                apps[app_name]()
            else:
                subprocess.Popen(apps[app_name], creationflags=subprocess.DETACHED_PROCESS)
            return f"Avvio {app_name} Sir."
        except Exception:
            return f"Errore nell'apertura di {app_name} Sir."
    return f"{app_name} non trovato Sir."

def get_system_info_tool():
    """Info sistema reale"""
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory()
        return f"CPU al {cpu} percento, RAM al {ram.percent} percento, Disco al {psutil.disk_usage('/').percent} percento, Sir."
    except Exception:
        return "Informazioni di sistema non disponibili Sir."

def check_finances_tool():
    """Check finanze dal finance engine."""
    _gap, msg = check_gap()
    return msg

def get_finance_report_tool():
    """Report finanziario completo."""
    return get_report()

def get_recipe_tool(user_input: str):
    """Suggerisce una ricetta economica."""
    u = user_input.lower()

    # Detect budget from input
    budget = 2.00  # default
    for word in u.split():
        try:
            val = float(word.replace("€", "").replace(",", "."))
            if 0 < val < 50:
                budget = val
                break
        except ValueError:
            pass

    # Detect time constraint
    time_limit = None
    if any(w in u for w in ["veloce", "fretta", "subito", "rapido"]):
        time_limit = 15

    result = get_budget_recipe(budget, time_minutes=time_limit)
    return result["messaggio"]

def home_action_tool(user_input: str):
    """Handle home automation commands."""
    ha = get_ha_bridge()
    if not ha.available:
        return "Home Assistant non è configurato, Sir. Configuri il file config/home_assistant.json."

    u = user_input.lower()

    # "stato casa" / "dispositivi" → get all states
    if "stato casa" in u or "dispositivi" in u or "stato dispositivi" in u:
        return ha.get_all_states()

    # Extract device name from common patterns
    device = None
    for keyword in ["accendi", "spegni", "alterna"]:
        if keyword in u:
            # Take everything after the keyword
            idx = u.index(keyword) + len(keyword)
            device = u[idx:].strip().rstrip(".")
            break

    if "luminosità" in u or "brightness" in u:
        # Parse "luminosità luce camera al 50%"
        parts = u.split("luminosità")[-1].strip()
        # Try to extract percentage
        import re
        pct_match = re.search(r"(\d+)\s*%?", parts)
        pct = int(pct_match.group(1)) if pct_match else 50
        dev = re.sub(r"\d+\s*%?|al\b", "", parts).strip()
        return ha.set_brightness(dev or "luce camera", pct)

    if "temperatura" in u:
        import re
        parts = u.split("temperatura")[-1].strip()
        temp_match = re.search(r"(\d+(?:\.\d+)?)", parts)
        temp = float(temp_match.group(1)) if temp_match else 21.0
        dev = re.sub(r"\d+(?:\.\d+)?|gradi|a\b", "", parts).strip()
        return ha.set_temperature(dev or "termostato", temp)

    if device:
        if "accendi" in u:
            return ha.turn_on(device)
        elif "spegni" in u:
            return ha.turn_off(device)
        elif "alterna" in u:
            return ha.toggle(device)

    # Check state of specific device
    if "stato" in u:
        for alias in ha._aliases:
            if alias in u:
                return ha.get_state(alias)

    return "Non ho capito il comando domotica, Sir. Provi con 'accendi luce camera' o 'stato casa'."


def screenshot_tool():
    """Fa uno screenshot reale"""
    try:
        import pyautogui
        path = Path.home() / "Desktop" / "screenshot_jarvis.png"
        pyautogui.screenshot(str(path))
        return "Screenshot salvato sul Desktop Sir."
    except Exception:
        return "Pyautogui non disponibile Sir."

# ========== ROUTING LOGIC ==========

ACTION_VERBS = ["apri", "avvia", "lancia", "chiudi", "termina", "metti", "riproduci",
                "stoppa", "segna", "aggiungi", "check", "screenshot"]

QUESTION_WORDS = ["come", "cosa", "chi", "quando", "dove", "perché", "qual", "dimmi",
                  "spiega", "raccontami", "cosa ne pensi", "sei", "puoi", "riesci"]

# Finance trigger phrases (checked via fuzzy match)
FINANCE_TRIGGERS = [
    "situazione affitto", "come sto con l'affitto", "report finanziario",
    "stato affitto", "quanto manca per l'affitto", "soldi affitto",
    "budget affitto", "entrate e uscite", "finanze", "gap affitto",
]

# Recipe trigger phrases
RECIPE_TRIGGERS = [
    "cosa cucino", "cosa mangio", "ricetta", "ricette", "fame",
    "suggerisci qualcosa da mangiare", "pranzo economico", "cena economica",
    "cosa posso cucinare",
]

# Home automation triggers
HOME_TRIGGERS = [
    "accendi", "spegni", "alterna", "luminosità", "temperatura",
    "luce", "luci", "lampada", "ventilatore", "condizionatore",
    "termostato", "stato casa", "dispositivi",
]

def _fuzzy_match(user_input: str, triggers: list, threshold: int = 70) -> bool:
    """Check if user_input fuzzy-matches any trigger phrase."""
    u = user_input.lower()
    for trigger in triggers:
        if trigger in u:
            return True
        if fuzz.partial_ratio(u, trigger) >= threshold:
            return True
    return False


def is_question(user_input):
    """Controlla se è una domanda"""
    u = user_input.lower()
    return any(word in u for word in QUESTION_WORDS) or u.endswith("?")

def has_action_verb(user_input):
    """Controlla se ci sono verbi d'azione"""
    u = user_input.lower()
    return any(verb in u for verb in ACTION_VERBS)

def execute_action(user_input):
    """Esegue l'azione REALE - Tool Use"""
    u = user_input.lower()

    # APERTURA APP
    if any(w in u for w in ["apri", "avvia", "lancia"]):
        for app in ["chrome", "youtube", "spotify", "google", "notepad", "calc"]:
            if app in u:
                return open_app_tool(app)

    # SCREENSHOT
    if "screenshot" in u or "schermata" in u:
        return screenshot_tool()

    # SISTEMA (more specific check — avoid conflict with finance "stato")
    if any(w in u for w in ["cpu", "ram", "memoria", "disco"]):
        return get_system_info_tool()
    if "stato sistema" in u or "stato del sistema" in u:
        return get_system_info_tool()

    return None

def handle_conversation(user_input):
    """Conversazione con contesto (umorismo Stark)"""
    u = user_input.lower()

    gap, _ = check_gap()

    responses = {
        "greeting": [
            f"Buonasera Tony. Tutti i sistemi operativi. Per l'affitto mancano ancora {gap:.2f} euro, ma non è il momento di piangere.",
            "Buonasera Tony. Tutto a posto Sir.",
            "Presente Sir. Tutti i sistemi attivi.",
        ],
        "status": [
            f"Sarei più rilassato se il suo conto non sembrasse un deserto del Nevada, Sir. Mancano {gap:.2f} euro.",
            f"Perfetto Sir. Mancano ancora {gap:.2f} euro per l'affitto, ma la strada è in discesa.",
            "Sistema operazionale, Sir. Come sempre, monitorando il suo budget.",
        ]
    }

    if any(w in u for w in ["ciao", "buonasera", "buongiorno"]):
        return random.choice(responses["greeting"])

    if any(w in u for w in ["come stai", "come sta", "va bene"]):
        return random.choice(responses["status"])

    # Se è domanda, chiedi a Ollama
    if is_question(user_input):
        if is_ollama_available():
            answer = ask_ollama(user_input)
            if answer:
                return answer
        return "Sir, non sono riuscito a rispondere a quella domanda."

    return "Sir, non ho capito. Può ripetere?"

def process_input(user_input):
    """
    Main router — processes user input through priority layers:
    1. Finance triggers (fuzzy matched)
    2. Recipe triggers (fuzzy matched)
    3. Action verbs → tool use
    4. Questions → Ollama
    5. Conversation fallback
    """
    # PRIORITY 0: Finance check (fuzzy matched)
    if _fuzzy_match(user_input, FINANCE_TRIGGERS):
        return get_finance_report_tool()

    # PRIORITY 0b: Home automation (check before recipes — avoids fuzzy false positives)
    if any(t in user_input.lower() for t in HOME_TRIGGERS):
        ha = get_ha_bridge()
        if ha.available:
            return home_action_tool(user_input)

    # PRIORITY 0c: Recipe request (fuzzy matched)
    if _fuzzy_match(user_input, RECIPE_TRIGGERS):
        return get_recipe_tool(user_input)

    # PRIORITY 1: Action verbs → tool use
    if has_action_verb(user_input):
        result = execute_action(user_input)
        if result:
            return result

    # PRIORITY 2: Questions → Ollama
    if is_question(user_input):
        if is_ollama_available():
            answer = ask_ollama(user_input)
            if answer:
                return answer
        return "Sir, Ollama non è disponibile in questo momento."

    # PRIORITY 3: Conversation / NLU fallback
    result = handle_conversation(user_input)
    if result == "Sir, non ho capito. Può ripetere?":
        # Last resort: try Ollama as general NLU
        print(f"[BRAIN] No intent matched for: {user_input!r} — trying Ollama NLU fallback")
        if is_ollama_available():
            answer = ask_ollama(user_input)
            if answer:
                return answer
    return result
