"""
jarvis_ws_server.py — JARVIS v4.0 WebSocket + REST Server

Serves the React frontend and exposes:
  WS  /ws              — real-time state broadcast + text input
  GET /api/state       — current state snapshot (JSON)
  POST /api/input      — send text command to JARVIS
  GET /api/finance     — monthly financial summary
  GET /api/finance/daily — today's spending
  GET /api/calendar    — today's events
  GET /api/mood/trend  — 7-day mood trend
  GET /                — serve React build (frontend/dist/)

Usage:
  python jarvis_ws_server.py [--port 8765] [--dev]
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import date, datetime
from pathlib import Path

from aiohttp import web, WSMsgType
import aiohttp

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s — %(message)s",
)
logger = logging.getLogger("jarvis.ws_server")

# ── Env / Config ──────────────────────────────────────────────────────────────

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
SERVER_PORT = int(os.environ.get("JARVIS_WS_PORT", 8765))
FRONTEND_DIST = Path(__file__).parent / "frontend" / "dist"

# ── JARVIS modules (optional — graceful fallback) ─────────────────────────────

_core = None
_memory = None
_finance = None


def _init_modules():
    global _core, _memory, _finance
    try:
        from jarvis_memory import JarvisMemory
        _memory = JarvisMemory()
        logger.info("[INIT] JarvisMemory loaded (%d conversations)", _memory.stats()["conversations"])
    except Exception as e:
        logger.warning("[INIT] JarvisMemory unavailable: %s", e)

    if ANTHROPIC_API_KEY:
        try:
            from jarvis_core import JarvisCore
            _core = JarvisCore(api_key=ANTHROPIC_API_KEY, memory=_memory)
            logger.info("[INIT] JarvisCore loaded (Haiku + Sonnet)")
        except Exception as e:
            logger.warning("[INIT] JarvisCore unavailable: %s", e)
    else:
        logger.warning("[INIT] ANTHROPIC_API_KEY not set — local fallback only")

    if _memory:
        try:
            from jarvis_finance import FinanceManager
            _finance = FinanceManager(memory=_memory)
            logger.info("[INIT] FinanceManager loaded")
        except Exception as e:
            logger.warning("[INIT] FinanceManager unavailable: %s", e)


# ── Shared JARVIS state ───────────────────────────────────────────────────────

class JARVISState:
    def __init__(self):
        self.jarvis_state = "LISTENING"
        self.mood = "neutral"
        self.mood_score = 5.0
        self.mood_trend = "stable"
        self.user_input = ""
        self.response = ""
        self.timestamp = datetime.now().isoformat()
        self.last_5_commands: list[dict] = []
        self.api_cost_today = 0.0
        self.today_spent = 0.0
        self.next_event: dict | None = None
        self.briefing = "Tutti i sistemi operativi. In ascolto, Sir."
        self.budget_alerts: list[dict] = []

    def to_dict(self) -> dict:
        return {
            "type":            "state",
            "jarvis_state":    self.jarvis_state,
            "mood":            self.mood,
            "mood_score":      self.mood_score,
            "mood_trend":      self.mood_trend,
            "user_input":      self.user_input,
            "response":        self.response,
            "timestamp":       self.timestamp,
            "last_5_commands": self.last_5_commands,
            "api_cost_today":  self.api_cost_today,
            "today_spent":     self.today_spent,
            "next_event":      self.next_event,
            "briefing":        self.briefing,
            "budget_alerts":   self.budget_alerts,
        }


_state = JARVISState()
_ws_clients: set[web.WebSocketResponse] = set()


async def _broadcast(data: dict):
    """Broadcast JSON message to all connected WebSocket clients."""
    msg = json.dumps(data, ensure_ascii=False)
    dead = set()
    for ws in list(_ws_clients):
        try:
            await ws.send_str(msg)
        except Exception:
            dead.add(ws)
    _ws_clients.difference_update(dead)


def _refresh_live_data():
    """Pull latest data from modules into _state (sync, fast)."""
    global _state
    if _finance:
        try:
            summary = _finance.get_monthly_summary()
            _state.today_spent = _finance.get_daily_spending()
            alerts = _finance.check_budget_alerts()
            _state.budget_alerts = alerts[:3]
        except Exception:
            pass

    if _memory:
        try:
            from jarvis_memory_semantic import SemanticMemoryManager
            sem = SemanticMemoryManager(memory=_memory)
            trend = sem.get_mood_trend(days=7)
            _state.mood_trend = trend.get("direction", "stable")
        except Exception:
            pass

        try:
            from jarvis_calendar import CalendarManager
            cal = CalendarManager(memory=_memory)
            nxt = cal.get_next_event()
            if nxt:
                _state.next_event = {
                    "title":      nxt.get("title", ""),
                    "start_time": nxt.get("start_time", ""),
                }
        except Exception:
            pass


# ── WebSocket handler ─────────────────────────────────────────────────────────

async def ws_handler(request: web.Request) -> web.WebSocketResponse:
    ws = web.WebSocketResponse(heartbeat=30)
    await ws.prepare(request)
    _ws_clients.add(ws)
    logger.info("[WS] Client connected (%d total)", len(_ws_clients))

    # Send current state immediately on connect
    _refresh_live_data()
    await ws.send_str(json.dumps(_state.to_dict()))

    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                except json.JSONDecodeError:
                    data = {"type": "input", "text": msg.data}

                if data.get("type") == "input":
                    asyncio.create_task(_handle_text_input(data.get("text", "")))

            elif msg.type in (WSMsgType.ERROR, WSMsgType.CLOSE):
                break
    finally:
        _ws_clients.discard(ws)
        logger.info("[WS] Client disconnected (%d total)", len(_ws_clients))

    return ws


async def _handle_text_input(text: str):
    """Process text through JarvisCore and broadcast state changes."""
    global _state
    text = text.strip()
    if not text:
        return

    _state.jarvis_state = "PROCESSING"
    _state.user_input = text
    _state.timestamp = datetime.now().isoformat()
    await _broadcast(_state.to_dict())

    # Process
    response_text = ""
    mood_label = "neutral"
    mood_score = 5.0

    if _core:
        try:
            result = await _core.process(text)
            response_text = result.get("response", "")
            mood_data = result.get("mood", {})
            mood_label = mood_data.get("label", "neutral")
            mood_score = float(mood_data.get("score", 5.0))
            _state.api_cost_today += _estimate_cost(result.get("model", "haiku"))
        except Exception as e:
            logger.error("[PROCESS] Error: %s", e)
            response_text = f"Errore nel processamento, Sir: {str(e)[:80]}"
    else:
        response_text = _local_fallback(text)

    # Update state
    _state.jarvis_state = "SPEAKING"
    _state.response = response_text
    _state.mood = mood_label
    _state.mood_score = mood_score
    _state.timestamp = datetime.now().isoformat()

    # Track command history (last 5)
    _state.last_5_commands.append({
        "input":      text,
        "response":   response_text[:120],
        "mood":       mood_label,
        "mood_score": mood_score,
        "timestamp":  _state.timestamp,
    })
    _state.last_5_commands = _state.last_5_commands[-5:]

    # Refresh financial / calendar data
    _refresh_live_data()
    await _broadcast(_state.to_dict())

    # Return to LISTENING after brief pause
    await asyncio.sleep(2)
    _state.jarvis_state = "LISTENING"
    await _broadcast(_state.to_dict())


def _estimate_cost(model: str) -> float:
    """Rough token cost estimate (EUR)."""
    rates = {"haiku": 0.0002, "sonnet": 0.003, "local": 0.0, "cache": 0.0}
    return rates.get(model, 0.001)


def _local_fallback(text: str) -> str:
    """Simple keyword responses when no API key is configured."""
    t = text.lower()
    if any(w in t for w in ["ciao", "hello", "salve"]):
        return "Buongiorno, Sir. Tutti i sistemi operativi."
    if any(w in t for w in ["status", "stato", "come stai"]):
        return "Sistema al massimo delle capacità, Sir."
    if any(w in t for w in ["speso", "budget", "soldi"]):
        return "Configura ANTHROPIC_API_KEY per analisi finanziaria completa."
    return f"Ricevuto: '{text[:40]}'. Configura ANTHROPIC_API_KEY per risposte complete."


# ── REST API handlers ─────────────────────────────────────────────────────────

async def api_state(request: web.Request) -> web.Response:
    _refresh_live_data()
    return web.json_response(_state.to_dict())


async def api_input(request: web.Request) -> web.Response:
    try:
        body = await request.json()
        text = body.get("text", "").strip()
    except Exception:
        return web.json_response({"error": "Invalid JSON"}, status=400)
    if not text:
        return web.json_response({"error": "Empty input"}, status=400)
    asyncio.create_task(_handle_text_input(text))
    return web.json_response({"queued": True, "input": text})


async def api_finance(request: web.Request) -> web.Response:
    if not _finance:
        return web.json_response({"error": "FinanceManager not available"}, status=503)
    try:
        summary = _finance.get_monthly_summary()
        alerts = _finance.check_budget_alerts()
        return web.json_response({"summary": summary, "alerts": alerts})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


async def api_finance_daily(request: web.Request) -> web.Response:
    if not _finance:
        return web.json_response({"error": "FinanceManager not available"}, status=503)
    try:
        today = _finance.get_daily_spending()
        return web.json_response({"today_spent": today, "date": date.today().isoformat()})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


async def api_calendar(request: web.Request) -> web.Response:
    if not _memory:
        return web.json_response({"events": []})
    try:
        from jarvis_calendar import CalendarManager
        cal = CalendarManager(memory=_memory)
        ctx = cal.get_schedule_context()
        today_str = date.today().isoformat()
        events = _memory.get_events_for_date(today_str)
        return web.json_response({"events": events, "context": ctx})
    except Exception as e:
        return web.json_response({"events": [], "error": str(e)})


async def api_mood_trend(request: web.Request) -> web.Response:
    if not _memory:
        return web.json_response({"trend": "unknown", "avg_score": 5.0})
    try:
        from jarvis_memory_semantic import SemanticMemoryManager
        sem = SemanticMemoryManager(memory=_memory)
        trend = sem.get_mood_trend(days=7)
        return web.json_response(trend)
    except Exception as e:
        return web.json_response({"trend": "unknown", "error": str(e)})


async def api_news(request: web.Request) -> web.Response:
    if not _memory:
        return web.json_response({"articles": []})
    try:
        articles = _memory.get_recent_news(limit=5)
        briefing = _memory.get_morning_briefing(date.today().isoformat())
        return web.json_response({"articles": articles, "briefing": briefing})
    except Exception as e:
        return web.json_response({"articles": [], "error": str(e)})


# ── Static file serving ───────────────────────────────────────────────────────

async def index_handler(request: web.Request) -> web.Response:
    index = FRONTEND_DIST / "index.html"
    if index.exists():
        return web.FileResponse(index)
    return web.Response(
        text='<h1>JARVIS v4.0</h1><p>Build the frontend: <code>cd frontend && npm run build</code></p>',
        content_type="text/html",
    )


# ── App factory ───────────────────────────────────────────────────────────────

def create_app() -> web.Application:
    app = web.Application()

    # CORS middleware (allow Vite dev server)
    @web.middleware
    async def cors_middleware(request, handler):
        response = await handler(request)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    app.middlewares.append(cors_middleware)

    # Routes
    app.router.add_get("/ws", ws_handler)
    app.router.add_get("/api/state", api_state)
    app.router.add_post("/api/input", api_input)
    app.router.add_get("/api/finance", api_finance)
    app.router.add_get("/api/finance/daily", api_finance_daily)
    app.router.add_get("/api/calendar", api_calendar)
    app.router.add_get("/api/mood/trend", api_mood_trend)
    app.router.add_get("/api/news", api_news)

    # Serve React build
    if FRONTEND_DIST.exists():
        app.router.add_static("/assets", FRONTEND_DIST / "assets", name="assets")
    app.router.add_get("/{tail:.*}", index_handler)

    return app


async def periodic_broadcast():
    """Broadcast state updates every 10s to keep clients alive."""
    while True:
        await asyncio.sleep(10)
        if _ws_clients:
            _refresh_live_data()
            await _broadcast(_state.to_dict())


async def startup(app):
    asyncio.create_task(periodic_broadcast())


def main():
    _init_modules()
    app = create_app()
    app.on_startup.append(startup)

    logger.info("=" * 60)
    logger.info("  J.A.R.V.I.S. v4.0 WebSocket Server")
    logger.info("  http://localhost:%d", SERVER_PORT)
    logger.info("  ws://localhost:%d/ws", SERVER_PORT)
    logger.info("  API key: %s", "✓ SET" if ANTHROPIC_API_KEY else "✗ NOT SET")
    logger.info("  Frontend: %s", "✓ built" if FRONTEND_DIST.exists() else "✗ run npm run build")
    logger.info("=" * 60)

    web.run_app(app, host="0.0.0.0", port=SERVER_PORT, access_log=None)


if __name__ == "__main__":
    main()
