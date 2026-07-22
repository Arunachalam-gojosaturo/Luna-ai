# ==============================================================================
#  Luna AI (Luna OS X) — Windows 11 Automated PowerShell Installer
#  One-Line PowerShell Command:
#  iwr -useb https://raw.githubusercontent.com/Arunachalam-gojosaturo/Luna-ai/main/win11/install.ps1 | iex
# ==============================================================================

$ErrorActionPreference = "Stop"

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host " 🌙 Luna AI — Windows 11 Automated Installer" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

# 1. Check Python & Node.js
Write-Host "▸ Checking system prerequisites..." -ForegroundColor Yellow

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "⚠️ Python 3 is not installed. Installing via winget..." -ForegroundColor Yellow
    winget install --id Python.Python.3.11 -e --accept-source-agreements --accept-package-agreements
}

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "⚠️ Node.js is not installed. Installing via winget..." -ForegroundColor Yellow
    winget install --id OpenJS.NodeJS -e --accept-source-agreements --accept-package-agreements
}

$InstallDir = "$env:LOCALAPPDATA\LunaAI"
$TargetDir = $PSScriptRoot

if (-not (Test-Path "$TargetDir\luna_desktop.py")) {
    Write-Host "▸ Downloading Luna AI Windows source to $InstallDir..." -ForegroundColor Yellow
    if (Get-Command git -ErrorAction SilentlyContinue) {
        if (Test-Path "$InstallDir\.git") {
            Set-Location $InstallDir
            git pull origin main
        } else {
            Remove-Item -Recurse -Force $InstallDir -ErrorAction SilentlyContinue
            git clone https://github.com/Arunachalam-gojosaturo/Luna-ai.git $InstallDir
            Set-Location "$InstallDir\win11"
        }
    } else {
        Write-Host "❌ Git is required to clone the repository. Please install Git via winget install Git.Git" -ForegroundColor Red
        Exit 1
    }
    $TargetDir = "$InstallDir\win11"
}

Set-Location $TargetDir

# 2. Virtual Environment Setup
Write-Host "▸ Setting up Python virtual environment..." -ForegroundColor Yellow
if (-not (Test-Path "venv")) {
    python -m venv venv
}

& ".\venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
if (Test-Path "requirements.txt") {
    & ".\venv\Scripts\pip.exe" install -r requirements.txt --quiet
}
& ".\venv\Scripts\pip.exe" install PyQt6 PyQt6-WebEngine pywin32 pycaw --quiet

# 3. Node Dependencies & Asset Build
Write-Host "▸ Installing Node.js dependencies & building frontend..." -ForegroundColor Yellow
npm install --silent
npm run build

# 4. Create Windows Desktop Shortcut & Batch Wrappers
Write-Host "▸ Creating Windows Application Shortcuts..." -ForegroundColor Yellow

$DesktopPath = [System.IO.Path]::Combine([System.Environment]::GetFolderPath("Desktop"), "Luna AI.lnk")
$StartMenuPath = [System.IO.Path]::Combine([System.Environment]::GetFolderPath("StartMenu"), "Programs", "Luna AI.lnk")

$WScriptShell = New-Object -ComObject WScript.Shell

foreach ($LnkPath in @($DesktopPath, $StartMenuPath)) {
    $Shortcut = $WScriptShell.CreateShortcut($LnkPath)
    $Shortcut.TargetPath = "$TargetDir\venv\Scripts\pythonw.exe"
    $Shortcut.Arguments = """$TargetDir\luna_desktop.py"""
    $Shortcut.WorkingDirectory = $TargetDir
    if (Test-Path "$TargetDir\public\deskopticon.png") {
        $Shortcut.IconLocation = "$TargetDir\public\deskopticon.png"
    }
    $Shortcut.Save()
}

# Create Batch Wrappers in %LOCALAPPDATA%\Microsoft\WindowsApps
$WinApps = "$env:LOCALAPPDATA\Microsoft\WindowsApps"
if (Test-Path $WinApps) {
    Set-Content -Path "$WinApps\luna-ai.bat" -Value "@echo off`r`ncd /d ""$TargetDir""`r`n""$TargetDir\venv\Scripts\python.exe"" luna_desktop.py %*"
    Set-Content -Path "$WinApps\luna.bat" -Value "@echo off`r`ncd /d ""$TargetDir""`r`n""$TargetDir\venv\Scripts\python.exe"" luna_desktop.py %*"
    Set-Content -Path "$WinApps\luna-cli.bat" -Value "@echo off`r`ncd /d ""$TargetDir""`r`n""$TargetDir\venv\Scripts\python.exe"" luna_cli_enhanced.py %*"
}

Write-Host "======================================================================" -ForegroundColor Green
Write-Host " ✨ SUCCESS! Luna AI installed successfully on Windows 11!" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Green
Write-Host ""
Write-Host " 🚀 How to Launch Luna AI on Windows 11:" -ForegroundColor White
Write-Host "   1. Double-click 'Luna AI' on your Desktop or Start Menu" -ForegroundColor White
Write-Host "   2. In CMD / PowerShell, type 'luna-ai' or 'luna'" -ForegroundColor White
Write-Host "   3. In CLI mode, type 'luna-cli'" -ForegroundColor White
Write-Host "======================================================================" -ForegroundColor Green
