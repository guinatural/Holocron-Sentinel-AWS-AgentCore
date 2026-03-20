import json
import logging
import re
from datetime import datetime, timezone

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent, tool
from strands.models import BedrockModel

logger = logging.getLogger("holocron_sentinel")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")

app = BedrockAgentCoreApp()


@tool
def validar_termo_consentimento(texto: str) -> str:
    t = (texto or "").lower()
    checks = {
        "finalidade": any(k in t for k in ["finalidade", "propósito", "objetivo"]),
        "base_legal": any(k in t for k in ["base legal", "consentimento", "art.", "artigo"]),
        "direitos_titular": any(k in t for k in ["direitos", "revogação", "acesso", "correção", "portabilidade", "eliminação"]),
        "canal_dpo": any(k in t for k in ["encarregado", "dpo", "contato", "canal"]),
        "retencao": any(k in t for k in ["retenção", "prazo", "armazenamento"]),
    }
    faltando = [k for k, ok in checks.items() if not ok]
    if not faltando:
        return "OK: termo parece conter itens mínimos (finalidade, base legal, direitos, canal DPO, retenção)."
    return "PENDENTE: faltando itens no termo: " + ", ".join(faltando)


@tool
def anonimizar_texto(texto: str) -> str:
    if not texto:
        return ""
    out = re.sub(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b", "***.***.***-**", texto)
    out = re.sub(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", "***@***.***", out, flags=re.IGNORECASE)
    return out


@tool
def registrar_evento_auditoria(evento_json: str) -> str:
    try:
        evento = json.loads(evento_json) if isinstance(evento_json, str) else evento_json
    except Exception:
        evento = {"raw": str(evento_json)}
    envelope = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "tipo": "AUDITORIA_COMPLIANCE",
        "evento": evento,
    }
    logger.info("AUDIT_EVENT %s", json.dumps(envelope, ensure_ascii=False))
    return "AUDIT_OK"


model_id = "global.anthropic.claude-haiku-4-5-20251001-v1:0"
model = BedrockModel(model_id=model_id)

agent = Agent(
    model=model,
    tools=[validar_termo_consentimento, anonimizar_texto, registrar_evento_auditoria],
    system_prompt=(
        "Você é o Holocron Sentinel V2, um agente corporativo de Compliance LGPD. "
        "Ajude a validar termos de consentimento, sugerir ajustes e orientar auditoria. "
        "Quando houver dados pessoais no texto, prefira anonimizar antes de registrar eventos."
    ),
)


@app.entrypoint
def strands_agent_bedrock(payload):
    user_input = (payload or {}).get("prompt", "")
    logger.info("INVOKE prompt_len=%s", len(user_input))
    response = agent(user_input)
    return response.message["content"][0]["text"]


if __name__ == "__main__":
    app.run()
