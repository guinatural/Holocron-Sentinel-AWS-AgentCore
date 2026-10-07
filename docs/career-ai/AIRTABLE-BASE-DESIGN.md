# Design da Base Airtable — Holocron Career CRM

> Base sugerida: **Holocron Career AI**  
> Workspace: pessoal (free tier)

---

## Tabelas

### 1. Companies (Empresas)

| Campo | Tipo | Notas |
|---|---|---|
| Name | Single line | Primary |
| Website | URL | |
| Industry | Single select | Cloud, Fintech, Health, etc. |
| Favorite | Checkbox | Empresa alvo |
| Notes | Long text | |
| Jobs | Link → Jobs | |
| Applications | Link → Applications | via Jobs |

### 2. Jobs (Vagas)

| Campo | Tipo | Notas |
|---|---|---|
| Title | Single line | Primary |
| Company | Link → Companies | |
| Description | Long text | Texto completo |
| Source | Single select | RSS, Manual, LinkedIn, Gupy, Indeed |
| Source URL | URL | |
| Location | Single line | |
| Remote | Checkbox | |
| Seniority | Single select | Intern, Junior, Mid, Senior |
| Salary Min | Number | |
| Salary Max | Number | |
| Content Hash | Single line | Dedup Make.com |
| Status | Single select | Inbox, Reviewing, Skipped, Applied |
| Match Score | Number | 0–100 (Claude) |
| Match Notes | Long text | Explicação do score |
| Discovered At | Created time | Auto |
| Applications | Link → Applications | |

### 3. Applications (Candidaturas)

| Campo | Tipo | Notas |
|---|---|---|
| Name | Formula | `{Job Title} @ {Company}` |
| Job | Link → Jobs | |
| Pipeline Status | Single select | **Ver estados abaixo** |
| Applied At | Date | |
| Recruiter | Link → Recruiters | |
| Match Score | Lookup | De Jobs |
| Resume Version | Single select | v1-original, v2-aws, v3-security |
| Cover Letter | Attachment | PDF gerado |
| Notes | Long text | |
| Next Action | Single line | |
| Next Action Date | Date | |
| Feedback | Long text | Pós-entrevista |
| Salary Offered | Number | |
| Events | Link → Events | |

**Pipeline Status (11 estados):**
```
Discovered → Analyzed → Applied → Screening → HR Interview →
Tech Interview → Case → Offer → Rejected → Hired → Archived
```

### 4. Recruiters

| Campo | Tipo |
|---|---|
| Name | Single line |
| Email | Email |
| LinkedIn | URL |
| Company | Link → Companies |
| Applications | Link → Applications |

### 5. Events (Histórico)

| Campo | Tipo |
|---|---|
| Application | Link → Applications |
| Event Type | Single select | Status Change, Note, Email, Call |
| From Status | Single select |
| To Status | Single select |
| Note | Long text |
| Date | Created time |

### 6. Skills Tracker (opcional Fase 3)

| Campo | Tipo |
|---|---|
| Skill | Single line |
| Category | Single select | AWS, Python, Security, Soft |
| Demand Count | Rollup | De Jobs |
| You Have | Checkbox |

---

## Views essenciais

| View | Tabela | Tipo | Uso |
|---|---|---|---|
| Inbox | Jobs | Grid, filter Status=Inbox | Triagem diária |
| Kanban Pipeline | Applications | Kanban por Pipeline Status | CRM visual |
| Esta Semana | Applications | Calendar Next Action Date | Follow-ups |
| Score ≥ 70 | Jobs | Grid, filter Match Score ≥ 70 | Prioridade |
| Favoritas | Companies | Grid, Favorite=✓ | Alvos |
| KPI Dashboard | Applications | Interface | Métricas |

---

## Interface (Dashboard no-code)

Criar **Airtable Interface** com blocos:

1. **Números:** total candidaturas, aplicadas esta semana, entrevistas, taxa resposta
2. **Kanban:** pipeline Applications
3. **Lista:** Jobs Inbox
4. **Gráfico:** candidaturas por status (pie)
5. **Gráfico:** top skills (bar, quando Fase 3)

---

## Import inicial

Exportar tabela de `CONTROLE_CANDIDATURAS.md` para CSV:

| Empresa | Vaga | Data | Status | Diferencial |
→ mapear para Companies + Jobs + Applications

Script manual: copiar/colar 10 linhas atuais — 15 min.

---

## Formula útil — Taxa resposta

Campo rollup em Applications:
```
Response Rate = COUNT(status NOT IN (Applied, Discovered)) / COUNT(all)
```
Implementar via Interface ou revisão semanal manual no início.
