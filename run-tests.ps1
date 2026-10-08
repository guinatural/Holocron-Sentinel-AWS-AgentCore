# Run all tests for Holocron Sentinel V2
Write-Host "Running Holocron Sentinel V2 Tests" -ForegroundColor Cyan

# Check if pytest is installed
if (-not (Get-Command pytest -ErrorAction SilentlyContinue)) {
    Write-Host "Installing pytest..." -ForegroundColor Yellow
    pip install pytest pytest-asyncio
}

# Run all tests with coverage
Write-Host "Running unit tests..." -ForegroundColor Cyan
pytest tests/unit/ -v --cov=app --cov-report=term-missing --cov-report=html

# Run integration tests
Write-Host "Running integration tests..." -ForegroundColor Cyan
pytest tests/integration/ -v

# Generate coverage report
Write-Host "Coverage report generated in htmlcov/index.html" -ForegroundColor Green
