"""
JARVIS Brain - Routing intelligente: Ollama per conversazioni, fuzzy matching per comandi.
Fallback graceful se Ollama non disponibile.
"""

import json
import subprocess
import webbrowser
import requests
from pathlib import Path
from thefuzz import fuzz
import random

# ─── Config ──────────────────────────────────────────────────────────────────

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.1:8b"
OLLAMA_TIMEOUT = 15  # secondi

ACTION_VERBS = [
    "apri", "avvia", "lancia", "chiudi", "termina", "metti", "riproduci",
    "stoppa", "segna", "aggiungi", "check", "stato", "screenshot", "crea",
    "scrivi", "ricetta", "quanto"
]

QUESTION_SIGNALS = [
    "?", "come", "cosa", "perché", "quando", "dove", "chi", "qual",
    "puoi", "potresti", "sai", "dimmi", "spiegami", "hai", "pensi",
    "cos'è", "che cos", "aiutami", "help"
]

# ─── Loaders ─────────────────────────────────────────────────────────────────

def load_commands_schema() -> dict:
    schema_file = Path("config") / "commands_schema.json"
    if schema_file.exists():
        try:
            with open(schema_file, "r", encoding="utf-8-sig") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def load_finances() -> dict:
    finance_file = Path("config") / "finances.json"
    if finance_file.exists():
        try:
            with open(finance_file, "r", encoding="utf-8-sig") as f:
                return json.load(f)
        except Exception:
            pass
    return {"target_affitto": 110, "entrate_attuali": 0}


COMMANDS_SCHEMA = load_commands_schema()
FINANCES = load_finances()

# ─── Ollama ───────────────────────────────────────────────────────────────────

def is_ollama_available() -> bool:
    """Verifica se Ollama è raggiungibile."""
    try:
        resp = requests.get("http://localhost:11434", timeout=3)
        return resp.status_code == 200
    except Exception:
        return False


def ask_ollama(prompt: str, context: list = None) -> str:
    """
    Chiede a Ollama (llama3.1:8b) e ritorna la risposta.
    Usa il contesto degli ultimi scambi se disponibile.
    Falls back a risposta generica se Ollama non raggiungibile.
    """
    # Costruisci il messaggio con system prompt
    system = (
        "Sei JARVIS, assistente AI personale di Antonio (Tony). "
        "Personalità: elegante, sarcastico, british, sempre con classe. "
        "Chiama l'utente Tony o Sir in modo naturale e variato. "
        "Rispondi SEMPRE in italiano, massimo 3 frasi brevi perché vengono lette ad alta voce. "
        "Sii diretto, brillante e mai banale."
    )

    # Includi contesto conversazione se disponibile
    context_text = ""
    if context:
        recent = context[-3:]  # ultimi 3 scambi
        context_text = "\n".join([
            f"Tony: {ex['user']}\nJARVIS: {ex['jarvis']}"
            for ex in recent
        ])
        full_prompt = f"{context_text}\nTony: {prompt}"
    else:
        full_prompt = prompt

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": full_prompt,
        "system": system,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "num_predict": 200
        }
    }

    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=OLLAMA_TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("response", "").strip()
        else:
            return _fallback_response()
    except requests.exceptions.Timeout:
        return "Ollama impiega troppo, Tony. Riprova tra un momento Sir."
    except Exception:
        return _fallback_response()


def _fallback_response() -> str:
    """Risposta generica quando Ollama non è disponibile."""
    responses = [
        "Ollama è offline, Sir. Sto operando in modalità limitata.",
        "I miei circuiti neurali sono temporaneamente irraggiungibili, Tony. Riprova.",
        "Connessione a Ollama assente. Posso gestire solo comandi diretti, Sir.",
    ]
    return random.choice(responses)

# ─── Tools ───────────────────────────────────────────────────────────────────

def open_app_tool(app_name: str) -> str:
    apps = {
        "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "notepad": "notepad.exe",
        "calc": "calc.exe",
        "youtube": lambda: webbrowser.open("https://youtube.com"),
        "google": lambda: webbrowser.open("https://google.com"),
        "spotify": lambda: webbrowser.open("https://spotify.com"),
        "discord": lambda: webbrowser.open("https://discord.com/app"),
    }

    app_name = app_name.lower().strip()
    if app_name in apps:
        try:
            if callable(apps[app_name]):
                apps[app_name]()
            else:
                subprocess.Popen(
                    apps[app_name],
                    creationflags=subprocess.DETACHED_PROCESS
                )
            variants = [
                f"Avvio {app_name} Sir.",
                f"{app_name.capitalize()} pronto Tony.",
                f"Fatto Sir, {app_name} è aperto."
            ]
            return random.choice(variants)
        except FileNotFoundError:
            return f"{app_name} non trovato sul sistema Sir. Verificare il percorso."
        except Exception as e:
            return f"Errore nell'apertura di {app_name}: {e}"

    return f"{app_name} non nel mio dizionario Sir. Aggiungerlo alla config?"


def get_system_info_tool() -> str:
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        commentary = ""
        if cpu > 85:
            commentary = " Sta minando criptovalute Sir, o ha aperto Excel."
        elif ram.percent > 85:
            commentary = " La RAM è quasi satura Tony."
        return (
            f"CPU: {cpu:.0f}%  |  RAM: {ram.percent:.0f}% "
            f"({ram.used // (1024**3):.1f}GB/{ram.total // (1024**3):.0f}GB)  |  "
            f"Disco: {disk.percent:.0f}%.{commentary}"
        )
    except ImportError:
        return "psutil non installato Sir. pip install psutil"
    except Exception as e:
        return f"Sistema non disponibile: {e}"


