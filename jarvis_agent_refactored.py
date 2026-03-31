import random
import time
import os
from pathlib import Path

from jarvis_config import config
from jarvis_brain import process_input, is_ollama_available
from jarvis_voice import say
from finance_engine import check_gap
from memory_manager import add_to_memory, get_context

# FRASI INTRO RANDOMICHE
INTRO_VARIANTS = [
    "Oggi sono particolarmente utile con i suoi appunti universitari.",
    "Posso cercare qualsiasi cosa su internet in tempo reale.",
    "Controllo completo del suo PC. La prego, niente 47 tab aperti su Chrome.",
    "Sistema operativo ottimizzato per la procrastinazione... scherzo Sir.",
]

FAREWELLS = [
    "Arrivederci Tony. Cerchero di non annoiarmi troppo.",
    "Sistemi in standby. Si faccia vedere ogni tanto, Sir.",
    "Buona fortuna con quel codice, Sir. Torni quando ha problemi.",
]

class JarvisAgent:
    def __init__(self):
        self.history = []
        self.memory = []
        self.intro_shown = False
    
    def play_back_in_black(self):
        """Riproduce Back in Black intro"""
        try:
            if Path("backInBlack.mp3").exists():
                import pygame
                pygame.mixer.init()
                pygame.mixer.music.load("backInBlack.mp3")
                pygame.mixer.music.play()
                time.sleep(3)
            else:
                print("[JARVIS] Back in Black non trovato (opzionale)")
        except:
            pass
    
    def intro_sequence(self):
        """Intro con frasi randomiche"""
        self.play_back_in_black()
        
        say("Buonasera, Tony.")
        time.sleep(0.3)
        say("Sono JARVIS, il suo sistema di intelligenza artificiale personale.")
        time.sleep(0.2)
        
        variant = random.choice(INTRO_VARIANTS)
        say(variant)
        time.sleep(0.2)
        
        say("Tutti i sistemi operativi, Sir. Come posso assisterla?")
        self.intro_shown = True
    
    def run(self):
        """Main loop"""
        self.intro_sequence()
        
        while True:
            try:
                # Input: testo O voce
                mode = input("\nTony> ").strip()
                
                if not mode:
                    continue
                
                # EXIT COMMANDS
                if any(w in mode.lower() for w in ["exit", "quit", "ciao", "arrivederci"]):
                    say(random.choice(FAREWELLS))
                    break
                
                # VOICE INPUT (se l'utente digita "voce")
                if mode.lower() == "voce":
                    try:
                        from jarvis_voice_input import listen_and_transcribe
                        print("\n[JARVIS] Ascoltando Sir...")
                        user_input = listen_and_transcribe()
                        print(f"[Riconosciuto: {user_input}]\n")
                    except Exception as e:
                        say(f"Errore nel riconoscimento")
                        continue
                else:
                    user_input = mode
                
                # PROCESS INPUT (Tool Use + Conversazione + Memoria)
                response = process_input(user_input)
                
                # SAY (non print, solo say che stampa internamente)
                say(response)
                
                # SALVA IN MEMORIA
                add_to_memory(user_input, response)
                
                # Mantieni history locale
                self.memory.append({
                    "user": user_input,
                    "response": response,
                    "timestamp": time.time()
                })
                
                if len(self.memory) > 20:
                    self.memory.pop(0)
            
            except KeyboardInterrupt:
                say("Sistemi in standby. Goodbye Sir.")
                break
            except Exception as e:
                print(f"\n[ERROR] {e}")
                say("Si è verificato un errore Sir. Riprova.")

if __name__ == "__main__":
    agent = JarvisAgent()
    agent.run()
