# Guia de Desenvolvimento Local

## Pré-requisitos

| Ferramenta | Versão mínima |
|---|---|
| Docker Desktop | 4.x |
| Node.js | 20+ |
| pnpm | 9+ |
| Python | 3.12+ |
| uv ou poetry | latest |
| AWS CLI | 2.x (Fase 3+, Bedrock) |
| Git | 2.x |

---

## Setup inicial (Fase 1)

```powershell
# 1. Clonar (quando repo existir)
git clone https://github.com/guinatural/holocron-career-ai.git
cd holocron-career-ai

# 2. Variáveis de ambiente
copy .env.example .env
# Editar .env — ver [[GUIA-VARIAVEIS-AMBIENTE]]

# 3. Subir infraestrutura
docker compose -f infra/docker/docker-compose.yml up -d postgres

# 4. Backend
cd apps/api
uv sync                          # ou: poetry install
uv run alembic upgrade head
uv run uvicorn src.main:app --reload --port 8000

# 5. Frontend (novo terminal)
cd apps/web
pnpm install
pnpm dev                         # http://localhost:3000
```

---

## Docker Compose (tudo junto)

```powershell
docker compose -f infra/docker/docker-compose.yml up --build
```

Serviços:

| Serviço | URL |
|---|---|
| API | http://localhost:8000 |
| Swagger | http://localhost:8000/docs |
| Web | http://localhost:3000 |
| PostgreSQL | localhost:5432 |

---

## Comandos úteis

```powershell
# Migrations
cd apps/api
uv run alembic revision --autogenerate -m "descricao"
uv run alembic upgrade head
uv run alembic downgrade -1

# Testes
uv run pytest tests/ -v --cov=src --cov-report=term-missing

# Lint
uv run ruff check src/
uv run mypy src/

# Import candidaturas
uv run python ../../scripts/import-candidaturas.py `
  --file "../../AWS-reStart-Compliance-Portfolio/01 - PROJETOS/Freelance/CONTROLE_CANDIDATURAS.md"

# Frontend
pnpm lint
pnpm test
pnpm build
```

---

## Estrutura de branches

```
main          → estável
develop       → integração
feat/*        → features
fix/*         → bugs
docs/*        → documentação
```

---

## CI/CD (GitHub Actions)

Pipeline mínimo Fase 1:

1. Lint Python + TypeScript
2. pytest
3. pnpm test + build
4. Docker build (sem push)

---

## Troubleshooting

| Problema | Solução |
|---|---|
| Port 5432 ocupada | Alterar `POSTGRES_PORT` no `.env` |
| Cognito erro local | Setar `AUTH_DEV_BYPASS=true` |
| CORS blocked | Verificar `CORS_ORIGINS` inclui `http://localhost:3000` |
| Migration falha | `alembic downgrade base && alembic upgrade head` |
| Bedrock AccessDenied | Configurar AWS profile + região us-east-1 |

---

## Checklist antes de PR

- [ ] Testes passando
- [ ] Swagger atualizado se endpoint novo
- [ ] Migration incluída se schema mudou
- [ ] `tenant_id` em toda query nova
- [ ] Sem secrets no código
- [ ] README atualizado se setup mudou
