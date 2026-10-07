# generate-mcp-wrappers.ps1 – Gerar wrappers MCP a partir de funções Lambda
# Este script cria, dentro da pasta mcp, um arquivo <lambda>.py para cada nome listado.
# Cada wrapper contém:
#   - import boto3
#   - função invoke_<lambda>(payload) que chama a Lambda via boto3
#   - anonimização LGPD (remove campo 'ssn' se existir)

$projRoot = "C:\Users\barre\AWS-reStart-Compliance-Portfolio\01 - PROJETOS\Holocron"
Set-Location $projRoot

# Garantir que a pasta mcp exista
$mcpDir = Join-Path $projRoot "mcp"
if (-not (Test-Path $mcpDir)) {
    New-Item -ItemType Directory -Path $mcpDir | Out-Null
    Write-Host "✅ Criada pasta mcp"
}

# Lista de nomes de Lambdas – ajuste conforme necessário
$lambdaNames = @(
    "process_user_data",
    "audit_event",
    "generate_report"
)

foreach ($name in $lambdaNames) {
    $filePath = Join-Path $mcpDir "${name}.py"
    $content = @"
import boto3
import json

lambda_client = boto3.client('lambda')

def invoke_${name}(payload: dict) -> dict:
    """Invoke a AWS Lambda named '$name' via MCP wrapper.
    LGPD compliance: removes 'ssn' from the response if present.
    """
    response = lambda_client.invoke(
        FunctionName='$name',
        Payload=json.dumps(payload).encode()
    )
    result = json.loads(response['Payload'].read())
    # Anonimização LGPD – remover campo sensível
    if isinstance(result, dict):
        result.pop('ssn', None)
    return result
"@
    Set-Content -Path $filePath -Value $content -Encoding UTF8
    Write-Host "✅ Wrapper criado: $filePath"
}
