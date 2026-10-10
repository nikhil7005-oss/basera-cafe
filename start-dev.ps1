$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPath = Join-Path $root ".venv"

if (-not (Test-Path $venvPath)) {
    Write-Host "Creating Python virtual environment..."
    python -m venv $venvPath
}

$pythonExe = Join-Path $venvPath "Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = (Get-Command python -ErrorAction Stop).Source
}

Write-Host "Installing backend dependencies..."
& $pythonExe -m pip install --upgrade pip
& $pythonExe -m pip install -r (Join-Path $root "backend\requirements.txt")

Write-Host "Starting backend server..."
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$root'; & '$pythonExe' -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload"
) | Out-Null

Write-Host "Starting frontend server..."
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$root'; & '$pythonExe' -m http.server 8080 --directory '$root/frontend'"
) | Out-Null

Start-Sleep -Seconds 1
Start-Process "http://127.0.0.1:8080"

Write-Host ""
Write-Host "App is running."
Write-Host "Frontend: http://127.0.0.1:8080"
Write-Host "Backend API: http://127.0.0.1:8000"
Write-Host "Swagger Docs: http://127.0.0.1:8000/docs"
