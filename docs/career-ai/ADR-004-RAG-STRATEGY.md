# ADR-004 — Estratégia RAG

**Status:** Aceito  
**Data:** 2026-07-30

## Contexto

Agentes precisam contexto do perfil (CV, LinkedIn, projetos) sem alucinar.

## Decisão

**Fase 3 (local):** ChromaDB + embeddings Bedrock Titan  
**Fase 8 (prod):** Amazon Bedrock Knowledge Base + OpenSearch Serverless

### Pipeline

1. Ingest: PDF/MD → chunk 512 tokens, overlap 64
2. Metadata: `tenant_id`, `doc_type`, `source`, `verified`, `updated_at`
3. Retrieve: top-k=5, filtro por tenant_id
4. Generate: prompt com sources[] obrigatório na resposta

### Documentos indexados (prioridade)

1. CV PDF
2. PERFIL_LINKEDIN_SENIOR.md
3. README Holocron + Hack2Hire
4. Certificações
5. CONTROLE_CANDIDATURAS.md (histórico)

## Consequências

- (+) Respostas grounded com citações
- (+) Migração path clara local→AWS
- (-) ChromaDB não é multi-tenant nativo → filtro manual por metadata

## Alternativas rejeitadas

| Alternativa | Motivo |
|---|---|
| Pinecone | Custo + vendor lock |
| Sem RAG | Alucinação inaceitável em CV |
| pgvector only | OK futuro, ChromaDB mais rápido para MVP |
