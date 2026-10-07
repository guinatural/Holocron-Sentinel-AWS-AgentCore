# OpenAPI / Contratos — Fase 1

> Spec completa será gerada em `docs/openapi/openapi.yaml` no repositório.  
> Swagger UI: `http://localhost:8000/docs`

---

## Info

```yaml
openapi: 3.1.0
info:
  title: Holocron Career AI API
  version: 0.1.0
  description: CRM de carreira SaaS multi-tenant
servers:
  - url: http://localhost:8000/api/v1
    description: Local dev
```

---

## Auth

```yaml
securitySchemes:
  BearerAuth:
    type: http
    scheme: bearer
    bearerFormat: JWT
```

Header obrigatório (exceto health): `Authorization: Bearer {token}`

Claims JWT: `sub`, `tenant_id`, `role`, `email`

---

## Endpoints Fase 1

### Health

| Method | Path | Auth | Descrição |
|---|---|---|---|
| GET | `/health` | não | Liveness |
| GET | `/ready` | não | Readiness (DB ping) |

### Auth

| Method | Path | Descrição |
|---|---|---|
| POST | `/auth/login` | Troca credentials por JWT (dev) |
| POST | `/auth/refresh` | Refresh token |
| GET | `/auth/me` | Perfil do usuário logado |

### Jobs

| Method | Path | Descrição |
|---|---|---|
| GET | `/jobs` | Lista paginada (filtros: status, source, q) |
| POST | `/jobs` | Cria vaga manual |
| GET | `/jobs/{id}` | Detalhe |
| PATCH | `/jobs/{id}` | Atualiza |
| DELETE | `/jobs/{id}` | Soft delete |

### Applications

| Method | Path | Descrição |
|---|---|---|
| GET | `/applications` | Lista (filtros: status, min_score) |
| POST | `/applications` | Cria candidatura |
| GET | `/applications/{id}` | Detalhe + timeline |
| PATCH | `/applications/{id}` | Atualiza (inclui status) |
| POST | `/applications/{id}/transition` | Transição de estado validada |
| DELETE | `/applications/{id}` | Arquiva |

### Companies

| Method | Path | Descrição |
|---|---|---|
| GET | `/companies` | Lista |
| POST | `/companies` | Cria |
| GET | `/companies/{id}` | Detalhe |
| PATCH | `/companies/{id}` | Atualiza |

### Dashboard

| Method | Path | Descrição |
|---|---|---|
| GET | `/dashboard/kpis` | KPIs agregados |
| GET | `/dashboard/pipeline` | Contagem por status |

### Import

| Method | Path | Descrição |
|---|---|---|
| POST | `/import/markdown` | Import CONTROLE_CANDIDATURAS |
| POST | `/import/csv` | Import CSV genérico |

---

## Schemas principais

### JobCreate

```yaml
JobCreate:
  type: object
  required: [title, company_id]
  properties:
    title: { type: string, maxLength: 255 }
    company_id: { type: string, format: uuid }
    description: { type: string }
    source: { type: string, enum: [manual, rss, api, linkedin] }
    source_url: { type: string, format: uri }
    location: { type: string }
    seniority: { type: string, enum: [intern, junior, mid, senior, lead] }
    employment_type: { type: string, enum: [clt, pj, remote, hybrid] }
    salary_min: { type: number }
    salary_max: { type: number }
    currency: { type: string, default: BRL }
```

### ApplicationCreate

```yaml
ApplicationCreate:
  type: object
  required: [job_id]
  properties:
    job_id: { type: string, format: uuid }
    status: { type: string, default: discovered }
    notes: { type: string }
    applied_at: { type: string, format: date-time }
```

### ApplicationTransition

```yaml
ApplicationTransition:
  type: object
  required: [to_status]
  properties:
    to_status:
      type: string
      enum: [discovered, analyzed, applied, screening, hr_interview,
             tech_interview, case, offer, rejected, hired, archived]
    note: { type: string }
```

### DashboardKPIs

```yaml
DashboardKPIs:
  type: object
  properties:
    total_jobs: { type: integer }
    total_applications: { type: integer }
    applications_this_week: { type: integer }
    response_rate: { type: number, format: float }
    interview_rate: { type: number, format: float }
    avg_response_days: { type: number, format: float }
    top_skills: { type: array, items: { type: object } }
    pipeline_distribution: { type: object }
```

### Error

```yaml
Error:
  type: object
  properties:
    detail: { type: string }
    code: { type: string }
    trace_id: { type: string }
```

---

## Paginação padrão

```yaml
PaginatedResponse:
  properties:
    items: { type: array }
    total: { type: integer }
    page: { type: integer, default: 1 }
    page_size: { type: integer, default: 20 }
    pages: { type: integer }
```

Query params: `?page=1&page_size=20&sort=-updated_at`

---

## Endpoints futuros (Fase 2+)

| Fase | Prefix | Exemplos |
|---|---|---|
| 2 | `/agents/search` | POST trigger busca |
| 3 | `/agents/matching/{job_id}` | POST calcular score |
| 4 | `/agents/resume` | POST gerar versão |
| 5 | `/agents/cover-letter` | POST gerar mensagens |
| 7 | `/agents/interview/{app_id}` | POST prep pack |
| 8 | `/analytics/insights` | GET insights |

Jobs async retornam `202 Accepted` + `job_id` para polling em `/jobs/tasks/{id}`.
