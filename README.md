# J.A.R.V.I.S. — Just A Rather Very Intelligent System

> *"L'intelligenza artificiale non è il futuro. È il presente che chi sa usarla sta già vivendo."*

## La Sfida

A 20 anni, 150km da casa, studente ITS di IA & Data Science a Bari con:
- Un PC mid-range (i7-1370P, 32GB RAM)
- WiFi residenziale (non fibra)
- 110€ mensili di affitto da coprire
- Necessità di concentrarsi su 3 cose: coding, studio, sopravvivenza economica

**Il problema:** La vita quotidiana è un context switch costante. Ogni interruzione costa CPU biologica.

**La soluzione:** Non inventare nuova tecnologia. **Combinare gli strumenti che la ricerca ha già messo a disposizione.**

---

## Cosa è J.A.R.V.I.S. (In 90 secondi)

Un ecosistema locale che:

1. **Ascolta** via Alexa Echo Pop (voce naturale, no tastiera)
2. **Ragiona** localmente con Ollama (llama3.1:8b) + Claude API (Haiku) quando serve
3. **Agisce** sul PC: apre file, crea ricette, traccia finanze
4. **Ricorda** cosa hai studiato (RAG su PDF universitari)
5. **Preoccupa anticipatamente** — sa che mancano 34€ all'affitto

Zero cloud proprietario. Zero subscription obbligatorie. **Tutto quello che puoi controllare, controluri tu.**

---

## Architettura
```
┌─────────────────────────────────────────────┐
│   VOICE INPUT                               │
│   Echo Pop (Alexa Skill)                    │
└──────────────┬────────────────────────────┘
               │ (ngrok HTTPS tunnel)
               ↓
┌─────────────────────────────────────────────┐
│   BACKEND LAYER                             │
│   Flask Server (localhost:5000)             │
│   - Intent routing                          │
│   - State management                        │
│   - Response building                       │
└──────────────┬────────────────────────────┘
               │
       ┌───────┼────────┐
       ↓       ↓        ↓
   OLLAMA  JARVIS   SYSTEM
   (Local) BRAIN    TOOLS
   LLM    (Logic)   (PyAutoGUI)
               │
               ↓
   ┌───────────────────────────┐
   │ PERSISTENT MEMORY         │
   │ - ChromaDB (Vector DB)    │
   │ - finances.json           │
   │ - memory.json             │
   └───────────────────────────┘
```

---

## Filosofia: "Intelligenza come Force Multiplier"

Questo NON è un chatbot. È un **acceleratore di efficienza personale**.

### 3 Principi Chiave

**1. Local-First, Cloud-Fallback**
- 95% dei processi girano localmente (privati, veloci, offline-capable)
- Claude Haiku entra solo quando Ollama non basta (reasoning complesso)
- Costo runtime: ~€0-5/mese (solo fallback)

**2. Context Over Perfection**
- JARVIS non è "intelligente" in senso astratto
- È *situationally aware*: sa che stai studiando IA alle 2 di notte, conosce il tuo cash flow, ricorda i tuoi preferiti
- Usa memoria di breve termine (ultimi 20 scambi) per conversazione coerente

**3. Tooling Over Building**
- Non ho scritto un LLM. Ho imparato a *stackare* Claude + Ollama + ChromaDB + Alexa ASK
- Il valore sta nell'integrazione, non nell'invenzione
- **Chiunque con un PC normale può farlo.**

---

## Cosa Puoi Fare (Real Examples)

### Voice Commands Reali
```
Tu > "JARVIS situazione"
JARVIS > "CPU al 45%, RAM al 62%. Affitto: mancano 34€. 
         Il tuo ultimo studio era su FastAPI. Vuoi riprendere?"

Tu > "che si mangia"
JARVIS > "Lenticchie e riso Sir. 2€. Ricetta salvata sul Desktop. 
         Proteico, economico, vi tiene concentrati."

Tu > "interrogami su IA"
JARVIS > [risposta Ollama personalizzata su quello che hai studiato]

Tu > "sono stanco"
JARVIS > "Lo so Sir. Back in Black in avvio. Anche il mio circuito è un po' teso 
         con questi 110€ pendenti. Riprendiamo tra 10 minuti?"
```

### Come è Stato Costruito (Real Process)

**Giorno 1-2:** Proof of concept grezzo  
**Giorno 3:** Problemi di BOM encoding, percorsi Windows, gestione errori  
**Giorno 4:** Integrazione Ollama, scoperta che llama3.1:8b era sufficiente  
**Giorno 5:** Voice input (Whisper), problemi FFmpeg, soluzione alternativa con scipy  
**Giorno 6:** Alexa skill setup, debugging ngrok, routing intelligente  
**Giorno 7:** Memory system, context awareness, personality layer  
**Giorno 8:** Polish & documentazione  

