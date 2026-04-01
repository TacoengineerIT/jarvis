"""
JARVIS Control — PC automation functions.
"""
import subprocess
import webbrowser


APPS = {
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "notepad": "notepad.exe",
    "calc": "calc.exe",
}

WEBSITES = {
    "youtube": "https://youtube.com",
    "google": "https://google.com",
    "spotify": "https://spotify.com",
    "github": "https://github.com",
}


def open_app(name):
    name = name.lower().strip()
    if name in APPS:
        try:
            subprocess.Popen(APPS[name], creationflags=subprocess.DETACHED_PROCESS)
            return f"{name} aperto Sir."
        except Exception:
            return f"Errore nell'apertura di {name} Sir."
    return f"{name} non trovato Sir."


def get_system_info():
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory()
        return f"CPU: {cpu}%, RAM: {ram.percent}%, Disco: {psutil.disk_usage('/').percent}%"
    except Exception:
        return "System info non disponibile."


def get_app_list() -> dict:
    return dict(APPS)


def get_website_list() -> dict:
    return dict(WEBSITES)
