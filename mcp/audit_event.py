import boto3
import json

lambda_client = boto3.client('lambda')

def invoke_audit_event(payload: dict) -> dict:
    \"\"\"Invoke a AWS Lambda named 'audit_event' via MCP wrapper.
    LGPD compliance: removes 'ssn' from the response if present.
    \"\"\"
    response = lambda_client.invoke(
        FunctionName='audit_event',
        Payload=json.dumps(payload).encode()
    )
    result = json.loads(response['Payload'].read())
    # LGPD – anonimização de campo sensível
    if isinstance(result, dict):
        result.pop('ssn', None)
    return result
