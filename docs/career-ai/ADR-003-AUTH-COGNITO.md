# ADR-003 — Autenticação Cognito + RBAC

**Status:** Aceito  
**Data:** 2026-07-30

## Contexto

SaaS precisa auth production-grade. Cognito integra com AWS e demonstra skill de portfólio.

## Decisão

- **Amazon Cognito User Pool** (dev pool para local)
- JWT RS256 validado no middleware FastAPI
- Roles: `tenant_admin`, `user`, `viewer`
- Claims custom: `tenant_id`, `role`
- Dev bypass: `AUTH_DEV_BYPASS=true` + API key local (somente dev)

## RBAC

| Role | Jobs | Applications | Admin | Agents |
|---|---|---|---|---|
| tenant_admin | CRUD | CRUD | sim | sim |
| user | R | CRUD own | não | sim |
| viewer | R | R | não | não |

## Consequências

- (+) Production-ready auth
- (+) Portfólio AWS
- (-) Setup Cognito local mais complexo → mitigado com dev bypass

## Alternativas rejeitadas

| Alternativa | Motivo |
|---|---|
| Auth0 | Custo + menos AWS-native |
| JWT manual | Reinventar roda |
| Session cookies only | Não serve SPA/mobile futuro |
