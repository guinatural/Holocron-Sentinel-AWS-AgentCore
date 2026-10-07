import boto3
import json

lambda_client = boto3.client('lambda')

def invoke_process_user_data(payload: dict) -> dict:
    \"\"\"Invoke a AWS Lambda named 'process_user_data' via MCP wrapper.
    LGPD compliance: removes 'ssn' from the response if present.
    \"\"\"
    response = lambda_client.invoke(
        FunctionName='process_user_data',
        Payload=json.dumps(payload).encode()
    )
    result = json.loads(response['Payload'].read())
    # LGPD – anonimização de campo sensível
    if isinstance(result, dict):
        result.pop('ssn', None)
    return result
