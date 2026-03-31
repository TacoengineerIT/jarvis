"""
JARVIS Agent - Main loop completo.
Supporta: input testo, input voce, output voce, conversazione Ollama,
          tool use, memoria persistente.
"""

from jarvis_brain import process_input, is_ollama_available
from jarvis_voice import say
from memory_manager import save_exchange, get_context, get_personalized_hint


class JarvisAgent:
    def __init__(self):
        self.voice_output = True  # Abilita TTS

    def _respond(self, text: str):
        """Stampa e opzionalmente legge la risposta."""
        if self.voice_output:
            say(text, print_also=True)
        else:
            print(f"JARVIS: {text}")

    def _get_voice_input(self) -> str:
        """Tenta trascrizione vocale, fallback a input testo."""
        try:
            from jarvis_voice_input import listen_and_transcribe
            result = listen_and_transcribe()
            if result:
                print(f"[Trascritto]: {result}")
                return result
            else:
                print("[JARVIS] Non ho rilevato nulla. Usa il testo.")
                return input("Tony> ").strip()
        except ImportError:
            print("[JARVIS] Modulo voce non disponibile. Usa input testo.")
            return input("Tony> ").strip()
        except Exception as e:
            print(f"[JARVIS] Errore microfono: {e}. Usa input testo.")
            return input("Tony> ").strip()

    def run(self):
        # Status check
        ollama_ok = is_ollama_available()
        status = "Ollama ✓" if ollama_ok else "Ollama offline"

        self._respond(f"Buonasera Tony. Tutti i sistemi operativi. [{status}]")
        print("─" * 55)
        print("Comandi rapidi: 'voce' = mic | 'muto' = disabilita TTS")
        print("                'exit' = esci | 'help' = lista comandi")
        print("─" * 55)
        print()

        # Suggerimento personalizzato dalla memoria
        hint = get_personalized_hint()
        if hint:
            self._respond(hint)

        while True:
            # ── Input ──────────────────────────────────────────────
            try:
                raw = input("Tony> ").strip()
            except (KeyboardInterrupt, EOFError):
                self._respond("Arrivederci Tony. Alla prossima Sir.")
                break

            if not raw:
                continue

            # ── Comandi meta ───────────────────────────────────────
            low = raw.lower()

            if low in ("exit", "quit", "esci", "stop"):
                self._respond("Arrivederci Tony. Chiusura ordinata, Sir.")
                break

            if low == "voce":
                print("[JARVIS] Attivazione microfono...")
                raw = self._get_voice_input()
                if not raw:
                    continue
                low = raw.lower()

            if low == "muto":
                self.voice_output = not self.voice_output
                stato = "abilitato" if self.voice_output else "disabilitato"
                print(f"[JARVIS] Output vocale {stato}.")
                continue

            if low == "help":
                self._show_help()
                continue

            if low == "status":
                self._show_status()
                continue

            # ── Elaborazione ───────────────────────────────────────
            context = get_context(n=5)

            try:
                response = process_input(raw, context=context)
            except Exception as e:
                response = f"Errore interno Sir: {e}. Riprovo."

            if not response:
                response = "Sir, non ho una risposta per questo. Può riformulare?"

            self._respond(response)

            # ── Salva in memoria ───────────────────────────────────
            try:
                save_exchange(raw, response)
            except Exception:
                pass  # Memoria non critica, non bloccare

    def _show_help(self):
        help_text = """
Comandi disponibili:
  voce          → attiva input microfono
  muto          → attiva/disattiva output vocale
  status        → mostra stato sistemi
  exit          → chiudi JARVIS

Comandi tool:
  apri chrome/notepad/spotify/youtube
  screenshot    → cattura schermata
  cpu/ram       → info sistema
  affitto       → stato finanze
  ricetta [budget] → ricetta economica
  crea file ... → scrive file su Desktop

Conversazione:
  Qualsiasi domanda → risponde Ollama (se disponibile)
        """
        print(help_text)

    def _show_status(self):
        ollama = "✓ Online" if is_ollama_available() else "✗ Offline"
        tts = "✓ Attivo" if self.voice_output else "✗ Muto"
        from memory_manager import get_stats
        stats = get_stats()
        mem = f"{stats['total']} scambi memorizzati"

        print(f"""
─ JARVIS Status ─────────────────
  Ollama:   {ollama}
  TTS:      {tts}
  Memoria:  {mem}
─────────────────────────────────""")


if __name__ == "__main__":
    agent = JarvisAgent()
    agent.run()
