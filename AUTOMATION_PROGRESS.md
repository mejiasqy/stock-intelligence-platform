# AUTOMATION_PROGRESS.md — Diário Operacional do Projeto

## 1. Identificação do projeto
- **Projeto:** Stock Intelligence Platform
- **Objetivo:** plataforma de análise de ações, ranking de ativos, backtesting e relatórios assistidos por IA para fins educacionais e de portfólio.
- **Documento mestre:** `PROJECT_CONTEXT.md`
- **Status geral:** Não iniciado
- **Sprint atual:** Sprint 0 — Fundação e governança
- **Última atualização:** 2026-06-23 — 12:00 (Bootstrap)
- **Responsável de implementação:** Claude Code sob direção do usuário
- **Regra de segurança:** o sistema não executa ordens de compra/venda e não oferece recomendação financeira.

---

## 2. Como atualizar este arquivo

Inclua estas regras explícitas:

1. Ler este arquivo e `PROJECT_CONTEXT.md` antes de iniciar qualquer nova sessão.
2. Atualizar este arquivo ao encerrar toda sessão, mesmo que não haja conclusão.
3. Não marcar uma tarefa como concluída sem evidência: comando executado, teste aprovado, validação manual ou arquivo inspecionado.
4. Registrar datas, arquivos alterados, comandos e resultados reais.
5. Não registrar chaves, tokens, senhas, URLs privadas ou outros segredos.
6. Quando houver bloqueio, registrar causa, impacto e próximo passo para destravar.
7. Quando houver decisão arquitetural, registrar a decisão e a justificativa.
8. Sempre manter uma única "Próxima tarefa recomendada", específica e verificável.
9. Preservar o histórico de sessões; nunca apagar registros anteriores.
10. Usar status apenas entre: `não iniciado`, `em andamento`, `bloqueado`, `concluído`, `validado`.

---

## 3. Estado atual por sprint

| Sprint | Objetivo | Status | Entregas concluídas | Pendências | Evidência de validação |
|---|---|---|---|---|---|
| Sprint 0 | Fundação e governança | não iniciado | — | Criar estrutura, ambiente, backend/frontend mínimos, CI, testes smoke e documentação base | — |
| Sprint 1 | Dados e banco | não iniciado | — | Modelagem, migrations e ingestão idempotente | — |
| Sprint 2 | Motor de indicadores | não iniciado | — | SMA, EMA, RSI, MACD, Bollinger e snapshots | — |
| Sprint 3 | Scoring e sinais | não iniciado | — | Score, ranking, reason codes e sinais explicáveis | — |
| Sprint 4 | Backtesting | não iniciado | — | Motor de backtest, métricas e auditoria | — |
| Sprint 5 | API profissional e segurança inicial | não iniciado | — | Contratos, documentação, validação e proteção inicial | — |
| Sprint 6 | Dashboard | não iniciado | — | Overview, watchlist, ativo e backtests | — |
| Sprint 7 | IA, relatórios e alertas | não iniciado | — | Relatórios seguros, fallback e alertas | — |
| Sprint 8 | Deploy, observabilidade e portfólio | não iniciado | — | CI completo, documentação, screenshots e entrega final | — |

---

## 4. Checklist da Sprint 0

- [ ] Estrutura inicial do repositório criada e revisada.
- [ ] `README.md` inicial criado.
- [ ] `.gitignore` criado e revisado.
- [ ] `.env.example` criado sem segredos.
- [ ] `docker-compose.yml` criado e validado.
- [ ] `Makefile` ou comandos equivalentes criados.
- [ ] Backend FastAPI inicial criado.
- [ ] Endpoint `/health` implementado e testado.
- [ ] Frontend Next.js inicial criado.
- [ ] Teste smoke do backend criado e aprovado.
- [ ] Lint, formatação e typecheck configurados.
- [ ] Pipeline de CI inicial criado.
- [ ] `CHANGELOG.md` inicial criado.
- [ ] Documentação técnica inicial criada.
- [ ] Validação completa da Sprint 0 executada.
- [ ] Sprint 0 encerrada e marcada como validada.

