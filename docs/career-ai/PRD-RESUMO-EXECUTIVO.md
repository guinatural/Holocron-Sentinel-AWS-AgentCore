# PRD — Resumo Executivo

## Produto

**Holocron Career AI** — plataforma SaaS multi-tenant que automatiza busca, análise, personalização e acompanhamento de candidaturas de emprego usando agentes de IA especializados.

## Problema

Profissionais Cloud/AI gastam 2–4h/dia em tarefas repetitivas: buscar vagas, adaptar currículo, rastrear status, preparar entrevistas — sem CRM, scoring objetivo ou aprendizado com resultados.

## Solução

Copiloto de carreira com:

- **CRM de pipeline** (11 estados)
- **Matching inteligente** (score 0–100 explicável)
- **Personalização de materiais** (sem inventar fatos)
- **Preparação para entrevistas** (técnica + STAR)
- **Analytics** (o que gera entrevista)
- **Governança LGPD** (auditoria, consentimento, retenção)

## Objetivos mensuráveis

| KPI | Primary | Secondary |
|---|---|---|
| Taxa de entrevista | ↑ principal | — |
| Taxa de resposta | — | ↑ |
| Taxa de oferta | — | long-term |
| Tempo/dia em busca | ↓ 50% | — |

## Usuário-alvo (MVP)

**Guilherme Barreto Gomes** — Cloud/AI Engineer em transição, certificado AWS CP, SAA-C03 em preparação.

**Futuro:** profissionais tech (Cloud, DevOps, AI, Security) no Brasil e remoto.

## Guardrails invioláveis

1. **Nunca inventar** experiências, certificações, datas ou resultados.
2. **Provenance:** toda alteração de CV/carta registra origem e diff.
3. **LGPD:** consentimento por tipo de dado; auditoria; direito ao esquecimento.
4. **Multi-tenant:** `tenant_id` em toda query; zero vazamento cross-tenant.
5. **Scraping:** apenas fontes permitidas (RSS, API, import manual).

## Fora de escopo (Fase 1)

- Agentes de IA
- Busca automática
- Billing Stripe
- Deploy AWS produção
- Application Agent (autofill)

## Integração Holocron

Extensão do ecossistema Holocron Sentinel — reutiliza padrões de agentes, observabilidade, MCP e compliance-by-design.

## Critério de sucesso do MVP (Fase 1)

CRM funcional substituindo `CONTROLE_CANDIDATURAS.md` com dashboard, CRUD testado e import de dados reais.
