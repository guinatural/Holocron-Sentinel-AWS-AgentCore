# Estratégia — Portfólio + Praticidade

## Problema a resolver

Dois objetivos conflitantes:

1. **Portfólio:** impressionar recrutadores Cloud/AI com arquitetura SaaS, multiagentes, Bedrock, LGPD.
2. **Praticidade:** usar todo dia para conseguir entrevistas antes da prova SAA-C03 (14/09/2026).

## Decisão: arquitetura SaaS, execução incremental

| Camada | Portfólio (documentar) | Praticidade (implementar) |
|---|---|---|
| Multi-tenant | `tenant_id` + RBAC desde Fase 1 | Single-tenant pessoal (`guilherme`) |
| Auth | Cognito + JWT (desenho AWS) | Cognito dev pool + bypass local opcional |
| Banco | Aurora PostgreSQL (prod) | PostgreSQL Docker Compose |
| Agentes | 8 agentes Strands/Bedrock | CRM manual Fase 1; IA Fase 2+ |
| Deploy | ECS Fargate + API Gateway | `docker compose up` |
| RAG | Bedrock Knowledge Base | ChromaDB local Fase 3 |

**Regra de ouro:** cada fase entrega valor real de uso, não só diagrama.

---

## Posicionamento no portfólio

```
Holocron Ecosystem
├── Holocron Sentinel V2    → Compliance / LGPD / DPO (B2B)
└── Holocron Career AI      → Career CRM / Multiagent (B2C SaaS)
```

### Narrativa para entrevista (30 segundos)

> "Construí um ecossistema Holocron: o Sentinel audita conformidade LGPD na AWS; o Career AI é um CRM de carreira multiagente que faz matching inteligente, personaliza currículo sem inventar fatos, e aprende com resultados. Arquitetura SaaS multi-tenant, FastAPI, Bedrock, PostgreSQL, observabilidade OpenTelemetry."

### Evidências por fase

| Fase | Demo | Skill demonstrada |
|---|---|---|
| 1 | Kanban + KPIs + import candidaturas | Full-stack, DDD, PostgreSQL |
| 2 | 20 vagas RSS deduplicadas | Integração, pipelines async |
| 3 | Match score explicável | RAG + Bedrock + prompt engineering |
| 4 | CV adaptado com diff | LLM governance, provenance |
| 5 | Cover letter personalizada | Geração controlada |
| 6 | Pipeline completo | CRM, event sourcing leve |
| 7 | Prep entrevista AWS | Domain expertise |
| 8 | Analytics + learning loop | ML ops leve, métricas |

---

## O que NÃO fazer (anti-padrões)

- ❌ Scraping LinkedIn automatizado (risco ToS + LGPD)
- ❌ SaaS billing antes de usar pessoalmente 30 dias
- ❌ 8 agentes antes do CRM funcionar
- ❌ Inventar experiências no currículo (mata credibilidade)
- ❌ Terraform AWS antes do produto local rodar

---

## Métricas de sucesso pessoal (90 dias)

| Métrica | Meta |
|---|---|
| Candidaturas rastreadas no CRM | 100% (zero planilha solta) |
| Tempo/dia em busca manual | < 45 min |
| Taxa entrevista | ≥ 10% das aplicadas |
| Commits GitHub/semana | ≥ 5 (assiduidade PDI) |
| Post LinkedIn sobre o projeto | 2 (Fase 1 e Fase 3) |

---

## Próximo passo

Implementar **Fase 1** conforme [[ROADMAP]]. Documentação completa antes de código.
