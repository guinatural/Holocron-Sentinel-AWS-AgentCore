"""Offline tests for Bedrock invocation contracts."""

import io
import json
from unittest.mock import Mock

from app.aws.bedrock import BedrockClient


def test_invoke_for_use_case_calls_bedrock_and_returns_text(monkeypatch):
    response_body = io.BytesIO(
        json.dumps(
            {
                "content": [{"type": "text", "text": "Análise concluída."}],
                "usage": {"input_tokens": 12, "output_tokens": 8},
            }
        ).encode()
    )
    runtime_client = Mock(invoke_model=Mock(return_value={"body": response_body}))
    monkeypatch.setattr(
        "app.aws.bedrock.boto3.client", Mock(return_value=runtime_client)
    )

    bedrock = BedrockClient(region_name="us-east-1")
    result = bedrock.invoke_for_use_case(
        prompt="Analise as falhas.",
        use_case="detailed_analysis",
        system_prompt="Você é um auditor.",
    )

    assert result == "Análise concluída."
    runtime_client.invoke_model.assert_called_once()
    call = runtime_client.invoke_model.call_args.kwargs
    assert call["modelId"] == bedrock.MODELS["sonnet"].model_id
    payload = json.loads(call["body"])
    assert payload["messages"] == [
        {"role": "system", "content": "Você é um auditor."},
        {"role": "user", "content": "Analise as falhas."},
    ]
    assert payload["max_tokens"] == 4096
