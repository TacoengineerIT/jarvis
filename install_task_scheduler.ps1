# =============================================================================
# Install JARVIS as Windows Task Scheduler Job
# =============================================================================
#
# Run as Administrator:
# powershell -ExecutionPolicy Bypass -File install_task_scheduler.ps1
#

param(
    [switch]$Remove = $false
)

$TaskName = "JARVIS"
$JarvisDir = "C:\Users\mabat\Desktop\Jarvis"
$StartupScript = "$JarvisDir\startup.ps1"

# =============================================================================
# FUNZIONI
# =============================================================================

function Write-Title {
    param([string]$Text)
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║ $Text" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
}

function Check-AdminPrivileges {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# =============================================================================
# MAIN
# =============================================================================

Write-Title "JARVIS - Windows Task Scheduler Installation"

# Controlla privilegi admin
if (-not (Check-AdminPrivileges)) {
    Write-Host "ERRORE: Esegui come Amministratore!" -ForegroundColor Red
    Write-Host "Fai click destro su PowerShell → 'Run as administrator'" -ForegroundColor Yellow
    exit 1
}

# ========== REMOVE EXISTING TASK
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Write-Host "Task '$TaskName' esiste già" -ForegroundColor Yellow
    
    if ($Remove) {
        Write-Host "Rimozione task..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "Task rimosso" -ForegroundColor Green
        exit 0
    } else {
        Write-Host "Utilizzo flag -Remove per rimuoverlo" -ForegroundColor Yellow
        Write-Host "Esempio: .\install_task_scheduler.ps1 -Remove" -ForegroundColor Cyan
        exit 0
    }
}

# ========== VERIFICA STARTUP SCRIPT
if (-not (Test-Path $StartupScript)) {
    Write-Host "ERRORE: Script non trovato: $StartupScript" -ForegroundColor Red
    exit 1
}

# ========== CREA TASK
Write-Host "Creazione scheduled task '$TaskName'..." -ForegroundColor Cyan

$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-ExecutionPolicy Bypass -NoProfile -File `"$StartupScript`""

$trigger = New-ScheduledTaskTrigger `
    -AtLogOn `
    -User "$env:USERDOMAIN\$env:USERNAME"

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

$task = New-ScheduledTask `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "JARVIS - Personal AI Assistant. Launches at user logon."

Register-ScheduledTask `
    -TaskName $TaskName `
    -InputObject $task `
    -Force | Out-Null

# ========== VERIFICA CREAZIONE
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Write-Host ""
    Write-Host "✓ Task creato con successo!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Dettagli task:" -ForegroundColor Cyan
    Write-Host "  Nome:        $TaskName" -ForegroundColor Gray
    Write-Host "  Trigger:     At logon (login)" -ForegroundColor Gray
    Write-Host "  Azione:      Avvio $StartupScript" -ForegroundColor Gray
    Write-Host "  Utente:      $env:USERNAME" -ForegroundColor Gray
    Write-Host ""
    Write-Host "JARVIS si avvierà automaticamente al prossimo login!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Per testare subito:" -ForegroundColor Cyan
    Write-Host "  Start-ScheduledTask -TaskName $TaskName" -ForegroundColor White
    Write-Host ""
    Write-Host "Per disabilitare:" -ForegroundColor Cyan
    Write-Host "  .\install_task_scheduler.ps1 -Remove" -ForegroundColor White
} else {
    Write-Host "✗ Errore nella creazione del task" -ForegroundColor Red
    exit 1
}
