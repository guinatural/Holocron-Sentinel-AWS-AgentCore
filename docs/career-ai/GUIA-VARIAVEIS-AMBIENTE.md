# Guia de Variáveis de Ambiente

> Arquivo raiz: `.env` (nunca commitar). Template: `.env.example` (commitar).

---

## Backend (`apps/api/.env`)

### App

| Variável | Obrigatória | Default | Descrição |
|---|---|---|---|
| `APP_ENV` | sim | `development` | `development` \| `staging` \| `production` |
| `APP_NAME` | não | `Holocron Career AI` | Nome exibido |
| `DEBUG` | não | `false` | Hot reload + logs verbose |
| `LOG_LEVEL` | não | `INFO` | DEBUG, INFO, WARNING, ERROR |
| `API_PREFIX` | não | `/api/v1` | Prefixo REST |
| `CORS_ORIGINS` | sim | `http://localhost:3000` | CSV de origins |

### Database

| Variável | Obrigatória | Default | Descrição |
|---|---|---|---|
| `DATABASE_URL` | sim | — | `postgresql+asyncpg://user:pass@localhost:5432/career_ai` |
| `DATABASE_POOL_SIZE` | não | `5` | Pool connections |
| `DATABASE_ECHO` | não | `false` | Log SQL (dev only) |

### Auth (Cognito)

| Variável | Obrigatória | Default | Descrição |
|---|---|---|---|
| `AUTH_DEV_BYPASS` | não | `false` | `true` = skip Cognito (dev only) |
| `AUTH_DEV_API_KEY` | se bypass | — | Key para dev bypass |
| `COGNITO_REGION` | sim* | `us-east-1` | Região AWS |
| `COGNITO_USER_POOL_ID` | sim* | — | User Pool ID |
| `COGNITO_APP_CLIENT_ID` | sim* | — | App Client ID |
| `COGNITO_JWKS_URL` | não | auto | JWKS endpoint |
| `JWT_ALGORITHM` | não | `RS256` | Algoritmo JWT |

*Obrigatório se `AUTH_DEV_BYPASS=false`

### LLM (Fase 3+)

| Variável | Obrigatória | Default | Descrição |
|---|---|---|---|
| `LLM_PROVIDER` | não | `bedrock` | `bedrock` \| `ollama` \| `openai` |
| `AWS_REGION` | se bedrock | `us-east-1` | Região Bedrock |
| `AWS_PROFILE` | não | `default` | Profile AWS CLI |
| `BEDROCK_MODEL_ID` | não | `anthropic.claude-3-5-sonnet-20241022-v2:0` | Modelo |
| `OLLAMA_BASE_URL` | se ollama | `http://localhost:11434` | URL Ollama |
| `OLLAMA_MODEL` | se ollama | `llama3.2` | Modelo local |
| `OPENAI_API_KEY` | se openai | — | Key OpenAI |
| `LLM_TOKEN_BUDGET_DAILY` | não | `100000` | Budget tokens/tenant/dia |

### RAG (Fase 3+)

| Variável | Obrigatória | Default | Descrição |
|---|---|---|---|
| `CHROMA_PERSIST_DIR` | não | `./data/chroma` | Persistência local |
| `RAG_CHUNK_SIZE` | não | `512` | Tokens por chunk |
| `RAG_CHUNK_OVERLAP` | não | `64` | Overlap |
| `RAG_TOP_K` | não | `5` | Resultados retrieval |

### Storage (Fase 4+)

| Variável | Obrigatória | Default | Descrição |
|---|---|---|---|
| `STORAGE_BACKEND` | não | `local` | `local` \| `s3` |
| `S3_BUCKET` | se s3 | — | Bucket artefatos |
| `LOCAL_STORAGE_PATH` | se local | `./data/storage` | Path local |

### Observabilidade

| Variável | Obrigatória | Default | Descrição |
|---|---|---|---|
| `OTEL_ENABLED` | não | `false` | OpenTelemetry |
| `OTEL_EXPORTER_ENDPOINT` | se otel | — | Collector endpoint |

---

## Frontend (`apps/web/.env.local`)

| Variável | Obrigatória | Default | Descrição |
|---|---|---|---|
| `NEXT_PUBLIC_API_URL` | sim | `http://localhost:8000/api/v1` | URL da API |
| `NEXT_PUBLIC_APP_NAME` | não | `Holocron Career AI` | Título UI |
| `NEXT_PUBLIC_COGNITO_DOMAIN` | Fase 1+ | — | Hosted UI domain |
| `NEXT_PUBLIC_COGNITO_CLIENT_ID` | Fase 1+ | — | Client ID |

---

## Docker Compose (`infra/docker/.env`)

| Variável | Default | Descrição |
|---|---|---|
| `POSTGRES_USER` | `career_ai` | User DB |
| `POSTGRES_PASSWORD` | `career_ai_dev` | Password DB |
| `POSTGRES_DB` | `career_ai` | Database name |
| `POSTGRES_PORT` | `5432` | Porta host |

---

## Exemplo `.env.example` (raiz)

```env
# === App ===
APP_ENV=development
DEBUG=true
LOG_LEVEL=DEBUG
CORS_ORIGINS=http://localhost:3000

# === Database ===
DATABASE_URL=postgresql+asyncpg://career_ai:career_ai_dev@localhost:5432/career_ai

# === Auth (dev bypass para Fase 1 local) ===
AUTH_DEV_BYPASS=true
AUTH_DEV_API_KEY=dev-local-key-change-me

# === Cognito (preencher quando sair do bypass) ===
# COGNITO_REGION=us-east-1
# COGNITO_USER_POOL_ID=us-east-1_XXXXX
# COGNITO_APP_CLIENT_ID=xxxxxxxx

# === LLM (Fase 3+) ===
# LLM_PROVIDER=bedrock
# AWS_REGION=us-east-1
# AWS_PROFILE=default

# === Frontend ===
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## Segurança

- ❌ Nunca commitar `.env`
- ✅ Usar `.env.example` sem valores reais
- ✅ Secrets Manager na AWS (Fase 8)
- ✅ Rotacionar `AUTH_DEV_API_KEY` se vazou
