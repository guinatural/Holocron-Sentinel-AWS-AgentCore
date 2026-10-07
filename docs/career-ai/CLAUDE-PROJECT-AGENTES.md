# Claude Project — 8 Agentes No-Code

> Crie um **Claude Project** chamado `Holocron Career AI`  
> Anexe: CV PDF, PERFIL_LINKEDIN, README Holocron, PDI SAA-C03

---

## Instruções globais do Project

```
Você é o Holocron Career AI — assistente de carreira do Guilherme Barreto Gomes.

REGRAS:
- NUNCA invente experiências, certificações, datas ou empresas.
- Só use fatos dos documentos anexados.
- Se faltar informação, diga "não consta no perfil" — não preencha.
- Respostas em português (BR).
- Formato: markdown estruturado.
- Guilherme busca: Cloud Engineer, Solutions Architect Jr, AI Engineer, Cloud Security.
- Stack: AWS, Python, Bedrock, Terraform, LGPD, Holocron Sentinel.
```

---

## Agent 1 — Search (manual)

**Quando usar:** busca pontual fora do RSS

**Prompt:**
```
/search
Keywords: {cloud aws junior remote brazil}
Liste 10 tipos de vagas ideais para meu perfil com:
- título sugerido
- seniority esperada
- 3 keywords ATS para cada
- plataforma recomendada para buscar
```

---

## Agent 2 — Matching

**Prompt:**
```
/match
---VAGA---
{colar descrição completa}
---FIM---

Retorne JSON:
{
  "score": 0-100,
  "recommendation": "apply|maybe|skip",
  "breakdown": {
    "hard_skills": {"score": N, "evidence": [], "gaps": []},
    "seniority": {...},
    "aws_alignment": {...},
    "location": {...},
    "salary": {...}
  },
  "explanation": "2-3 frases",
  "pitch_angle": "ângulo para cover letter"
}
```

Copiar score → Airtable campo Match Score.

---

## Agent 3 — Resume

**Prompt:**
```
/resume
Vaga: {título + empresa}
Match gaps: {gaps do matching}

Gere versão adaptada do CV:
1. Resumo (3 linhas)
2. Competências reordenadas (mais relevantes primeiro)
3. Projetos destacados (Holocron, Hack2Hire)
4. Keywords ATS (só dos meus fatos reais)

Inclua seção DIFF:
- o que mudou vs CV original
- facts_verified: true/false
```

---

## Agent 4 — Cover Letter

**Prompt:**
```
/cover
Empresa: {nome}
Vaga: {título}
Pitch angle: {do matching}

Gere:
1. Cover letter (≤ 250 palavras, específica, não genérica)
2. Mensagem LinkedIn (≤ 300 caracteres)
3. Email subject + body

Proibido: "venho por meio desta", "sou profissional dedicado"
```

---

## Agent 5 — Application Assist

**Prompt:**
```
/apply
URL ou descrição do formulário: {colar}

Checklist de preenchimento com:
- campo | valor sugerido | fonte no meu perfil
- perguntas extras que podem aparecer
- red flags da vaga
```

---

## Agent 6 — CRM (via Airtable)

Não usa Claude — Airtable nativo.  
Claude só para sugerir próxima ação:

**Prompt:**
```
/crm
Status atual: {pipeline status}
Último evento: {nota}
Empresa: {nome}

Sugira:
- próxima ação concreta
- prazo
- template de follow-up se aplicável
```

---

## Agent 7 — Interview Prep

**Prompt:**
```
/interview
Empresa: {nome}
Vaga: {título + descrição}
Tipo: {RH|Técnica|Case}

Gere prep pack:
1. 10 perguntas técnicas AWS prováveis + respostas baseadas no MEU perfil
2. 5 perguntas comportamentais STAR (com esboço de resposta)
3. 3 cenários arquitetura AWS para desenhar
4. 5 questões Python
5. Plano de estudo 48h (tópico | horas | recurso)
6. Checklist pré-entrevista
```

---

## Agent 8 — Learning

**Prompt semanal:**
```
/learn
Esta semana apliquei em: {lista}
Entrevistas: {lista}
Rejeições: {lista}

Analise padrões:
- o que correlaciona com entrevistas (não causalidade)
- keywords que aparecem nas vagas com resposta
- empresas/setores com melhor retorno
- 3 ajustes de estratégia para próxima semana
```

Registrar insights → nota Obsidian semanal.

---

## Atalhos recomendados

Salve cada prompt como **Snippet** no Claude ou template no Obsidian:

`01 - PROJETOS/Holocron/docs/career-ai/templates/`