**Lezione:** Non è partito "perfetto". È partito *vero*, poi è stato iterato fino a funzionare.

---

## Tech Stack (Scelte Consapevoli)

| Layer | Tool | Perché |
|-------|------|--------|
| **LLM Local** | Ollama + llama3.1:8b | Gratis, offline, <10s latency su i7 |
| **LLM Cloud** | Claude Haiku 4.5 | Fallback intelligente quando serve reasoning |
| **Voice Input** | Whisper (OpenAI) | Gratis, open source, supporta italiano |
| **Voice Output** | Edge-TTS Neural | Gratis, non richiede account, voce naturale |
| **Memory** | ChromaDB | Vector DB locale, zero dipendenze cloud |
| **Code Search** | Sentence Transformers | Semantic search su università PDFs |
| **Voice Interface** | Alexa ASK + Flask | Skill personalizzate, latency basso |
| **Tunneling** | ngrok free | Semplice, affidabile, autorizza dinamicamente |
| **PC Automation** | PyAutoGUI | Lightweight, niente driver speciali |

---

## Setup: Come Replicarlo

### Hardware Minimo
- PC Windows/Mac/Linux (8GB RAM consigliato)
- WiFi qualunque (anche residenziale)
- Echo Pop (~€99 una volta)

### Software (Tutto Gratuito)
```bash
# Python 3.11+
pip install -r requirements.txt

# Ollama (local LLM)
# https://ollama.ai

# ngrok (free tier)
# https://ngrok.com
```

### Tempo Totale Setup
**~3 ore** (scarica modelli, configura Alexa Developer Console, testa)

### Costi Ricorrenti
- **€0/mese** se usi solo Ollama
- **€2-5/mese** se attivi fallback Claude Haiku

---

## Cosa Puoi Imparare da Questo

**Per Developer:**
- Come stackare multiple AI models (local + cloud)
- Voice interface design
- Semantic search con vector DBs
- Alexa Skill development
- Windows automation via Python

**Per Problem Solvers:**
- Thought process: ridefinire il problema (non "chatbot", ma "force multiplier")
- Constraint-driven design (€110, WiFi normale, PC mid-range)
- Tooling > building: cosa usare vs. cosa fare da zero

**Per Studenti:**
- Come liberare cognitively load dalle cose banali
- Importanza del contesto (situational awareness)
- Tool stacking come superpotere

---

## Limitazioni Consapevoli

- ❌ Non legge schermo autonomamente (planned: Claude Computer Use v2)
- ❌ Ollama 8B non batte Sonnet nel reasoning (by design: fallback a Claude)
- ❌ Richiede ngrok per Alexa remote (ma locale funziona in LAN)
- ❌ TTS dipende da Microsoft Edge (non critical, ha fallback text)

Tutte sono trade-off consapevoli tra semplicità, costo e performance.

---

## Roadmap (Prossimi 90 giorni)

- [ ] **Computer Use**: Claude Sonnet analizza errori dallo schermo
- [ ] **Intervista Mock**: Simula colloqui tecnici via Alexa
- [ ] **GitHub Autopilot**: Suggeri commits basato su codice scritto
- [ ] **Finanza Pro**: Tracking spese, raccomandazioni budget, simulazioni
- [ ] **Publish Open**: Dockerfile + guida per chiunque voglia replicarlo

---

## Note dell'Autore

Questo non è un "side project" per il portfolio. È **il mio sistema operativo personale**.

Ogni feature è nata da una necessità vera:
- **Financial tracking** = affitto non pagato per ritardo
- **Voice input** = mani occupate, occhi stanchi
- **Semantic search** = 200+ file universitari, impossibile trovare quella formula
- **Emotional support** = a volte serve una voce amica alle 2 di notte

**La scoperta più importante:** Non serve essere un genius dell'IA per costruire sistemi intelligenti. Serve saper **usare gli strumenti che gli altri hanno già creato**.

Se riesco io — student, 20 anni, con WiFi da residenza — chiunque può farlo.

---

## Come Contribuire

Questo è un **sistema living**, non finito.

Se hai suggerimenti:
1. Fork il repo
2. Aggiungi feature / risolvi bug
3. Documenta il tuo processo (non solo il codice)

**In particolare cerco:**
- Ottimizzazioni per latency su hardware base
- Integrazioni custom per altri LLM locali
- Case study da altri student (il tuo problema, la tua soluzione)

---

<div align="center">

**Built with hunger, caffeine, and too many PowerShell windows open at 2 AM.**

*By TacoEngineerIT* 🇮🇹  
*Student @ ITS Apulia Digital Maker, Bari*

> "L'eccellenza non è un'abilità. È la scelta di mangiare il mondo con le proprie mani, ogni singolo giorno."

</div>
