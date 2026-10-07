# Arquitetura Técnica — Holocron Career AI

## Visão C4 — Contexto

```mermaid
flowchart LR
    User[Profissional / Tenant User]
    Admin[Tenant Admin]
    Platforms[Plataformas de Vagas<br/>RSS / APIs / Manual]
    
    User --> CareerAI[Holocron Career AI]
    Admin --> CareerAI
    Platforms --> CareerAI
    
    CareerAI --> Bedrock[Amazon Bedrock]
    CareerAI --> Cognito[Amazon Cognito]
    CareerAI --> Aurora[(Aurora PostgreSQL)]
    CareerAI --> S3[(S3 Artefatos)]
    CareerAI --> Vector[(Vector Store / RAG)]
```

---

## Visão C4 — Containers (Fase 1 local → Fase 8 AWS)

```mermaid
flowchart TB
    subgraph Client["Cliente"]
        WEB[Next.js 15<br/>Dashboard + Kanban]
    end

    subgraph Edge["Edge — Fase 8+"]
        CF[CloudFront]
        APIGW[API Gateway]
    end

    subgraph App["Aplicação"]
        API[FastAPI<br/>REST + OpenAPI]
        ORCH[Agent Orchestrator<br/>Strands SDK]
    end

    subgraph Agents["Agentes — Fase 2+"]
        SA[Search]
        MA[Matching]
        RA[Resume]
        CA[Cover Letter]
        AA[Application Assist]
        CRMA[CRM]
        IA[Interview]
        LA[Learning]
    end

    subgraph Data["Dados"]
        PG[(PostgreSQL)]
        VEC[(ChromaDB / OpenSearch)]
        S3[(S3 / MinIO local)]
        REDIS[(Redis — cache Fase 6+)]
    end

    subgraph Events["Eventos — Fase 3+"]
        EB[EventBridge]
        SQS[SQS]
        SF[Step Functions]
    end

    subgraph Auth["Auth"]
        COG[Cognito]
    end

    subgraph AI["IA"]
        BR[Bedrock Claude]
        RAG[RAG Pipeline]
    end

    subgraph Obs["Observabilidade"]
        OTEL[OpenTelemetry]
        CW[CloudWatch]
        XR[X-Ray]
    end

    WEB --> API
    API --> COG
    API --> PG
    API --> ORCH
    ORCH --> Agents
    Agents --> RAG --> VEC
    Agents --> BR
    Agents --> PG
    Agents --> S3
    ORCH --> EB --> SQS
    API --> OTEL --> CW
    OTEL --> XR
```

---

## Decisões sync vs async

| Fluxo | Modo | Justificativa |
|---|---|---|
| CRUD vagas/candidaturas | **Sync** REST | UX imediata, baixa latência |
| Login / refresh token | **Sync** | Padrão OAuth2 |
| Search Agent (RSS) | **Async** SQS + worker | Pode demorar; não bloqueia UI |
| Matching Agent | **Async** (job) | LLM + RAG > 5s |
| Resume / Cover Letter | **Async** (job) | Geração longa; polling ou SSE |
| Learning Agent | **Async** batch | Processamento noturno |
| Dashboard KPIs | **Sync** (cache 5min) | Agregações pré-computadas |

---

## Multi-tenant

```mermaid
flowchart LR
    REQ[Request JWT] --> MW[Tenant Middleware]
    MW --> |extrai tenant_id| CTX[Request Context]
    CTX --> REPO[Repository Layer]
    REPO --> |WHERE tenant_id = ?| PG[(PostgreSQL RLS opcional Fase 8)]
```

**Estratégia:** shared database, shared schema, `tenant_id` em todas as tabelas de negócio.

**RLS PostgreSQL:** habilitar na Fase 8 (produção AWS).

---

## Stack por camada

| Camada | Tecnologia | Fase |
|---|---|---|
| Frontend | Next.js 15, Tailwind, shadcn/ui (dark) | 1 |
| API | FastAPI, Pydantic v2, async SQLAlchemy 2 | 1 |
| Auth | Cognito User Pool + JWT | 1 |
| DB | PostgreSQL 16 + Alembic | 1 |
| Agentes | Strands Agents SDK + Bedrock | 2+ |
| RAG | ChromaDB (local) → Bedrock KB (prod) | 3+ |
| Filas | In-process (Fase 2) → SQS (Fase 8) | 2+ |
| Storage | MinIO local → S3 | 4+ |
| IaC | Docker Compose (Fase 1) → Terraform (Fase 8) | 1 / 8 |
| CI/CD | GitHub Actions | 1 |
| Observabilidade | structlog + OTEL → CloudWatch/X-Ray | 1 / 8 |

---

## Segurança (Zero Trust lite)

| Controle | Implementação |
|---|---|
| AuthN | Cognito JWT (RS256) |
| AuthZ | RBAC: `tenant_admin`, `user`, `viewer` |
| Isolamento | `tenant_id` middleware + testes cross-tenant |
| Secrets | `.env` local → Secrets Manager |
| Criptografia | TLS in-transit; AES at-rest (RDS Fase 8) |
| Rate limit | slowapi 60 req/min/user |
| Auditoria | tabela `audit_logs` imutável |
| LGPD | consent flags, TTL, DELETE endpoint |

---

## Custo previsível (Fase 3+)

- Token budget por tenant/dia (configurável)
- Cache de embeddings (Redis, TTL 24h)
- Modelo barato para triagem; Sonnet para geração
- Batch Learning Agent 1x/dia

---

## Estrutura do monorepo

```
holocron-career-ai/
├── apps/
│   ├── api/                 # FastAPI
│   │   ├── src/
│   │   │   ├── domain/
│   │   │   ├── application/
│   │   │   ├── infrastructure/
│   │   │   └── presentation/
│   │   ├── alembic/
│   │   └── tests/
│   └── web/                 # Next.js
├── packages/
│   ├── agents/              # Strands agents
│   ├── core/                # DTOs, ports, shared
│   └── rag/                 # ingestion, retrieval
├── infra/
│   ├── docker/
│   │   └── docker-compose.yml
│   └── terraform/           # Fase 8
├── docs/
│   ├── adr/
│   ├── openapi/
│   │   └── openapi.yaml
│   └── architecture/
├── scripts/
│   └── import-candidaturas.py
├── .github/workflows/
└── README.md
```

---

## Clean Architecture (backend)

```mermaid
flowchart TB
    subgraph Presentation
        R[Routers / Controllers]
    end
    subgraph Application
        S[Services / Use Cases]
    end
    subgraph Domain
        E[Entities]
        P[Ports / Interfaces]
    end
    subgraph Infrastructure
        REPO[SQLAlchemy Repos]
        EXT[External APIs]
        AGT[Agent Adapters]
    end

    R --> S --> P
    REPO -.-> P
    EXT -.-> P
    AGT -.-> P
```

Dependência sempre aponta para dentro (Domain no centro).
