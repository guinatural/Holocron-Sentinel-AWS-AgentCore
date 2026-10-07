# ADR-002 — Estratégia Multi-Tenant

**Status:** Aceito  
**Data:** 2026-07-30

## Contexto

Produto é SaaS. Precisamos isolamento desde Fase 1 sem over-engineering.

## Decisão

**Shared database, shared schema, discriminação por `tenant_id`.**

- Coluna `tenant_id UUID NOT NULL` em toda tabela de negócio
- Middleware extrai `tenant_id` do JWT
- Repository base aplica filtro automático
- Testes de isolamento cross-tenant obrigatórios
- RLS PostgreSQL na Fase 8 (produção AWS)

## Consequências

- (+) Simples de implementar e escalar inicialmente
- (+) SaaS-ready desde Fase 1
- (-) Risco de vazamento se dev esquecer filtro → mitigado com base repository + testes

## Alternativas rejeitadas

| Alternativa | Motivo |
|---|---|
| DB por tenant | Custo operacional alto |
| Schema por tenant | Complexidade Alembic |
| Single-tenant only | Não serve portfólio SaaS |
