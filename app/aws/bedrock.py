"""Bedrock client with cost-optimized model selection."""

import json
import boto3
import logging
from typing import Literal, Optional, Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class BedrockModel:
    """Bedrock model configuration."""

    name: str
    model_id: str
    price_per_1m_input: float  # USD
    price_per_1m_output: float  # USD
    max_tokens: int


class BedrockClient:
    """
    Cost-optimized Bedrock client for multi-tenant workloads.

    Automatically selects the most appropriate model based on use case.
    """

    # Model configurations
    MODELS = {
        "haiku": BedrockModel(
            name="Claude 3.5 Haiku",
            model_id="anthropic.claude-3-5-haiku-20241022-v1:0",
            price_per_1m_input=0.25,
            price_per_1m_output=1.25,
            max_tokens=4096,
        ),
        "sonnet": BedrockModel(
            name="Claude 3.5 Sonnet",
            model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
            price_per_1m_input=3.00,
            price_per_1m_output=15.00,
            max_tokens=4096,
        ),
    }

    # Use case mapping
    USE_CASES = {
        "initial_triage": "haiku",
        "detailed_analysis": "sonnet",
        "executive_report": "sonnet",
        "quick_check": "haiku",
        "comprehensive_audit": "sonnet",
    }

    def __init__(self, region_name: str = "us-east-1"):
        """
        Initialize Bedrock client.

        Args:
            region_name: AWS region for Bedrock
        """
        self.client = boto3.client("bedrock-runtime", region_name=region_name)
        self.current_model = "haiku"  # Default to cheapest

    def set_model(self, model_type: Literal["haiku", "sonnet"]) -> None:
        """
        Set the model to use for subsequent calls.

        Args:
            model_type: 'haiku' (fast, cheap) or 'sonnet' (powerful, expensive)
        """
        if model_type not in self.MODELS:
            raise ValueError(f"Unknown model: {model_type}")
        self.current_model = model_type
        logger.info(f"Switched to model: {self.MODELS[model_type].name}")

    def invoke_model(
        self,
        prompt: str,
        model_type: Optional[Literal["haiku", "sonnet"]] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Invoke Bedrock model with cost optimization.

        Args:
            prompt: User prompt
            model_type: Model to use (auto-selects if None)
            max_tokens: Maximum output tokens
            temperature: Model temperature (0.0-1.0)
            system_prompt: Optional system prompt

        Returns:
            Model response text
        """
        if model_type is None:
            model_type = self.current_model

        model = self.MODELS[model_type]
        logger.info(f"Invoking {model.name} for prompt (length: {len(prompt)} chars)")

        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        body = {
            "anthropic_version": "bedrock-2023-05-10",
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        try:
            response = self.client.invoke_model(
                modelId=model.model_id, body=json.dumps(body)
            )

            result = json.loads(response["body"].read())
            content = result["content"][0]["text"]

            # Log token usage (for budget tracking)
            input_tokens = result.get("usage", {}).get("input_tokens", 0)
            output_tokens = result.get("usage", {}).get("output_tokens", 0)

            cost = (input_tokens / 1_000_000) * model.price_per_1m_input + (
                output_tokens / 1_000_000
            ) * model.price_per_1m_output

            logger.info(
                f"Model response: {input_tokens} input + {output_tokens} output tokens "
                f"(${cost:.4f})"
            )

            return content

        except Exception as e:
            logger.error(f"Bedrock invocation failed: {e}")
            raise

    def invoke_for_use_case(self, prompt: str, use_case: str, **kwargs) -> str:
        """
        Invoke model optimized for specific use case.

        Args:
            prompt: User prompt
            use_case: One of 'initial_triage', 'detailed_analysis', etc.
            **kwargs: Additional arguments passed to invoke_model

        Returns:
            Model response
        """
        model_type = self.USE_CASES.get(use_case, "haiku")
        logger.info(f"Use case '{use_case}' -> model '{model_type}'")
        return self.invoke_model(prompt, model_type=model_type, **kwargs)

    def estimate_cost(
        self, input_tokens: int, output_tokens: int, model_type: str = "haiku"
    ) -> float:
        """
        Estimate API cost for token usage.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model_type: Model to use for pricing

        Returns:
            Estimated cost in USD
        """
        model = self.MODELS[model_type]
        return (input_tokens / 1_000_000) * model.price_per_1m_input + (
            output_tokens / 1_000_000
        ) * model.price_per_1m_output

    def get_available_models(self) -> Dict[str, BedrockModel]:
        """Get dictionary of available models."""
        return self.MODELS


# Example usage
if __name__ == "__main__":
    # Initialize client
    client = BedrockClient(region_name="us-east-1")

    # Test quick check (cheap Haiku)
    print("Testing Haiku model (quick check)...")
    response = client.invoke_for_use_case(
        "Summarize this in one sentence: [long text]", use_case="initial_triage"
    )
    print(f"Response: {response}")

    # Switch to Sonnet for detailed analysis
    print("\nSwitching to Sonnet for detailed analysis...")
    client.set_model("sonnet")

    response = client.invoke_for_use_case(
        "Analyze security findings and provide remediation steps...",
        use_case="detailed_analysis",
    )
    print(f"Response: {response}")
