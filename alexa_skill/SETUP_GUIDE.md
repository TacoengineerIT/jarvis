# Alexa Skill Setup per JARVIS

## 1. Crea la Skill

1. Vai su https://developer.amazon.com/alexa/console/ask
2. **Create Skill**
3. Nome: `JARVIS Assistant`
4. Lingua: **Italian (IT)**
5. Tipo: **Custom**
6. Hosting: **Provision your own** (non Lambda)
7. Template: **Start from Scratch**

## 2. Interaction Model

1. Nel menu a sinistra clicca **JSON Editor**
2. Cancella tutto e incolla il contenuto di `interactionModel.json`
3. Clicca **Save Model**
4. Clicca **Build Model** (aspetta 30-60 secondi)

## 3. Endpoint

1. Menu sinistra → **Endpoint**
2. Seleziona **HTTPS**
3. Default Region: inserisci il tuo URL ngrok, es:
   ```
   https://XXXX-XX-XX-XX-XX.ngrok-free.app/alexa
   ```
   IMPORTANTE: aggiungi `/alexa` alla fine!
4. SSL Certificate: seleziona **My development endpoint is a sub-domain of a domain that has a wildcard certificate from a certificate authority**
5. **Save Endpoints**

## 4. Avvia il server locale

Terminale 1 — Flask:
```bash
cd C:\Users\A1600apulia\Desktop\jarvis_scuola
.\venv\Scripts\activate
python alexa_server.py
```

Terminale 2 — ngrok:
```bash
ngrok http 5000
```
Copia l'URL HTTPS che appare (es. `https://abcd-1234.ngrok-free.app`)
e incollalo nell'endpoint della Skill con `/alexa` alla fine.

## 5. Testa

1. Nella Alexa Console vai su **Test**
2. Abilita il test su **Development**
3. Scrivi o dì: `apri jarvis`
4. Poi: `chiedi come stai` oppure `spiegami la fotosintesi`

## Comandi vocali di esempio

| Dici ad Alexa | Intent |
|---|---|
| "Alexa, apri jarvis" | Apre la skill |
| "chiedi che ore sono" | AssistenzaJarvis |
| "stato del sistema" | StatoSistemaIntent |
| "situazione affitto" | LifeManagementIntent |
| "sono stanco" | EmotionalSupportIntent |
| "spiegami le reti neurali" | StudySessionIntent |

## Troubleshooting

- **Alexa dice "c'è stato un problema"**: controlla che Flask + ngrok siano attivi e che l'URL endpoint sia corretto con `/alexa`
- **Nessun log nel terminale Flask**: ngrok non sta raggiungendo il server. Verifica URL e porta
- **Timeout**: Ollama potrebbe essere lento. Controlla che sia attivo: `ollama list`
- **ngrok URL cambia**: ogni volta che riavvii ngrok l'URL cambia. Aggiornalo nella Alexa Console. Per URL fisso serve ngrok a pagamento oppure usa un dominio custom.
