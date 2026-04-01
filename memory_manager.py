import json
import threading
from pathlib import Path
from datetime import datetime

MEMORY_FILE = Path("memory.json")
_file_lock = threading.Lock()


def load_memory():
    if MEMORY_FILE.exists():
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {"conversations": [], "preferences": {}}


def save_memory(data):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def add_to_memory(user_input, response):
    with _file_lock:
        data = load_memory()
        data["conversations"].append({
            "user": user_input,
            "response": response,
            "timestamp": datetime.now().isoformat()
        })

        # Mantieni solo ultimi 20 scambi
        if len(data["conversations"]) > 20:
            data["conversations"] = data["conversations"][-20:]

        save_memory(data)


def get_context():
    data = load_memory()
    if not data["conversations"]:
        return ""

    # Ritorna gli ultimi 5 scambi come contesto
    recent = data["conversations"][-5:]
    context = "\n".join([f"Tony: {c['user']}\nJARVIS: {c['response']}" for c in recent])
    return context


def extract_preferences(user_input):
    with _file_lock:
        data = load_memory()

        if "spotify" in user_input.lower() or "musica" in user_input.lower():
            data["preferences"]["last_music_query"] = user_input
        if "ricetta" in user_input.lower() or "mangiare" in user_input.lower():
            data["preferences"]["interested_in_food"] = True

        save_memory(data)
