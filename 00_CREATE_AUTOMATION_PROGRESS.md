# Prompt para Claude Code — Criar o arquivo de acompanhamento do projeto

> **Objetivo deste prompt:** criar o arquivo `AUTOMATION_PROGRESS.md`, que será a fonte de verdade operacional para manter continuidade entre sessões do Claude Code.

Copie e envie o conteúdo abaixo ao Claude Code no diretório raiz do projeto.

---

```text
Leia integralmente o arquivo PROJECT_CONTEXT.md antes de qualquer ação.

Sua tarefa agora é APENAS criar o arquivo `AUTOMATION_PROGRESS.md` na raiz do projeto. Não crie código de produto, não instale dependências, não altere banco de dados e não inicie nenhuma sprint de implementação ainda.

O arquivo AUTOMATION_PROGRESS.md deve funcionar como um diário operacional e checklist de continuidade entre sessões. Ele será lido obrigatoriamente antes de qualquer nova sessão de trabalho e atualizado no encerramento de toda seção de desenvolvimento.

Crie o arquivo com a estrutura abaixo, mantendo o conteúdo em português, claro, objetivo e auditável.

# AUTOMATION_PROGRESS.md

## 1. Identificação do projeto
- **Projeto:** Stock Intelligence Platform
- **Objetivo:** plataforma de análise de ações, ranking de ativos, backtesting e relatórios assistidos por IA para fins educacionais e de portfólio.
- **Documento mestre:** `PROJECT_CONTEXT.md`
- **Status geral:** Não iniciado
- **Sprint atual:** Sprint 0 — Fundação e governança
- **Última atualização:** [preencher com data e hora local atual]
- **Responsável de implementação:** Claude Code sob direção do usuário
- **Regra de segurança:** o sistema não executa ordens de compra/venda e não oferece recomendação financeira.

## 2. Como atualizar este arquivo
Inclua estas regras explícitas:

1. Ler este arquivo e `PROJECT_CONTEXT.md` antes de iniciar qualquer nova sessão.
2. Atualizar este arquivo ao encerrar toda sessão, mesmo que não haja conclusão.
3. Não marcar uma tarefa como concluída sem evidência: comando executado, teste aprovado, validação manual ou arquivo inspecionado.
4. Registrar datas, arquivos alterados, comandos e resultados reais.
5. Não registrar chaves, tokens, senhas, URLs privadas ou outros segredos.
6. Quando houver bloqueio, registrar causa, impacto e próximo passo para destravar.
7. Quando houver decisão arquitetural, registrar a decisão e a justificativa.
8. Sempre manter uma única “Próxima tarefa recomendada”, específica e verificável.
9. Preservar o histórico de sessões; nunca apagar registros anteriores.
10. Usar status apenas entre: `não iniciado`, `em andamento`, `bloqueado`, `concluído`, `validado`.

## 3. Estado atual por sprint
Crie uma tabela com as colunas:
- Sprint
- Objetivo
- Status
- Entregas concluídas
- Pendências
- Evidência de validação

Preencha inicialmente as seguintes linhas:

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

## 4. Checklist da Sprint atual
Crie esta seção inicialmente para Sprint 0, com todos os itens desmarcados:

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

## 5. Registro de sessões
Crie um modelo que deverá ser duplicado ao final de cada sessão:

### Sessão YYYY-MM-DD — Título objetivo
- **Status da sessão:** não iniciado / em andamento / concluído / bloqueado / validado
- **Sprint e tarefa:** Sprint X — nome da tarefa
- **Objetivo da sessão:**
- **Arquivos criados:**
- **Arquivos alterados:**
- **Arquivos removidos:**
- **Decisões técnicas:**
- **Comandos executados:**
  - `comando` → resultado real
- **Testes e validações:**
  - teste/validação → resultado real
- **Resultado entregue:**
- **Problemas, riscos ou bloqueios:**
- **Pendências:**
- **Próxima tarefa recomendada:** uma ação única, concreta e verificável.
- **Data/hora de encerramento:**

Após o modelo, crie o primeiro registro:

### Sessão inicial — Bootstrap do tracker
- **Status da sessão:** concluído
- **Sprint e tarefa:** Sprint 0 — criação do arquivo de progresso
- **Objetivo da sessão:** estabelecer o controle de continuidade do projeto.
- **Arquivos criados:** `AUTOMATION_PROGRESS.md`
- **Arquivos alterados:** —
- **Arquivos removidos:** —
- **Decisões técnicas:** o arquivo de progresso será a fonte operacional de continuidade; `PROJECT_CONTEXT.md` continua sendo a fonte de verdade arquitetural.
- **Comandos executados:** registrar apenas os comandos realmente executados; se nenhum comando foi necessário, escrever “Nenhum comando necessário”.
- **Testes e validações:** confirmar que o arquivo foi criado na raiz e segue a estrutura exigida.
- **Resultado entregue:** tracker inicial criado.
- **Problemas, riscos ou bloqueios:** nenhum conhecido nesta etapa.
- **Pendências:** iniciar a preparação da Sprint 0.
- **Próxima tarefa recomendada:** inspecionar o repositório e propor o plano de implementação da Sprint 0, sem iniciar alterações até autorização do usuário.
- **Data/hora de encerramento:** [preencher com data e hora local atual]

## 6. Decisões arquiteturais
Crie uma tabela com:
- ID
- Data
- Decisão
- Justificativa
- Impacto
- Status

Preencha inicialmente:
| ID | Data | Decisão | Justificativa | Impacto | Status |
|---|---|---|---|---|---|
| ADR-001 | [data atual] | Usar `PROJECT_CONTEXT.md` como documento mestre e `AUTOMATION_PROGRESS.md` como registro operacional contínuo. | Evitar perda de contexto entre sessões e tornar decisões rastreáveis. | Todo trabalho futuro deve consultar ambos antes de começar. | validado |

## 7. Riscos e bloqueios conhecidos
Crie uma tabela com:
- ID
- Tipo
- Descrição
- Impacto
- Mitigação
- Status

Preencha inicialmente:
| ID | Tipo | Descrição | Impacto | Mitigação | Status |
|---|---|---|---|---|---|
| RISK-001 | Dados financeiros | Fontes públicas podem apresentar atraso, limites ou campos inconsistentes. | Médio | Abstrair provedor, validar dados e informar indisponibilidade. | aberto |
| RISK-002 | Qualidade analítica | Indicadores e backtests podem ser interpretados indevidamente como recomendação financeira. | Alto | Disclaimers, explicabilidade, custos simulados e linguagem não prescritiva. | aberto |
| RISK-003 | Continuidade | Sessões futuras podem perder contexto sobre decisões e pendências. | Médio | Atualização obrigatória deste arquivo ao encerrar cada sessão. | mitigado |

## 8. Próxima tarefa recomendada
- **Tarefa:** inspecionar o repositório atual e apresentar um plano de execução para a Sprint 0.
- **Pré-condições:** `PROJECT_CONTEXT.md` e este arquivo devem existir na raiz.
- **Critério de conclusão:** plano com etapas, arquivos previstos, comandos de validação, riscos e necessidade de confirmação do usuário antes de editar.
- **Status:** não iniciado

Quando concluir a criação:
1. Mostre o caminho do arquivo criado.
2. Resuma a estrutura criada.
3. Confirme que nenhum código de produto foi alterado.
4. Não inicie a Sprint 0 automaticamente.
```
