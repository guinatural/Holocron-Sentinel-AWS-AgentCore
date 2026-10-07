# -------------------------------------------------
# setup-holocron.ps1 – Preparar ambiente Holocron
# -------------------------------------------------
# Caminho absoluto da pasta do projeto
$projRoot = "C:\Users\barre\AWS-reStart-Compliance-Portfolio\01 - PROJETOS\Holocron"

# 1️⃣ Verifica workspace existente
Get-ChildItem -Path $projRoot -Filter *.code-workspace -File

# 2️⃣ Cria/atualiza o .code-workspace
$workspaceJson = @'
{
  "folders": [{ "path": "." }],
  "settings": {
    "python.pythonPath": ".venv\\Scripts\\python.exe",
    "python.formatting.provider": "black",
    "editor.tabSize": 4,
    "files.exclude": {
      "**/__pycache__": true,
      "**/.git": true
    },
    "cursor.rulesFile": ".cursorrules"
  },
  "extensions": {
    "recommendations": [
      "ms-python.python",
      "ms-azuretools.vscode-docker",
      "amazonwebservices.aws-toolkit-vscode",
      "github.copilot"
    ]
  }
}
'@
    $workspacePath = Join-Path $projRoot "holocron.code-workspace"
    Set-Content -Path $workspacePath -Value $workspaceJson -Encoding UTF8

# 3️⃣ Virtual env
Set-Location $projRoot
if (-not (Test-Path ".venv")) {
    python -m venv .venv
    Write-Host "✅ Virtual env criado"
} else {
    Write-Host "🔁 .venv já existe"
}
& .\.venv\Scripts\Activate.ps1

# 4️⃣ .cursorrules (cria se faltar)
$cursorrulesPath = Join-Path $projRoot ".cursorrules"
if (-not (Test-Path $cursorrulesPath)) {
    $rules = @"
# .cursorrules – Holocron Sentinel V2
# -------------------------------------------------
# • Projeto: Orquestrador DPO (LGPD) na AWS
# • Não Yapping – respostas curtas
# • Sempre usar logging via CloudWatch
# • Não modificar arquivos de exemplo em amazon‑bedrock‑agentcore‑samples
"@
    Set-Content -Path $cursorrulesPath -Value $rules -Encoding UTF8
    Write-Host "🛠️ .cursorrules criado"
} else {
    Write-Host "✅ .cursorrules já está presente"
}

# 5️⃣ Abre VS Code apontando para o workspace
code $workspacePath

# 6️⃣ Resumo dos artefatos criados
Write-Host "`n--- Resumo dos artefatos ---"
Get-Item $workspacePath | Select-Object Name, Length, LastWriteTime
Get-Item $cursorrulesPath | Select-Object Name, Length, LastWriteTime