---

## 5. Registro de sessões

### Sessão 2026-06-23 — Bootstrap do tracker

- **Status da sessão:** concluído
- **Sprint e tarefa:** Sprint 0 — criação do arquivo de progresso
- **Objetivo da sessão:** estabelecer o controle de continuidade do projeto.
- **Arquivos criados:** `AUTOMATION_PROGRESS.md`
- **Arquivos alterados:** —
- **Arquivos removidos:** —
- **Decisões técnicas:** o arquivo de progresso será a fonte operacional de continuidade; `PROJECT_CONTEXT.md` continua sendo a fonte de verdade arquitetural. Ambos devem ser lidos antes de qualquer nova sessão.
- **Comandos executados:** nenhum comando necessário nesta etapa.
- **Testes e validações:** 
  - Confirmado que o arquivo foi criado na raiz do projeto.
  - Confirmado que segue a estrutura exigida no bootstrap.
  - Confirmado que nenhum código de produto foi alterado.
- **Resultado entregue:** tracker inicial criado e operacional.
- **Problemas, riscos ou bloqueios:** nenhum conhecido nesta etapa.
- **Pendências:** preparar plano de execução para Sprint 0.
- **Próxima tarefa recomendada:** inspecionar o repositório atual e apresentar um plano detalhado de implementação da Sprint 0, sem iniciar alterações até autorização do usuário.
- **Data/hora de encerramento:** 2026-06-23 — 12:00

---

## 6. Decisões arquiteturais

| ID | Data | Decisão | Justificativa | Impacto | Status |
|---|---|---|---|---|---|
| ADR-001 | 2026-06-23 | Usar `PROJECT_CONTEXT.md` como documento mestre e `AUTOMATION_PROGRESS.md` como registro operacional contínuo. | Evitar perda de contexto entre sessões e tornar decisões rastreáveis. Todo trabalho futuro deve consultar ambos antes de começar. | Estabelece fluxo de trabalho obrigatório; aumenta rastreabilidade e continuidade. | validado |

---

## 7. Riscos e bloqueios conhecidos

| ID | Tipo | Descrição | Impacto | Mitigação | Status |
|---|---|---|---|---|---|
| RISK-001 | Dados financeiros | Fontes públicas podem apresentar atraso, limites de chamadas, campos inconsistentes ou dados corrompidos. | Médio | Abstrair o provedor de dados em uma interface; validar dados na ingestão; informar indisponibilidade ao usuário. | aberto |
| RISK-002 | Qualidade analítica | Indicadores e backtests podem ser interpretados indevidamente como recomendação de investimento. | Alto | Disclaimers obrigatórios, explicabilidade de cada sinal, custo de transação realista e linguagem explicitamente não prescritiva. | aberto |
| RISK-003 | Continuidade | Sessões futuras podem perder contexto sobre decisões, pendências e estado técnico. | Médio | Atualização obrigatória de `AUTOMATION_PROGRESS.md` ao encerrar cada sessão; manutenção de histórico completo. | mitigado |

---

## 8. Próxima tarefa recomendada

- **Tarefa:** inspecionar o repositório atual e apresentar um plano de execução detalhado para a Sprint 0.
- **Pré-condições:** `PROJECT_CONTEXT.md` e `AUTOMATION_PROGRESS.md` devem existir na raiz; nenhum código de produto foi iniciado ainda.
- **Critério de conclusão:** plano com etapas sequenciais, arquivos previstos, comandos de validação, riscos conhecidos e clara indicação de que necessita confirmação do usuário antes de qualquer alteração.
- **Status:** não iniciado
- **Estimativa:** próxima sessão

---

**Fim do arquivo AUTOMATION_PROGRESS.md**
