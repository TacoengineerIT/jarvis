"""
JARVIS Finance Engine — Rent gap tracker with JSON persistence.
Tracks monthly income vs target rent (default 110€).
"""
import json
from pathlib import Path

FINANCE_FILE = Path("config") / "finances.json"

_DEFAULT = {
    "target_affitto": 110.0,
    "entrate_attuali": 0.0,
    "voci_entrata": []
}


def _ensure_dir():
    FINANCE_FILE.parent.mkdir(parents=True, exist_ok=True)


def load_finances() -> dict:
    if FINANCE_FILE.exists():
        try:
            with open(FINANCE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Merge with defaults for missing keys
            for k, v in _DEFAULT.items():
                data.setdefault(k, v)
            return data
        except (json.JSONDecodeError, OSError):
            pass
    return dict(_DEFAULT)


def save_finances(data: dict):
    _ensure_dir()
    with open(FINANCE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def check_gap() -> tuple[float, str]:
    """Returns (gap_amount, tts_message). Positive gap = still owe money."""
    data = load_finances()
    target = data.get("target_affitto", 110.0)
    entrate = data.get("entrate_attuali", 0.0)
    gap = target - entrate

    if gap > 0:
        msg = f"Signore, mancano {gap:.2f} euro per l'affitto di {target:.0f} euro."
    elif gap == 0:
        msg = f"Obiettivo raggiunto Sir. Affitto di {target:.0f} euro coperto esattamente."
    else:
        msg = f"Surplus di {abs(gap):.2f} euro oltre l'obiettivo di {target:.0f} euro, Sir. Ottimo lavoro."
    return gap, msg


def update_finances(new_income: float, new_target: float = None):
    """Update current income and optionally the rent target."""
    data = load_finances()
    data["entrate_attuali"] = new_income
    if new_target is not None:
        data["target_affitto"] = new_target
    save_finances(data)


def add_income(amount: float, description: str = ""):
    """Add an income entry and update the total."""
    data = load_finances()
    data["voci_entrata"].append({"importo": amount, "descrizione": description})
    data["entrate_attuali"] = data.get("entrate_attuali", 0.0) + amount
    save_finances(data)


def get_report() -> str:
    """Returns a TTS-friendly financial report."""
    data = load_finances()
    target = data.get("target_affitto", 110.0)
    entrate = data.get("entrate_attuali", 0.0)
    gap = target - entrate
    voci = data.get("voci_entrata", [])

    lines = [f"Report finanziario, Sir."]
    lines.append(f"Obiettivo affitto: {target:.0f} euro.")
    lines.append(f"Entrate attuali: {entrate:.2f} euro.")

    if gap > 0:
        lines.append(f"Mancano ancora {gap:.2f} euro. Coraggio Tony.")
    else:
        lines.append(f"Surplus di {abs(gap):.2f} euro. Ottima gestione, Sir.")

    if voci:
        lines.append(f"Voci di entrata registrate: {len(voci)}.")

    return " ".join(lines)
