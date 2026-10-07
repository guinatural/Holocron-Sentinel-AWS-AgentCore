# Holocron Career AI — Hub de Documentação

> ⚠️ **Decisão atual:** stack **100% no-code** → ver [[00 - INDEX - Holocron Career AI (No-Code)|INDEX No-Code]]  
> A documentação abaixo (FastAPI/Next.js) fica como referência arquitetural futura.

> **Produto:** Plataforma SaaS multi-tenant de gestão de carreira com agentes de IA  
> **Ecossistema:** extensão do [[HOLOCRON_APRESENTACAO|Holocron Sentinel]]  
> **Status:** Fase 0 — Arquitetura e documentação  
> **Repositório alvo:** `guinatural/holocron-career-ai` (monorepo)

---

## Estratégia escolhida

Ver [[ESTRATEGIA-PORTFOLIO-PRATICIDADE|estratégia portfólio + praticidade]].

**Decisão:** SaaS desde o desenho (`tenant_id` em tudo), mas **execução local-first** na Fase 1 com Docker Compose. AWS produção entra na Fase 8+.

---

## Documentos

| Doc | Conteúdo |
|---|---|
| [[PRD-RESUMO-EXECUTIVO\|PRD — Resumo Executivo]] | Visão, objetivos, limites LGPD |
| [[ARQUITETURA\|Arquitetura Técnica]] | C4, AWS, componentes, sync/async |
| [[MODELO-DE-DADOS\|Modelo de Dados]] | Schema PostgreSQL, índices, migrações |
| [[FLUXOS-AGENTES\|Fluxos de Agentes]] | 8 agentes, contratos, sequências |
| [[ROADMAP\|Roadmap (8 Fases)]] | Ordem obrigatória + critérios de aceite |
| [[ADR-000-INDICE\|ADR — Índice]] | Decisões arquiteturais |
| [[OPENAPI-CONTRATOS\|OpenAPI / Contratos]] | Endpoints Fase 1 + schemas agentes |
| [[GUIA-DESENVOLVIMENTO-LOCAL\|Guia Dev Local]] | Docker Compose, comandos, testes |
| [[GUIA-VARIAVEIS-AMBIENTE\|Guia de Variáveis]] | `.env` por serviço |

---

## Integração com material existente

| Asset | Uso |
|---|---|
| [[../Freelance/CONTROLE_CANDIDATURAS\|CONTROLE_CANDIDATURAS]] | Import Fase 1 |
| [[../Freelance/PERFIL_LINKEDIN_SENIOR\|PERFIL_LINKEDIN]] | RAG Fase 3 |
| [[../../02 - ESTUDOS/ARCHITECT_SAA-C03/PDI_SAA-C03_CLOUD_JR\|PDI SAA-C03]] | Metas de carreira |
| Holocron Sentinel | Padrões de agentes, observabilidade, LGPD |

---

## Links externos (futuro)

- GitHub: `https://github.com/guinatural/holocron-career-ai`
- Swagger local: `http://localhost:8000/docs`
- Dashboard local: `http://localhost:3000`

---

#holocron #career-ai #saas #multiagent #portfolio #pdi