def check_finances_tool() -> str:
    target = FINANCES.get("target_affitto", 110)
    entrate = FINANCES.get("entrate_attuali", 0)
    gap = target - entrate

    if gap > 0:
        return (
            f"Signore, mancano {gap:.2f}€ per l'affitto di {target}€. "
            f"Entrate attuali: {entrate:.2f}€."
        )
    else:
        return f"Congratulazioni Tony, surplus di {abs(gap):.2f}€ rispetto al target."


def screenshot_tool() -> str:
    try:
        import pyautogui
        path = Path.home() / "Desktop" / "screenshot_jarvis.png"
        pyautogui.screenshot(str(path))
        return f"Screenshot salvato sul Desktop Sir. ({path.name})"
    except ImportError:
        return "pyautogui non installato Sir."
    except Exception as e:
        return f"Screenshot fallito: {e}"


def write_file_tool(filename: str, content: str) -> str:
    """
    Scrive un file nella cartella JARVIS_Files sul Desktop.
    Crea la cartella se non esiste.
    """
    try:
        jarvis_dir = Path.home() / "Desktop" / "JARVIS_Files"
        jarvis_dir.mkdir(parents=True, exist_ok=True)

        # Sanitizza il nome file
        safe_name = "".join(c for c in filename if c.isalnum() or c in "._- ").strip()
        if not safe_name:
            safe_name = "jarvis_output.txt"

        file_path = jarvis_dir / safe_name
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return f"File salvato Sir: {file_path}"
    except PermissionError:
        return "Permesso negato Tony. Non riesco a scrivere sul Desktop."
    except Exception as e:
        return f"Errore scrittura file: {e}"


def get_recipe_tool(budget: float, time_minutes: int = None) -> str:
    """Wrapper per survival_recipes.get_budget_recipe()."""
    try:
        from survival_recipes import get_budget_recipe
        result = get_budget_recipe(budget, time_minutes)
        return result["messaggio"]
    except ImportError:
        return "Modulo ricette non disponibile Sir."
    except Exception as e:
        return f"Errore ricette: {e}"

# ─── Routing ─────────────────────────────────────────────────────────────────

def is_question(user_input: str) -> bool:
    """
    Rileva se l'input è una domanda/conversazione (→ Ollama)
    vs un comando diretto (→ fuzzy matching tool).
    """
    u = user_input.lower().strip()
    if u.endswith("?"):
        return True
    return any(signal in u for signal in QUESTION_SIGNALS)


def has_action_verb(user_input: str) -> bool:
    u = user_input.lower()
    return any(verb in u for verb in ACTION_VERBS)


def execute_action(user_input: str) -> str | None:
    """Esegue azioni dirette basate su keyword matching."""
    u = user_input.lower()

    # Apri app
    if any(w in u for w in ["apri", "avvia", "lancia"]):
        for app in ["chrome", "youtube", "spotify", "google", "notepad", "calc", "discord"]:
            if app in u:
                return open_app_tool(app)

    # Screenshot
    if "screenshot" in u or "schermata" in u:
        return screenshot_tool()

    # Info sistema
    if any(w in u for w in ["cpu", "ram", "memoria", "disco", "stato sistema", "info sistema"]):
        return get_system_info_tool()

    # Finanze
    if any(w in u for w in ["affitto", "manca", "gap", "110", "finanze", "soldi", "budget"]):
        return check_finances_tool()

    # Ricette
    if any(w in u for w in ["ricetta", "mangiare", "cucinare", "cosa mangio"]):
        # Tenta di estrarre budget dal testo (es. "ricetta con 2 euro")
        budget = _extract_budget(u)
        return get_recipe_tool(budget)

    # Scrivi file
    if any(w in u for w in ["crea file", "scrivi file", "salva file", "crea un file"]):
        # Estrai contenuto dopo "con" o ":"
        content = user_input
        for sep in ["con ", "con:", ": "]:
            if sep in u:
                idx = u.index(sep) + len(sep)
                content = user_input[idx:]
                break
        return write_file_tool("jarvis_note.txt", content)

    return None


def _extract_budget(text: str) -> float:
    """Estrae un importo in euro dal testo (es. '2 euro', '1.5€')."""
    import re
    patterns = [
        r"(\d+[.,]\d+)\s*€",
        r"(\d+[.,]\d+)\s*euro",
        r"(\d+)\s*€",
        r"(\d+)\s*euro",
        r"con\s+(\d+[.,]?\d*)"
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            return float(m.group(1).replace(",", "."))
    return 5.0  # default 5€


def process_input(user_input: str, context: list = None) -> str:
    """
    Entry point principale del brain.
    1. Se è un comando → esegui tool direttamente
    2. Se è una domanda/conversazione → chiedi a Ollama
    3. Fallback → messaggio generico
    """
    if not user_input or not user_input.strip():
        return "Sir, non ho sentito nulla."

    # Prima: comandi espliciti (alta priorità)
    if has_action_verb(user_input) and not is_question(user_input):
        result = execute_action(user_input)
        if result:
            return result

    # Secondo: domande e conversazione → Ollama
    if is_question(user_input) or not has_action_verb(user_input):
        return ask_ollama(user_input, context=context)

    # Terzo: prova comunque execute_action
    result = execute_action(user_input)
    if result:
        return result

    # Fallback finale
    return ask_ollama(user_input, context=context)
