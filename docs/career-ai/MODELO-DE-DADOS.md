# Modelo de Dados — PostgreSQL

> Schema inicial Fase 1. Todas as tabelas de negócio incluem `tenant_id UUID NOT NULL`.

---

## Diagrama ER (Fase 1 + extensões futuras)

```mermaid
erDiagram
    tenants ||--o{ users : has
    tenants ||--o{ jobs : owns
    tenants ||--o{ applications : owns
    tenants ||--o{ companies : owns
    
    users ||--o{ applications : creates
    jobs ||--o{ applications : receives
    companies ||--o{ jobs : posts
    companies ||--o{ recruiters : employs
    recruiters ||--o{ applications : contacts
    
    applications ||--o{ application_events : history
    applications ||--o{ match_scores : scores
    applications ||--o{ messages : messages
    applications ||--o{ interviews : interviews
    
    users ||--o{ resume_versions : owns
    resume_versions ||--o{ resume_provenance : tracks
    
    users ||--o{ user_skills : has
    skills ||--o{ user_skills : tagged
    skills ||--o{ job_skills : required
    
    tenants ||--o{ learning_insights : learns
    tenants ||--o{ audit_logs : audits

    tenants {
        uuid id PK
        string name
        string slug UK
        jsonb settings
        timestamp created_at
    }

    users {
        uuid id PK
        uuid tenant_id FK
        string cognito_sub UK
        string email UK
        string role
        jsonb profile
        timestamp created_at
    }

    companies {
        uuid id PK
        uuid tenant_id FK
        string name
        string website
        string industry
        boolean is_favorite
    }

    jobs {
        uuid id PK
        uuid tenant_id FK
        uuid company_id FK
        string title
        text description
        string source
        string source_url
        string location
        string seniority
        string employment_type
        decimal salary_min
        decimal salary_max
        string currency
        string content_hash UK
        jsonb raw_payload
        timestamp discovered_at
        timestamp expires_at
    }

    applications {
        uuid id PK
        uuid tenant_id FK
        uuid job_id FK
        uuid user_id FK
        uuid recruiter_id FK
        string status
        decimal match_score
        text notes
        jsonb metadata
        timestamp applied_at
        timestamp updated_at
    }

    application_events {
        uuid id PK
        uuid tenant_id FK
        uuid application_id FK
        string event_type
        string from_status
        string to_status
        text note
        uuid actor_id
        timestamp created_at
    }

    recruiters {
        uuid id PK
        uuid tenant_id FK
        uuid company_id FK
        string name
        string email
        string linkedin_url
    }

    skills {
        uuid id PK
        string name UK
        string category
    }

    user_skills {
        uuid user_id FK
        uuid skill_id FK
        int proficiency
    }

    job_skills {
        uuid job_id FK
        uuid skill_id FK
        boolean required
    }

    match_scores {
        uuid id PK
        uuid tenant_id FK
        uuid application_id FK
        decimal total_score
        jsonb breakdown
        jsonb evidence
        jsonb gaps
        string model_version
        timestamp computed_at
    }

    resume_versions {
        uuid id PK
        uuid tenant_id FK
        uuid user_id FK
        string label
        text content_md
        string content_hash
        decimal ats_score
        boolean facts_verified
        timestamp created_at
    }

    resume_provenance {
        uuid id PK
        uuid resume_version_id FK
        string field_path
        string source_doc
        string source_excerpt
    }

    messages {
        uuid id PK
        uuid tenant_id FK
        uuid application_id FK
        string message_type
        text content
        string model_version
        jsonb prompt_metadata
        timestamp created_at
    }

    interviews {
        uuid id PK
        uuid tenant_id FK
        uuid application_id FK
        string interview_type
        timestamp scheduled_at
        jsonb prep_pack
        text feedback
    }

    learning_insights {
        uuid id PK
        uuid tenant_id FK
        string insight_type
        jsonb data
        decimal confidence
        timestamp computed_at
    }

    audit_logs {
        uuid id PK
        uuid tenant_id FK
        uuid user_id FK
        string action
        string resource_type
        uuid resource_id
        jsonb details
        timestamp created_at
    }
```

---

## Estados do pipeline (`applications.status`)

```
discovered → analyzed → applied → screening → hr_interview →
tech_interview → case → offer → rejected → hired → archived
```

Transições validadas no service layer (máquina de estados).

---

## Índices recomendados

```sql
-- Multi-tenant (todas as queries)
CREATE INDEX idx_jobs_tenant ON jobs(tenant_id);
CREATE INDEX idx_applications_tenant_status ON applications(tenant_id, status);
CREATE INDEX idx_applications_tenant_updated ON applications(tenant_id, updated_at DESC);

-- Deduplicação
CREATE UNIQUE INDEX idx_jobs_hash_tenant ON jobs(tenant_id, content_hash);

-- Busca
CREATE INDEX idx_jobs_title_trgm ON jobs USING gin(title gin_trgm_ops);
CREATE INDEX idx_companies_name_trgm ON companies USING gin(name gin_trgm_ops);

-- Match scores histórico
CREATE INDEX idx_match_scores_app ON match_scores(application_id, computed_at DESC);

-- Auditoria LGPD
CREATE INDEX idx_audit_tenant_time ON audit_logs(tenant_id, created_at DESC);
```

---

## Migrações Alembic

| Revisão | Conteúdo | Fase |
|---|---|---|
| `001_initial` | tenants, users, companies, jobs, applications | 1 |
| `002_events` | application_events, recruiters | 1 |
| `003_skills` | skills, user_skills, job_skills | 3 |
| `004_matching` | match_scores | 3 |
| `005_resumes` | resume_versions, resume_provenance | 4 |
| `006_messages` | messages | 5 |
| `007_interviews` | interviews | 7 |
| `008_learning` | learning_insights | 8 |
| `009_audit` | audit_logs | 1 (já na 001 se possível) |

---

## Versionamento de documentos

- CV/carta: imutável por versão (`resume_versions.content_hash`)
- Provenance: cada campo editado referencia fonte RAG
- S3 path: `s3://{tenant_id}/resumes/{version_id}.pdf`

---

## Seed Fase 1

```sql
INSERT INTO tenants (id, name, slug) VALUES
  ('00000000-0000-0000-0000-000000000001', 'Guilherme Personal', 'guilherme');

INSERT INTO users (id, tenant_id, cognito_sub, email, role) VALUES
  ('00000000-0000-0000-0000-000000000002',
   '00000000-0000-0000-0000-000000000001',
   'local-dev', 'guilherme@dev.local', 'tenant_admin');
```
