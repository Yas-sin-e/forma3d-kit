# Rôle : prépare l'environnement local, vérifie les tests, démarre FastAPI et ouvre Edge.
# Exécution : lancer depuis la racine du dépôt avec `./scripts/dev.ps1`.
param(
    [int]$Port = 8001
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$backendRoot = Join-Path $projectRoot "backend"
$venvRoot = Join-Path $backendRoot ".venv"
$pythonPath = Join-Path $venvRoot "Scripts\python.exe"
$requirementsPath = Join-Path $backendRoot "requirements.txt"
$baseUrl = "http://127.0.0.1:$Port"

if (-not (Test-Path -LiteralPath $pythonPath)) {
    Write-Host "Création de l'environnement virtuel backend/.venv..."
    python -m venv $venvRoot
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $pythonPath)) {
        throw "La création du venv a échoué. Vérifiez que Python est installé et accessible."
    }
}

& $pythonPath -c "import fastapi, pytest, uvicorn" *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installation des dépendances du projet dans backend/.venv..."
    & $pythonPath -m pip install -r $requirementsPath
    if ($LASTEXITCODE -ne 0) {
        throw "L'installation des dépendances a échoué. Consultez le message pip ci-dessus."
    }
}

Write-Host "Exécution de la suite pytest (environnement isolé de backend/.env)..."
# Les tests ne doivent pas dépendre du .env réel : on désactive python-dotenv et on vide
# HF_SPACE_ID pour pytest uniquement, puis on restaure les valeurs avant de démarrer Uvicorn.
$savedDotenvDisabled = $env:PYTHON_DOTENV_DISABLED
$savedSpaceId = $env:HF_SPACE_ID
$env:PYTHON_DOTENV_DISABLED = "true"
$env:HF_SPACE_ID = ""
Push-Location $backendRoot
try {
    & $pythonPath -m pytest -q
    if ($LASTEXITCODE -ne 0) {
        throw "Les tests ont échoué ; le serveur n'a pas été démarré."
    }
} finally {
    Pop-Location
    $env:PYTHON_DOTENV_DISABLED = $savedDotenvDisabled
    $env:HF_SPACE_ID = $savedSpaceId
}

$alreadyRunning = $false
try {
    $health = Invoke-RestMethod -Uri "$baseUrl/health" -TimeoutSec 2
    $alreadyRunning = $health.status -eq "ok"
} catch {
    $alreadyRunning = $false
}

if (-not $alreadyRunning) {
    $stdoutPath = Join-Path $backendRoot ".dev-server-output.log"
    $stderrPath = Join-Path $backendRoot ".dev-server-error.log"
    $server = Start-Process `
        -FilePath $pythonPath `
        -ArgumentList @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "$Port") `
        -WorkingDirectory $backendRoot `
        -WindowStyle Hidden `
        -RedirectStandardOutput $stdoutPath `
        -RedirectStandardError $stderrPath `
        -PassThru

    $ready = $false
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        if ($server.HasExited) {
            throw "Uvicorn s'est arrêté. Consultez backend/.dev-server-error.log."
        }
        try {
            $health = Invoke-RestMethod -Uri "$baseUrl/health" -TimeoutSec 2
            if ($health.status -eq "ok") {
                $ready = $true
                break
            }
        } catch {
            Start-Sleep -Seconds 1
        }
    }
    if (-not $ready) {
        throw "Uvicorn n'a pas répondu à /health dans les 30 secondes. Consultez ses journaux locaux."
    }
}

Write-Host "API prête : $baseUrl/health"
Write-Host "Le statut du fournisseur est visible dans l'interface et sur $baseUrl/health/provider."
try {
    Start-Process -FilePath "msedge.exe" -ArgumentList "$baseUrl/"
} catch {
    Start-Process -FilePath "$baseUrl/"
}
