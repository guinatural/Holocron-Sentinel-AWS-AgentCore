# Holocron Sentinel V2

> *"Não é um script. É um auditor que pensa."*

## Status do Projeto

⚠️ **EM DESENVOLVIMENTO ATIVO** - Última atualização: Outubro 2026

| Componente | Status | Detalhes |
|---|---|---|
| Core Architecture | ✅ | Estrutura com multi-tenancy |
| LGPD Anonymization | ✅ | Implementação básica |
| Session Manager | ✅ | FileSessionManager com criptografia |
| Bedrock Integration | ✅ | Model selection com otimização de custo |
| MCP Wrappers | ⚠️ | Wrappers básicos, precisam refinamento |
| Dashboard UI | 🔶 | Planejado (Streamlit) |
| Tests | 🔶 | Testes iniciais (unit tests) |
| CI/CD | 🔶 | Workflow básico configurado |

## Visão Geral

Holocron Sentinel V2 é um Agente Autônomo de Cibersegurança e Conformidade LGPD, construído sobre AWS Bedrock. Diferente da V1 (scripts estáticos), a V2 é uma ferramenta **SaaS Multi-Tenant** que raciocina sobre falhas, decide quais ferramentas usar e entrega relatórios executivos em linguagem natural.

### Diferença do Wayfinder

- **Holocron** = Agente **sob demanda** (prompt → Boto3 + Bedrock → relatório)
- **Wayfinder** = **Vigilância 24/7** (AWS Config + EventBridge + Lambda + Terraform)

## Stack Tecnológica

| Camada | Tecnologia |
|---|---|
| Runtime de IA | AWS Bedrock (Claude 3.5 Haiku / Sonnet) |
| Orquestração | Strands Agents SDK (preferido) |
| Infraestrutura AWS | boto3, Lambda, S3, CloudWatch |
| Backend | FastAPI + Uvicorn |
| Frontend | Streamlit (Planejado) |
| Qualidade | Black, Ruff, pytest |
| Auth | Cognito (Planejado) |

## Estrutura do Projeto

```
holocron/
├── app/
│   ├── agents/         # Agent implementations
│   ├── api/            # API endpoints (FastAPI)
│   ├── aws/            # AWS integrations
│   │   ├── bedrock.py  # Bedrock client
│   │   └── secrets.py  # Secrets manager
│   ├── core/           # Core utilities
│   │   ├── session_manager.py  # FileSessionManager
│   │   └── error_handling.py   # Retry logic
│   ├── mcp/            # MCP wrappers
│   ├── rag/            # RAG pipeline
│   └── security/       # LGPD compliance
│       └── anonymization.py    # Sensitive data removal
├── tests/
│   └── unit/           # Unit tests
├── .github/workflows/  # CI/CD
├── requirements.txt
├── .cursorrules        # Prompt engineering rules
└── README.md
```

## Configuração Local

### Requisitos

- Python 3.12+
- AWS credentials configurados
- AWS Bedrock access enabled

### Instalação

```bash
cd holocron
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Variáveis de Ambiente

```bash
# AWS
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1

# App
SESSION_KEY=your_32_byte_encryption_key
ENVIRONMENT=local
```

### Executar Testes

```bash
pytest tests/ -v
```

### Executar Anonymization Demo

```bash
python app/security/anonymization.py
```

## Arquitetura Multi-Tenant

Cada tenant tem:
- **Isolamento de sessão**: `tenant_id` único
- **Criaptografia**: Dados criptografados por tenant
- **Limites de uso**: Budget manager por tenant
- **Logs separados**: CloudWatch log groups isolados

## LGPD Compliance

O projeto implementa os princípios da LGPD:

- **Art. 46 (Segurança)**: Auditoria ativa de configurações
- **Art. 7º (Finalidade)**: System prompt com restrições
- **Art. 18 (Anonimização)**: Remoção automática de dados sensíveis

Campos anonimizados: CPF, CNPJ, email, nome, data de nascimento, telefone, endereço, RH, documentos, dados financeiros.

## Próximos Passos

### Short Term (Esta Semana)
- [ ] Fix MCP wrappers (error handling, validation)
- [ ] Implementar scanner S3 (block public access)
- [ ] CI/CD pipeline funcional
- [ ] Testes unitários (80%+ coverage)

### Medium Term (2-4 Semanas)
- [ ] FileSessionManager com criptografia completa
- [ ] Dashboard Streamlit
- [ ] Escaneadores IAM, EC2, EBS
- [ ] Relatório em PDF

### Long Term (2-3 Meses)
- [ ] Deploy AWS (ECS Fargate)
- [ ] Cognito integration
- [ ] API REST completa
- [ ] Multi-region support

## GitHub Repositories

| Projeto | Status | Link |
|---|---|---|
| Holocron-Sentinel-AWS-AgentCore | ✅ Ativo | [guinatural/Holocron-Sentinel-AWS-AgentCore](https://github.com/guinatural/Holocron-Sentinel-AWS-AgentCore) |
| Holocron-Sentinel-Startup-V2 | ⚠️ Descontinuado | [guinatural/Holocron-Sentinel-Startup-V2](https://github.com/guinatural/Holocron-Sentinel-Startup-V2) |

## Documentação

- [ADR-000-INDICE](docs/career-ai/ADR-000-INDICE.md) - Architecture Decision Records
- [ARQUITETURA](docs/career-ai/ARQUITETURA.md) - Technical Architecture
- [ROADMAP](docs/career-ai/ROADMAP.md) - 8 Fases de Implementação
- [PRD-RESUMO-EXECUTIVO](docs/career-ai/PRD-RESUMO-EXECUTIVO.md) - Product Requirements

## Contato

Desenvolvido por Guilherme Barreto  
LinkedIn: [linkedin.com/in/guinatural](https://linkedin.com/in/guinatural)

## Licença

MIT License