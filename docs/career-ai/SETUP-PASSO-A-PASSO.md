# Setup Passo a Passo — No-Code

## Pré-requisitos

- [ ] Conta Airtable (grátis): https://airtable.com
- [ ] Conta Make.com (grátis): https://make.com
- [ ] Claude Pro (recomendado): https://claude.ai
- [ ] Telegram bot (opcional, alertas): @BotFather

---

## Passo 1 — Airtable (30 min)

1. Criar workspace **Holocron**
2. Criar base **Career AI**
3. Criar tabelas conforme [[AIRTABLE-BASE-DESIGN]]
4. Configurar Pipeline Status (11 estados)
5. Criar views: Inbox, Kanban Pipeline, Score ≥ 70
6. Import CSV das candidaturas atuais (copiar de CONTROLE_CANDIDATURAS)

---

## Passo 2 — Interface Dashboard (20 min)

1. Airtable → Interfaces → Create new
2. Adicionar blocos:
   - Record count: Applications
   - Record count: Jobs (Status = Inbox)
   - Kanban: Applications by Pipeline Status
   - Chart: Applications by Status
3. Publicar interface (bookmark no browser)

---

## Passo 3 — Claude Project (15 min)

1. claude.ai → Projects → New Project
2. Nome: `Holocron Career AI`
3. Anexar arquivos:
   - `Guilherme_Barreto_Gomes_CV.pdf`
   - `PERFIL_LINKEDIN_SENIOR.md`
   - `PDI_SAA-C03_CLOUD_JR.md`
   - README Holocron (opcional)
4. Colar instruções globais de [[CLAUDE-PROJECT-AGENTES]]
5. Testar prompt `/match` com uma vaga real

---

## Passo 4 — Make.com RSS (45 min)

1. Criar scenario **Holocron RSS Search**
2. Seguir [[MAKE-CENARIOS]] Cenário 1
3. Conectar Airtable OAuth
4. Testar manualmente (Run once)
5. Ativar schedule 07:00 daily

---

## Passo 5 — Telegram alertas (15 min, opcional)

1. Criar bot via @BotFather
2. Obter chat_id
3. Adicionar módulo Telegram no final do cenário RSS
4. Testar notificação

---

## Passo 6 — Ritual diário (5 min/dia)

```
07:00  Make importa vagas → checar Inbox Airtable
07:15  Triagem: Skip ou Review
07:30  Claude /match nas top 3
08:00  Aplicar + mover Kanban
08:05  Commit saa-c03-journey
```

---

## Passo 7 — Documentar no portfólio (30 min)

1. Screenshot Interface Airtable
2. Screenshot cenário Make.com
3. Exemplo output Claude /match (anonimizado)
4. Nota Obsidian linkando [[00 - INDEX - Holocron Career AI (No-Code)]]
5. Post LinkedIn: "Montei meu Career OS no-code integrado ao Holocron"

---

## Troubleshooting

| Problema | Solução |
|---|---|
| Airtable 1000 records limit | Arquivar Rejected/Skipped |
| Make ops esgotadas | Reduzir feeds RSS para 1 |
| Claude não anexa PDF grande | Usar versão MD do CV |
| RSS sem vagas BR | Filtrar keywords pós-import |

---

## Variáveis / credenciais (guardar no gerenciador de senhas)

| Serviço | Onde guardar |
|---|---|
| Airtable PAT | Make.com connection (não no Obsidian) |
| Anthropic API key | Make cenário 5 (se usar) |
| Telegram bot token | Make.com |
| Claude | Login normal |

**Nunca commitar tokens no GitHub.**
