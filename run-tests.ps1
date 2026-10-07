# run-tests.ps1 – Executar testes unitários
# Este script assume que o .venv já foi criado.
$projRoot = "C:\Users\barre\AWS-reStart-Compliance-Portfolio\01 - PROJETOS\Holocron"
Set-Location $projRoot

# Ativa virtual env, se ainda não estiver ativo
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    & ".\.venv\Scripts\Activate.ps1"
}

Write-Host "Executando testes unitários..."
python -m unittest discover -s tests
Write-Host "✅ Testes concluídos"
