# run-tests.ps1 – Executar testes unitários
$projRoot = "C:\Users\barre\AWS-reStart-Compliance-Portfolio\01 - PROJETOS\Holocron"
Set-Location $projRoot
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    & ".\.venv\Scripts\Activate.ps1"
}
Write-Host "Executando testes unitários..."
python -m unittest discover -s tests
Write-Host "✅ Testes concluídos"
