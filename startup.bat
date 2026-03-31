@echo off
REM ====================================================================
REM JARVIS Startup Script for Windows
REM Avvia Ollama + JARVIS + Dashboard automaticamente
REM ====================================================================

setlocal enabledelayedexpansion

REM ====================================================================
REM VARIABILI
REM ====================================================================
set JARVIS_DIR=C:\Users\mabat\Desktop\Jarvis
set PYTHON_PATH=python
set OLLAMA_PORT=11434

REM ====================================================================
REM CONTROLLA SE JARVIS_DIR ESISTE
REM ====================================================================
if not exist "%JARVIS_DIR%" (
    echo ERRORE: JARVIS directory non trovata: %JARVIS_DIR%
    echo Modifica JARVIS_DIR nel file startup.bat
    pause
    exit /b 1
)

cd /d "%JARVIS_DIR%" || (
    echo ERRORE: Non riesco a navigare in %JARVIS_DIR%
    pause
    exit /b 1
)

REM ====================================================================
REM BANNER
REM ====================================================================
cls
echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║          JARVIS - Startup Sequence Initiated                   ║
echo ║                                                                ║
echo ║  "All systems coming online, Sir."                             ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

REM ====================================================================
REM CONTROLLA PYTHON
REM ====================================================================
echo [1/4] Verifying Python installation...
%PYTHON_PATH% --version >nul 2>&1
if errorlevel 1 (
    echo ERRORE: Python non trovato
    echo Installa Python 3.11+ da https://python.org
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('%PYTHON_PATH% --version') do set PY_VERSION=%%i
echo [OK] Python %PY_VERSION%

REM ====================================================================
REM CONTROLLA OLLAMA
REM ====================================================================
echo [2/4] Checking Ollama service...
timeout /t 2 /nobreak >nul

REM Prova a fare una richiesta a Ollama
curl -s http://localhost:%OLLAMA_PORT%/api/tags >nul 2>&1
if errorlevel 1 (
    echo [WARN] Ollama non risponde su localhost:%OLLAMA_PORT%
    echo.
    echo Avvio manuale di Ollama in una nuova finestra...
    echo.
    
    REM Controlla se ollama.exe esiste
    if exist "C:\Program Files\Ollama\ollama.exe" (
        echo Launching Ollama...
        start "" "C:\Program Files\Ollama\ollama.exe" serve
        echo.
        echo [*] Ollama avviato. Attendo 5 secondi...
        timeout /t 5 /nobreak >nul
    ) else (
        echo [WARN] Ollama non trovato in Program Files
        echo Download: https://ollama.ai
        echo.
    )
) else (
    echo [OK] Ollama is online
)

REM ====================================================================
REM INSTALLA DIPENDENZE (SE NECESSARIO)
REM ====================================================================
echo [3/4] Checking Python dependencies...
if not exist "venv" (
    echo Creating virtual environment...
    %PYTHON_PATH% -m venv venv
    call venv\Scripts\activate.bat
) else (
    call venv\Scripts\activate.bat
)

REM Installa/upgrade requirements
pip install -q -r requirements.txt
if errorlevel 1 (
    echo [WARN] Alcuni pacchetti potrebbero non essere installati
)

echo [OK] Dependencies checked

REM ====================================================================
REM AVVIA JARVIS AGENT
REM ====================================================================
echo [4/4] Starting JARVIS Agent...
echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║                                                                ║
echo ║              Launching jarvis_agent_refactored.py              ║
echo ║                                                                ║
echo ║           Waiting for AC/DC "Back in Black" intro...           ║
echo ║                                                                ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

%PYTHON_PATH% jarvis_agent_refactored.py

REM ====================================================================
REM CLEANUP
REM ====================================================================
echo.
echo JARVIS shutdown. Goodbye Sir.
pause
