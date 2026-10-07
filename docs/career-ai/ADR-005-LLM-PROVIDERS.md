# ADR-005 — Interface LLM Providers

**Status:** Aceito  
**Data:** 2026-07-30

## Contexto

Agentes usam LLM. Precisamos trocar provider sem reescrever agentes.

## Decisão

Interface `LLMProvider` (Protocol) com implementações:

| Provider | Uso | Fase |
|---|---|---|
| BedrockProvider | Produção, primário | 3+ |
| OllamaProvider | Dev offline | 3+ |
| OpenAIProvider | Fallback opcional | futuro |

Config via env: `LLM_PROVIDER=bedrock|ollama|openai`

Modelo padrão Bedrock: `anthropic.claude-3-5-sonnet-20241022-v2:0`

## Token budget

- Por request: max 4096 output
- Por tenant/dia: 100k tokens (configurável)
- Matching: max 2048 (triagem barata)

## Consequências

- (+) Testável com mocks
- (+) Dev sem AWS via Ollama
- (-) Interface adds abstraction layer (aceitável)
