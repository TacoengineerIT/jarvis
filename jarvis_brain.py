import json
import subprocess
import webbrowser
import requests
from pathlib import Path
from thefuzz import fuzz
import random

# CARICA SCHEMA E FINANZE
def load_commands_schema():
    schema_file = Path("config") / "commands_schema.json"
    if schema_file.exists():
        with open(schema_file, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    return {}

def load_finances():
    finance_file = Path("config") / "finances.json"
    if finance_file.exists():
        with open(finance_file, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    return {"target_affitto": 110, "entrate_attuali": 0}

COMMANDS_SCHEMA = load_commands_schema()
FINANCES = load_finances()
OLLAMA_URL = "http://localhost:11434"
LOCAL_MODEL = "llama3.1:8b"

# ========== OLLAMA FUNCTIONS ==========

def is_ollama_available():
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False

def ask_ollama(prompt: str, system: str = ""):
    """Chiede a Ollama una risposta"""
    try:
        payload = {
            "model": LOCAL_MODEL,
            "prompt": prompt,
            "system": system,
            "temperature": 0.7,
            "stream": False
        }
        response = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=30)
        if response.status_code == 200:
            return response.json().get("response", "").strip()
    except:
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
        except:
            return f"Errore nell'apertura di {app_name} Sir."
    return f"{app_name} non trovato Sir."

def get_system_info_tool():
    """Info sistema reale"""
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory()
        return f"CPU: {cpu}%, RAM: {ram.percent}%, Disco: {psutil.disk_usage('/').percent}%"
    except:
        return "Sistema non disponibile Sir."

def check_finances_tool():
    """Check finanze reali"""
    target = FINANCES.get("target_affitto", 110)
    entrate = FINANCES.get("entrate_attuali", 0)
    gap = target - entrate
    
    if gap > 0:
        return f"Signore, mancano {gap:.2f}€ per l'affitto di {target}€."
    else:
        return f"Congratulazioni, surplus di {abs(gap):.2f}€."

def screenshot_tool():
    """Fa uno screenshot reale"""
    try:
        import pyautogui
        path = Path.home() / "Desktop" / "screenshot_jarvis.png"
        pyautogui.screenshot(str(path))
        return "Screenshot salvato sul Desktop Sir."
    except:
        return "Pyautogui non disponibile Sir."

# ========== ROUTING LOGIC ==========

ACTION_VERBS = ["apri", "avvia", "lancia", "chiudi", "termina", "metti", "riproduci", 
                "stoppa", "segna", "aggiungi", "check", "stato", "screenshot"]

QUESTION_WORDS = ["come", "cosa", "chi", "quando", "dove", "perché", "qual", "dimmi", 
                  "spiega", "raccontami", "cosa ne pensi", "sei", "puoi", "riesci"]

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
    
    # SISTEMA
    if any(w in u for w in ["cpu", "ram", "memoria", "disco", "stato sistema"]):
        return get_system_info_tool()
    
    # FINANZE
    if any(w in u for w in ["affitto", "manca", "gap", "110", "stato", "finanze"]):
        return check_finances_tool()
    
    return None

def handle_conversation(user_input):
    """Conversazione con contesto (umorismo Stark)"""
    u = user_input.lower()
    
    gap = FINANCES.get("target_affitto", 110) - FINANCES.get("entrate_attuali", 0)
    
    responses = {
        "greeting": [
            f"Buonasera Tony. Tutti i sistemi operativi. Peccato il suo conto non sia altrettanto sano (gap: {gap:.2f}€).",
            "Buonasera Tony. Tutto a posto Sir.",
            "Presente Sir. Tutti i sistemi attivi.",
        ],
        "status": [
            f"Sarei più rilassato se il suo conto non sembrasse un deserto del Nevada, Sir. Mancano {gap:.2f}€.",
            f"Perfetto Sir. Mancano ancora {gap:.2f}€ per l'affitto, ma la strada è in discesa.",
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
    
    return "Sir, di che cosa parla?"

def process_input(user_input):
    """Triple Logic Router con priorità ai COMANDI"""
    
    # PRIORITÀ 1: Ha verbi d'azione? → Esegui subito (Tool Use)
    if has_action_verb(user_input):
        result = execute_action(user_input)
        if result:
            return result
    
    # PRIORITÀ 2: È una domanda? → Usa Ollama
    if is_question(user_input):
        if is_ollama_available():
            answer = ask_ollama(user_input)
            if answer:
                return answer
        return "Sir, Ollama non è disponibile in questo momento."
    
    # PRIORITÀ 3: È conversazione? → Rispondi con stile
    return handle_conversation(user_input)
