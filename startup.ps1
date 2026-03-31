# =============================================================================
# JARVIS Startup Script (PowerShell Advanced Version)
# =============================================================================
# 
# Run as administrator:
# powershell -ExecutionPolicy Bypass -File startup.ps1
#
# Oppure importa nel Task Scheduler di Windows per auto-start
#

param(
    [switch]$InstallScheduledTask = $false,
    [switch]$NoOllama = $false,
    [switch]$DashboardOnly = $false
)

# =============================================================================
# CONFIGURAZIONE
# =============================================================================
$JarvisDir = "C:\Users\mabat\Desktop\Jarvis"
$OllamaPort = 11434
$PythonExe = "python"

# Colori per output
$Colors = @{
    Success = "Green"
    Error = "Red"
    Warning = "Yellow"
    Info = "Cyan"
}

# =============================================================================
# FUNZIONI UTILITY
# =============================================================================

function Write-Status {
    param(
        [string]$Message,
        [string]$Status = "Info"
    )
    
    $color = $Colors[$Status]
    $prefix = switch ($Status) {
        "Success" { "✓" }
        "Error" { "✗" }
        "Warning" { "⚠" }
        "Info" { "[*]" }
    }
    
    Write-Host "$prefix $Message" -ForegroundColor $color
}

function Check-Command {
    param([string]$Name)
    
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    return $null -ne $cmd
}

function Test-OllamaAvailable {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$OllamaPort/api/tags" -TimeoutSec 2 -ErrorAction SilentlyContinue
        return $response.StatusCode -eq 200
    } catch {
        return $false
    }
}

function Start-Ollama {
    Write-Status "Avvio Ollama in background..." "Info"
    
    $ollamaPath = "C:\Program Files\Ollama\ollama.exe"
    if (Test-Path $ollamaPath) {
        & $ollamaPath serve | Out-Null &
        Start-Sleep -Seconds 5
        
        if (Test-OllamaAvailable) {
            Write-Status "Ollama started successfully" "Success"
            return $true
        } else {
            Write-Status "Ollama avviato ma non risponde ancora" "Warning"
            return $false
        }
    } else {
        Write-Status "Ollama non trovato in $ollamaPath" "Error"
        return $false
    }
}

# =============================================================================
# MAIN SCRIPT
# =============================================================================

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║       JARVIS - Startup Sequence (PowerShell)          ║" -ForegroundColor Cyan
Write-Host "║                                                        ║" -ForegroundColor Cyan
Write-Host "║   'All systems coming online, Sir.'                   ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ========== VERIFICA DIRECTORY
Write-Status "Verifying JARVIS directory..." "Info"
if (-not (Test-Path $JarvisDir)) {
    Write-Status "Directory non trovata: $JarvisDir" "Error"
    exit 1
}
Set-Location $JarvisDir
Write-Status "JARVIS directory OK: $JarvisDir" "Success"

# ========== VERIFICA PYTHON
Write-Status "Checking Python..." "Info"
if (-not (Check-Command $PythonExe)) {
    Write-Status "Python non trovato" "Error"
    exit 1
}
$pyVersion = & $PythonExe --version 2>&1
Write-Status "Python OK: $pyVersion" "Success"

# ========== VERIFICA OLLAMA
if (-not $NoOllama) {
    Write-Status "Checking Ollama..." "Info"
    
    if (Test-OllamaAvailable) {
        Write-Status "Ollama is online" "Success"
    } else {
        Write-Status "Ollama non disponibile" "Warning"
        Start-Ollama
    }
}

# ========== VIRTUAL ENVIRONMENT
Write-Status "Setting up Python virtual environment..." "Info"
if (-not (Test-Path "venv")) {
    & $PythonExe -m venv venv
}
& ".\venv\Scripts\Activate.ps1"
Write-Status "Venv activated" "Success"

# ========== INSTALLA DIPENDENZE
Write-Status "Installing dependencies..." "Info"
& pip install -q -r requirements.txt
if ($LASTEXITCODE -eq 0) {
    Write-Status "Dependencies installed" "Success"
} else {
    Write-Status "Some dependencies may have failed" "Warning"
}

# ========== TEST SUITE (OPZIONALE)
Write-Host ""
Write-Status "Running system test suite..." "Info"
& $PythonExe test_jarvis_system.py
Write-Host ""

# ========== AVVIA DASHBOARD O AGENT
Write-Host ""
if ($DashboardOnly) {
    Write-Status "Starting Streamlit Dashboard..." "Info"
    & streamlit run dashboard.py
} else {
    Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║                                                        ║" -ForegroundColor Cyan
    Write-Host "║          Launching jarvis_agent_refactored.py         ║" -ForegroundColor Cyan
    Write-Host "║                                                        ║" -ForegroundColor Cyan
    Write-Host "║     Waiting for 'Back in Black' intro sequence...     ║" -ForegroundColor Cyan
    Write-Host "║                                                        ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    
    & $PythonExe jarvis_agent_refactored.py
}

Write-Host ""
Write-Status "JARVIS shutdown. Goodbye Sir." "Info"
