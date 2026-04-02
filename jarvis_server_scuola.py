#!/usr/bin/env python3
"""
JARVIS Server (Scuola) - Brain with Ollama + ChromaDB
Runs on school PC (192.168.1.76), receives commands via SSH from home PC
Uses: ollama (qwen2.5:3b), chromadb (RAG with university PDFs)
"""

import sys
import os
import json
import random
from pathlib import Path
from datetime import datetime

# Ollama integration
try:
    import ollama
except ImportError:
    print("ERROR: ollama not installed. Run: pip install ollama")
    sys.exit(1)

# ChromaDB for RAG
try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    print("WARNING: chromadb not installed. RAG disabled.")
    chromadb = None

# Configuration
OLLAMA_MODEL = "llama3.1:8b"  # Changed from qwen2.5:3b to match actual install
OLLAMA_HOST = "http://localhost:11434"
CHROMADB_PATH = "C:/Users/A1600apulia/Desktop/jarvis_scuola/chromadb"

# System prompt for JARVIS personality
SYSTEM_PROMPT = """Sei JARVIS, un assistente AI personale ispirato da Iron Man. 
Rispondi sempre in italiano. Mantieni un tono formale e leggermente ironico (alla inglese).
Risposte brevi e dirette (max 3 righe).
Se chiesto di informazioni accademiche, usa il contesto fornito dal database RAG.
Firma le risposte con "— JARVIS" """

class JARVISServerScuola:
    def __init__(self):
        self.ollama_available = self._check_ollama()
        self.chromadb_client = None
        self.context = ""
        
        if chromadb and os.path.exists(CHROMADB_PATH):
            try:
                self.chromadb_client = chromadb.PersistentClient(path=CHROMADB_PATH)
                print(f"[ChromaDB] Loaded from {CHROMADB_PATH}")
            except Exception as e:
                print(f"[ChromaDB WARNING] {e}")
    
    def _check_ollama(self):
        """Verify Ollama is running and model is available"""
        try:
            response = ollama.list()
            models = [m.model for m in response.models]
            if OLLAMA_MODEL in models or any(OLLAMA_MODEL.split(':')[0] in m for m in models):
                print(f"[Ollama] Model {OLLAMA_MODEL} available")
                return True
            else:
                print(f"[Ollama WARNING] Model {OLLAMA_MODEL} not found. Available: {models}")
                return False
        except Exception as e:
            print(f"[Ollama ERROR] Not running or unreachable: {e}")
            return False
    
    def search_rag(self, query):
        """Search ChromaDB for relevant university PDF context"""
        if not self.chromadb_client:
            return ""
        
        try:
            collections = self.chromadb_client.list_collections()
            if not collections:
                return ""
            
            # Query first collection (assumes single "university_docs" collection)
            collection = self.chromadb_client.get_collection(name=collections[0].name)
            results = collection.query(query_texts=[query], n_results=3)
            
            if results and results['documents']:
                context = "\n".join(results['documents'][0])
                return context[:500]  # Limit context to 500 chars
        except Exception as e:
            print(f"[RAG ERROR] {e}")
        
        return ""
    
    def process_input(self, user_input):
        """Process user input and generate response via Ollama"""
        if not user_input.strip():
            return "Scusate, Sir. Non ho capito."
        
        # Search RAG if available
        self.context = self.search_rag(user_input)
        
        # Build prompt
        if self.context:
            full_prompt = f"{SYSTEM_PROMPT}\n\n[CONTESTO DA RAG]\n{self.context}\n\n[DOMANDA]\n{user_input}"
        else:
            full_prompt = f"{SYSTEM_PROMPT}\n\n[DOMANDA]\n{user_input}"
        
        if not self.ollama_available:
            return "Ollama non è disponibile, Sir. Controllare il servizio."
        
        try:
            response = ollama.generate(
                model=OLLAMA_MODEL,
                prompt=full_prompt,
                stream=False,
                timeout=60
            )
            
            answer = response.response.strip()
            
            # Fallback if response is empty
            if not answer:
                answer = random.choice([
                    "Non sono in grado di rispondere a questa domanda, Sir.",
                    "La mia risposta rimane indecifrabile, Sir.",
                    "Potete formulare diversamente?",
                ])
            
            return answer
        except Exception as e:
            print(f"[Ollama PROCESS ERROR] {e}")
            return f"Errore nel processamento: {str(e)}"
    
    def run(self):
        """Main server loop (reads from stdin for SSH piped input)"""
        print(f"[SERVER] JARVIS Server Started at {datetime.now()}")
        print(f"[SERVER] Ollama: {'Available' if self.ollama_available else 'NOT AVAILABLE'}")
        print(f"[SERVER] RAG: {'Loaded' if self.chromadb_client else 'Disabled'}")
        
        # Read input from stdin (piped from SSH client)
        try:
            user_input = sys.stdin.read().strip()
            if user_input:
                response = self.process_input(user_input)
                print(response)  # Output to stdout (captured by SSH client)
            else:
                print("Nessun input ricevuto, Sir.")
        except Exception as e:
            print(f"ERROR: {e}")
            sys.exit(1)

if __name__ == "__main__":
    server = JARVISServerScuola()
    server.run()
