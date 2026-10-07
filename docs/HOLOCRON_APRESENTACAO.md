# 🛡️ Holocron Sentinel V2 — Apresentação do Projeto

---

> *"Não é um script. É um auditor que pensa."*

---

## O QUE É O HOLOCRON SENTINEL

O **Holocron Sentinel V2** é um Agente Autônomo de Cibersegurança e Conformidade LGPD, construído sobre a infraestrutura de IA generativa da AWS (Amazon Bedrock). Enquanto a maioria das soluções de compliance ainda depende de scripts passivos que apenas listam recursos, o Holocron *raciocina sobre falhas*, decide quais ferramentas usar, e entrega relatórios executivos em linguagem natural.

O projeto surgiu de uma pergunta real:

> *"E se um DPO pudesse ter um assistente que nunca dorme, audita em tempo real e não depende de um analista para interpretar os resultados?"*

---

## PROBLEMA QUE RESOLVE

No mercado brasileiro, a LGPD impõe obrigações concretas de segurança da informação a qualquer empresa que processa dados pessoais. O problema é que:

- Auditoria manual de infraestrutura AWS é cara e esporádica.
- Scripts estáticos (V1) não explicam o impacto de uma falha — só listam.
- DPOs sem background técnico não conseguem interpretar logs brutos.
- Ambientes multi-cliente exigem isolamento rígido de dados (que a maioria das ferramentas ignora).

O Holocron resolve todos esses pontos com uma única arquitetura.

---

## ARQUITETURA EM CAMADAS

```
┌─────────────────────────────────────────────────────┐
│              INTERFACE (Streamlit Dashboard)         │
│         Dark Mode · Glassmorphism · PT-BR            │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│           AGENTE CLAUDE 3.5 (AWS Bedrock)            │
│   Raciocínio · Seleção de Ferramentas · Relatório    │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│         CAMADA MCP (Model Context Protocol)          │
│   audit_event · generate_report · process_user_data  │
│        Wrappers boto3 + Anonimização LGPD            │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│             AWS INFRASTRUCTURE                       │
│   Lambda · S3 · CloudWatch · Bedrock AgentCore       │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│         MULTI-TENANCY (FileSessionManager)           │
│     Isolamento criptográfico por tenant_id           │
│    Memória persistente entre sessões do DPO          │
└─────────────────────────────────────────────────────┘
```

---

## DIFERENCIAIS TÉCNICOS

### 1. Agente com Raciocínio Real
O coração do sistema é Claude 3.5 (Haiku/Sonnet) via AWS Bedrock. O modelo não apenas executa comandos — ele analisa o ambiente, identifica qual ferramenta acionar e produz um relatório executivo em português, acessível para um gestor não-técnico.

### 2. Protocolo MCP Integrado
Os três wrappers MCP (`audit_event`, `generate_report`, `process_user_data`) conectam o raciocínio do LLM às funções Lambda reais da AWS. Cada wrapper já implementa anonimização LGPD na camada de transporte, antes de qualquer dado chegar ao modelo.

### 3. Multi-Tenancy com Isolamento Criptográfico
O `FileSessionManager` garante que cada empresa tenha seu próprio silo de memória. O system prompt do agente inclui instruções explícitas contra vazamento cross-tenant — uma medida que vai além do que a maioria das demos de AgentCore demonstra.

### 4. Automação de Infraestrutura
Scripts PowerShell (`setup-holocron.ps1`, `generate-mcp-wrappers.ps1`) automatizam o provisionamento do ambiente, reduzindo onboarding de novos desenvolvedores a um único comando.

---

## STACK TECNOLÓGICO

| Camada | Tecnologia |
|---|---|
| Runtime de IA | AWS Bedrock (Claude 3.5 Haiku / Sonnet) |
| Orquestração | Strands Agents SDK + LangGraph |
| Protocolo de Ferramentas | Model Context Protocol (MCP) |
| Infraestrutura AWS | boto3, Lambda, S3, CloudWatch |
| API Layer | FastAPI + Uvicorn |
| Frontend | Streamlit (Dark / Glassmorphism) |
| Qualidade de Código | Black, Ruff, pytest |
| Ambiente | Python 3.12, venv, PowerShell |

---

## ALINHAMENTO COM LGPD

O projeto não menciona LGPD apenas no nome. Ele implementa os princípios:

- **Art. 46 (Segurança):** Auditoria ativa de configurações S3, IAM e acesso público.
- **Art. 7º (Finalidade):** O agente opera com system prompt que limita o escopo de processamento de dados.
- **Art. 18 (Anonimização):** Remoção automática de campos sensíveis (`ssn` e derivados) antes do processamento pelo LLM.
- **Isolamento de Dados:** Multi-tenancy com silo criptográfico por `tenant_id`.

---

## STATUS ATUAL

| Componente | Estado |
|---|---|
| Ambiente e Setup Scripts | ✅ Operacional |
| Wrappers MCP (3 ferramentas) | ✅ Implementados |
| Anonimização LGPD na camada MCP | ✅ Ativo |
| Estrutura de pastas (`app/`, `tests/`, `docs/`) | ✅ Scaffolding criado |
| Lógica de negócio nos módulos `app/` | 🔶 Estrutura existe, implementação pendente |
| Testes automatizados | 🔶 Runner configurado, casos pendentes |
| Dashboard Streamlit | 🔶 Arquitetura definida, build pendente |
| Deploy AWS (AgentCore Runtime) | 🔶 Planejado, não executado |

---

## IMPACTO DE PORTFÓLIO

O Holocron Sentinel V2 demonstra, em um único projeto:

- **Engenharia de Prompt Avançada** — system prompt com restrições de compliance e anti-vazamento.
- **Infraestrutura como Ferramenta de IA** — boto3 exposto como MCP tools para um LLM.
- **Arquitetura Multi-Tenant Segura** — isolamento de sessão com FileSessionManager.
- **Conformidade Legal Aplicada** — LGPD como constraint de engenharia, não como documentação.
- **DevSecOps mindset** — segurança embutida no `.gitignore`, `.cursorrules`, e nos wrappers.

---

> **Repositório:** github.com/guinatural/Holocron-Sentinel-Startup-V2
> **Construído por:** Guilherme Barreto Gomes
> **Data de referência:** Março → Junho 2026
