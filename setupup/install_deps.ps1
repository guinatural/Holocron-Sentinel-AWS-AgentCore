# Install Python dependencies for Holocron project
# Activate virtual env if needed
if (!(Test-Path ".venv")) {
    Write-Host "Virtual env not found. Creating..."
    python -m venv .venv
}
& .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Write-Host "✅ Dependencies installed"
