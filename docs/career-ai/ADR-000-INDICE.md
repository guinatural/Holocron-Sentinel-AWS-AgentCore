# ADR — Índice de Decisões Arquiteturais

| ADR | Título | Status |
|---|---|---|
| [[ADR-001-MONOREPO-STACK\|ADR-001]] | Monorepo + Stack Fase 1 | Aceito |
| [[ADR-002-MULTI-TENANT\|ADR-002]] | Estratégia Multi-Tenant | Aceito |
| [[ADR-003-AUTH-COGNITO\|ADR-003]] | Autenticação Cognito + RBAC | Aceito |
| [[ADR-004-RAG-STRATEGY\|ADR-004]] | Estratégia RAG e Embeddings | Aceito |
| [[ADR-005-LLM-PROVIDERS\|ADR-005]] | Interface LLM Providers | Aceito |
| [[ADR-006-ASYNC-EXECUTION\|ADR-006]] | Lambda vs ECS vs In-Process | Proposto |
| [[ADR-007-COST-CONTROL\|ADR-007]] | Token Budget e Rate Limiting | Proposto |

---

## Quando criar novo ADR

- Mudança de banco, auth ou multi-tenant
- Novo provider LLM como primário
- Migração local → AWS
- Qualquer decisão irreversível

Formato: contexto → decisão → consequências → alternativas rejeitadas.
