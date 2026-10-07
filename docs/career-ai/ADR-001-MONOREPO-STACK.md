# ADR-001 — Monorepo e Stack Fase 1

**Status:** Aceito  
**Data:** 2026-07-30

## Contexto

Precisamos de stack que demonstre competência full-stack Cloud/AI e permita iterar rápido localmente.

## Decisão

- **Monorepo** com `apps/api` (FastAPI) + `apps/web` (Next.js) + `packages/*`
- **PostgreSQL 16** via Docker Compose desde Fase 1
- **Alembic** para migrações
- **pnpm** workspaces para frontend; **uv/poetry** para Python
- **Docker Compose** para dev local

## Consequências

- (+) Um repo, um CI, fácil demo
- (+) PostgreSQL real desde início (sem migração SQLite→PG)
- (-) Monorepo exige disciplina de boundaries

## Alternativas rejeitadas

| Alternativa | Motivo rejeição |
|---|---|
| Multi-repo | Overhead para solo dev |
| SQLite Fase 1 | Migração desnecessária |
| Django | Menos alinhado ao Holocron (FastAPI) |
