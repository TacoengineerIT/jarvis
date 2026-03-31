"""
JARVIS Memory Manager - Salva gli ultimi 20 scambi e personalizza le risposte.
Dimentica automaticamente i ricordi più vecchi di 7 giorni.
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

MEMORY_FILE = Path("memory.json")
MAX_EXCHANGES = 20
MAX_AGE_DAYS = 7


def _load_raw() -> dict:
    """Carica memory.json. Se corrotto o mancante, ritorna struttura vuota."""
    if not MEMORY_FILE.exists():
        return _empty_memory()
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Valida struttura minima
        if "exchanges" not in data or "preferences" not in data:
            return _empty_memory()
        return data
    except (json.JSONDecodeError, KeyError, TypeError):
        print("[Memory] File corrotto, ricreato da zero.")
        return _empty_memory()


def _empty_memory() -> dict:
    return {
        "exchanges": [],
        "preferences": {
            "musica": [],
            "app_frequenti": [],
            "orari_attivi": [],
            "ricette_preferite": []
        },
        "user_name": "Tony",
        "created_at": datetime.now().isoformat()
    }


def _save(data: dict):
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Memory] Errore salvataggio: {e}")


def _purge_old(data: dict) -> dict:
    """Rimuove scambi più vecchi di MAX_AGE_DAYS."""
    cutoff = datetime.now() - timedelta(days=MAX_AGE_DAYS)
    data["exchanges"] = [
        ex for ex in data["exchanges"]
        if datetime.fromisoformat(ex.get("timestamp", "2000-01-01")) > cutoff
    ]
    return data


def save_exchange(user_input: str, jarvis_response: str):
    """Salva uno scambio utente↔JARVIS nella memoria persistente."""
    data = _load_raw()
    data = _purge_old(data)

    exchange = {
        "timestamp": datetime.now().isoformat(),
        "user": user_input,
        "jarvis": jarvis_response
    }
    data["exchanges"].append(exchange)

    # Mantieni solo ultimi MAX_EXCHANGES
    if len(data["exchanges"]) > MAX_EXCHANGES:
        data["exchanges"] = data["exchanges"][-MAX_EXCHANGES:]

    # Aggiorna preferenze in base al contenuto
    _extract_preferences(data, user_input)

    _save(data)


def _extract_preferences(data: dict, user_input: str):
    """Estrae e aggiorna preferenze implicite dalla conversazione."""
    u = user_input.lower()
    prefs = data["preferences"]

    # Musica
    music_keywords = ["lo-fi", "lofi", "jazz", "rock", "classica", "hip hop", "trap"]
    for kw in music_keywords:
        if kw in u and kw not in prefs["musica"]:
            prefs["musica"].append(kw)

    # App frequenti
    app_keywords = ["chrome", "vscode", "cursor", "spotify", "discord", "telegram", "notepad"]
    for app in app_keywords:
        if app in u:
            if app not in prefs["app_frequenti"]:
                prefs["app_frequenti"].append(app)
            else:
                # Sposta in cima (più recente = più frequente)
                prefs["app_frequenti"].remove(app)
                prefs["app_frequenti"].insert(0, app)

    # Ricette
    recipe_keywords = ["pasta", "riso", "uova", "lenticchie", "ricetta"]
    for kw in recipe_keywords:
        if kw in u and kw not in prefs["ricette_preferite"]:
            prefs["ricette_preferite"].append(kw)

    # Limita lunghezza liste
    for key in prefs:
        if isinstance(prefs[key], list):
            prefs[key] = prefs[key][:10]


def get_context(n: int = 5) -> list:
    """
    Ritorna gli ultimi n scambi come lista di dict {user, jarvis}.
    Utile per passare contesto a Ollama.
    """
    data = _load_raw()
    return data["exchanges"][-n:]


def get_personalized_hint() -> Optional[str]:
    """
    Ritorna un suggerimento personalizzato basato sulle preferenze memorizzate.
    Es: "Come sempre, vuole la musica lo-fi Sir?"
    """
    data = _load_raw()
    prefs = data["preferences"]

    hints = []

    if prefs["musica"]:
        fav = prefs["musica"][0]
        hints.append(f"Come sempre, vuole la musica {fav} Sir?")

    if prefs["app_frequenti"]:
        fav_app = prefs["app_frequenti"][0]
        hints.append(f"Apro subito {fav_app}, come al solito?")

    if not hints:
        return None

    import random
    return random.choice(hints)


def get_stats() -> dict:
    """Statistiche sulla memoria attuale."""
    data = _load_raw()
    exchanges = data["exchanges"]
    if not exchanges:
        return {"total": 0, "oldest": None, "newest": None, "preferences": data["preferences"]}

    return {
        "total": len(exchanges),
        "oldest": exchanges[0]["timestamp"],
        "newest": exchanges[-1]["timestamp"],
        "preferences": data["preferences"]
    }


def clear_memory():
    """Azzera completamente la memoria (usa con cautela)."""
    _save(_empty_memory())
    print("[Memory] Memoria azzerata.")


if __name__ == "__main__":
    print("=== Test Memory Manager ===")
    save_exchange("apri chrome", "Chrome aperto Sir.")
    save_exchange("metti musica lo-fi", "Lo-fi in riproduzione.")
    save_exchange("come stai?", "Perfettamente calibrato, Tony.")

    ctx = get_context(3)
    print(f"Ultimi {len(ctx)} scambi:")
    for ex in ctx:
        print(f"  Tony: {ex['user']}")
        print(f"  JARVIS: {ex['jarvis']}")

    hint = get_personalized_hint()
    if hint:
        print(f"\nSuggerimento: {hint}")

    stats = get_stats()
    print(f"\nStatistiche: {stats['total']} scambi memorizzati")
    print(f"Preferenze: {stats['preferences']}")
