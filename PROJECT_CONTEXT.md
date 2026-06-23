# Stock Intelligence Platform — Documento Mestre do Projeto

> **Objetivo:** construir uma plataforma profissional de análise de ações, monitoramento de mercado, ranking de ativos, backtesting de estratégias e geração de relatórios assistidos por IA.  
> **Uso previsto:** projeto de portfólio/currículo, com qualidade de engenharia, documentação, testes e interface demonstrável.  
> **Importante:** este sistema é educacional e analítico. Ele **não executa ordens**, não promete rentabilidade e não deve ser apresentado como recomendação financeira.

---

## 1. Visão do produto

### 1.1 Nome provisório
**Stock Intelligence Platform**  
Alternativas futuras de marca: **MarketLens**, **AlphaScope**, **SignalForge** ou **Equity Intelligence OS**.

### 1.2 Problema que o produto resolve
Investidores e analistas precisam consultar diversas fontes, calcular indicadores, interpretar séries históricas, comparar ativos e acompanhar oportunidades. O objetivo desta plataforma é centralizar esse processo em um único sistema:

- coleta dados históricos de ativos;
- normaliza, valida e armazena séries de preço;
- calcula indicadores técnicos;
- classifica ativos por critérios transparentes;
- gera sinais explicáveis;
- permite testar estratégias em dados históricos;
- exibe resultados em dashboard;
- cria relatórios analíticos assistidos por IA;
- envia alertas informativos, sem executar negociações.

### 1.3 Diferencial para currículo
O projeto não deve parecer apenas “um script que usa `yfinance`”. Ele deve demonstrar competências de produto e engenharia:

- arquitetura em camadas;
- API REST documentada;
- banco relacional;
- processamento de dados;
- testes unitários e de integração;
- jobs agendados;
- dashboard responsivo;
- backtesting reproduzível;
- observabilidade;
- Docker;
- CI com GitHub Actions;
- documentação clara e decisões técnicas registradas.

---

## 2. Escopo e limites

### 2.1 O que entra no MVP profissional
1. Cadastro e monitoramento de uma watchlist de ativos.
2. Coleta de dados históricos diários.
3. Cálculo de indicadores técnicos.
4. Ranking de ativos por score configurável.
5. Geração de sinais analíticos explicáveis.
6. Backtesting de estratégias simples e auditáveis.
7. Dashboard com gráficos e páginas de detalhe.
8. API REST com documentação OpenAPI.
9. Relatórios analíticos por IA, baseados apenas em dados calculados pelo sistema.
10. Alertas informativos por Telegram ou e-mail.
11. Testes, documentação, Docker e pipeline de CI.

### 2.2 O que fica explicitamente fora do escopo inicial
- execução automática de compra/venda em corretoras;
- promessa de lucro ou previsão garantida;
- alta frequência;
- recomendações financeiras personalizadas;
- suporte a dinheiro real;
- scraping que infrinja termos de uso;
- uso da IA como fonte de números de mercado;
- armazenamento de chaves reais em arquivos versionados.

### 2.3 Regra de produto
Todo sinal deve ser apresentado como:

> **“Sinal analítico baseado em regras históricas. Não é recomendação de investimento.”**

---

## 3. Público e demonstração de portfólio

### 3.1 Público-alvo demonstrativo
- investidores que querem estudar análise técnica;
- estudantes de dados/finanças;
- recrutadores avaliando capacidade full-stack, dados e IA;
- pequenos analistas que precisam comparar ativos.

### 3.2 Cenário de demonstração
Um usuário abre a plataforma, visualiza sua watchlist, escolhe um ativo e vê:

- preço e variação recente;
- gráfico de candles/linha;
- volume;
- SMA, EMA, RSI, MACD e Bandas de Bollinger;
- score de oportunidade;
- explicação objetiva dos fatores que elevaram ou reduziram o score;
- resultado de backtest da estratégia escolhida;
- aviso de risco e limitações.

---

## 4. Stack recomendada

A stack deve ser moderna, mas proporcional ao projeto. Não adicionar complexidade sem benefício claro.

### 4.1 Backend e análise
- **Python 3.12+**
- **FastAPI** para API REST
- **Pydantic** para validação e contratos
- **SQLAlchemy 2.x** para ORM
- **Alembic** para migrations
- **Pandas** para manipulação de séries
- **NumPy** para cálculos numéricos
- **pandas-ta** ou implementação própria para indicadores
- **httpx** para clientes HTTP
- **APScheduler** para jobs simples no MVP
- **pytest**, **pytest-asyncio**, **coverage** para testes
- **Ruff**, **Black** e **mypy** para qualidade de código

### 4.2 Banco e infraestrutura
- **PostgreSQL** como banco principal
- **Supabase** pode hospedar PostgreSQL e autenticação posteriormente
- **Redis** apenas quando houver necessidade real de cache/fila; não é obrigatório no início
- **Docker Compose** para ambiente local reproduzível
- variáveis de ambiente em `.env`, com `.env.example` versionado

### 4.3 Frontend
Escolher apenas uma opção na fase de implementação:

**Opção recomendada para currículo full-stack**
- **Next.js + TypeScript**
- Tailwind CSS
- TanStack Query
- Recharts ou Lightweight Charts
- shadcn/ui ou componentes próprios

**Opção alternativa para entrega mais rápida**
- Streamlit

> Para este projeto, priorizar **Next.js + FastAPI**. Streamlit pode ser usado apenas em protótipos internos, não como dashboard final.

### 4.4 IA e relatórios
- Provedor de LLM configurável por variável de ambiente.
- A IA recebe somente contexto estruturado produzido pelo sistema: métricas, scores, indicadores, riscos, mudanças e limitações.
- A IA não deve inventar preços, retornos, notícias nem recomendar compra/venda.
- Todo texto de IA deve ser marcado como “insight automatizado”.

### 4.5 Dados de mercado
Começar com um adaptador de dados histórico para demonstração. A implementação deve ficar desacoplada para permitir trocar de fonte depois.

Interface conceitual:

```python
class MarketDataProvider(Protocol):
    async def fetch_daily_history(
        self,
        symbol: str,
        start: date,
        end: date,
    ) -> list[OHLCVRecord]:
        ...
```

Possíveis provedores:
- fonte pública para protótipo histórico;
- API comercial/licenciada no futuro;
- fonte específica para mercado brasileiro quando necessário.

**Regra:** nenhum módulo de domínio pode depender diretamente de uma biblioteca específica de dados.

---

## 5. Arquitetura do sistema

### 5.1 Princípios
1. **Separação de responsabilidades:** coleta, domínio, API, banco, jobs e UI não devem ficar misturados.
2. **Testabilidade:** lógica de indicadores, sinais, scoring e backtest deve ser pura sempre que possível.
3. **Auditabilidade:** todo score e sinal precisa guardar fatores de origem.
4. **Reprodutibilidade:** backtest deve registrar parâmetros, período e custos simulados.
5. **Fail closed:** na ausência de dados confiáveis, o sistema deve devolver estado “dados insuficientes”, não inventar análise.
6. **Segurança por padrão:** segredos fora do Git e validação em todas as entradas.
7. **Evolução incremental:** cada sprint deve produzir algo executável e validado.

### 5.2 Arquitetura em alto nível

```text
                        ┌──────────────────────────────┐
                        │     Mercado / Data Provider   │
                        └───────────────┬──────────────┘
                                        │
                         ┌──────────────▼──────────────┐
                         │    Data Ingestion Service    │
                         │ normalização + validações    │
                         └───────────────┬──────────────┘
                                        │
             ┌──────────────────────────▼──────────────────────────┐
             │                    PostgreSQL                       │
             │ assets | OHLCV | indicators | signals | backtests   │
             └──────────────────────────┬──────────────────────────┘
                                        │
          ┌─────────────────────────────▼──────────────────────────────┐
          │                    Analysis Domain                         │
          │ indicadores | scoring | sinais | risco | backtesting       │
          └─────────────────────┬───────────────────────┬──────────────┘
                                │                       │
                 ┌──────────────▼─────────────┐ ┌──────▼──────────────┐
                 │        FastAPI REST API     │ │  Scheduler / Alerts  │
                 │ Auth futura + OpenAPI       │ │  Telegram / e-mail   │
                 └──────────────┬──────────────┘ └─────────────────────┘
                                │
                     ┌──────────▼──────────┐
                     │  Next.js Dashboard  │
                     └─────────────────────┘
```

### 5.3 Estrutura recomendada do repositório

```text
stock-intelligence-platform/
├── README.md
├── PROJECT_CONTEXT.md
├── AUTOMATION_PROGRESS.md              # criado pelo prompt de bootstrap
├── CHANGELOG.md
├── CONTRIBUTING.md
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Makefile
├── backend/
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── routers/
│   │   │   └── dependencies.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── logging.py
│   │   │   └── security.py
│   │   ├── db/
│   │   │   ├── base.py
│   │   │   ├── session.py
│   │   │   ├── models/
│   │   │   └── migrations/
│   │   ├── domain/
│   │   │   ├── market_data/
│   │   │   ├── indicators/
│   │   │   ├── signals/
│   │   │   ├── scoring/
│   │   │   ├── backtesting/
│   │   │   └── reports/
│   │   ├── services/
│   │   │   ├── ingestion_service.py
│   │   │   ├── analysis_service.py
│   │   │   ├── backtest_service.py
│   │   │   └── alert_service.py
│   │   ├── providers/
│   │   │   ├── market_data/
│   │   │   └── llm/
│   │   ├── jobs/
│   │   └── schemas/
│   └── tests/
│       ├── unit/
│       ├── integration/
│       └── fixtures/
├── frontend/
│   ├── package.json
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── features/
│   │   ├── lib/
│   │   └── types/
│   └── public/
├── docs/
│   ├── architecture.md
│   ├── api.md
│   ├── data-model.md
│   ├── decisions/
│   ├── screenshots/
│   └── runbook.md
└── scripts/
    ├── seed_demo_data.py
    └── verify_environment.py
```

---

## 6. Modelo de dados

### 6.1 Entidades essenciais

#### `assets`
Representa o ativo monitorado.
- `id`
- `symbol`
- `exchange`
- `display_name`
- `asset_type`
- `currency`
- `is_active`
- `created_at`
- `updated_at`

#### `price_bars`
Série OHLCV normalizada.
- `id`
- `asset_id`
- `timeframe` (`1d` no MVP)
- `timestamp`
- `open`
- `high`
- `low`
- `close`
- `adjusted_close`
- `volume`
- `source`
- `ingested_at`

Índice único recomendado: `(asset_id, timeframe, timestamp, source)`.

#### `indicator_snapshots`
Snapshot calculado de indicadores.
- `id`
- `asset_id`
- `timestamp`
- `timeframe`
- `sma_20`
- `sma_50`
- `ema_20`
- `rsi_14`
- `macd`
- `macd_signal`
- `macd_histogram`
- `bollinger_upper`
- `bollinger_middle`
- `bollinger_lower`
- `calculation_version`
- `created_at`

#### `signals`
Resultado explicável de regras.
- `id`
- `asset_id`
- `timestamp`
- `signal_type` (`bullish`, `bearish`, `neutral`, `insufficient_data`)
- `strength` (`weak`, `moderate`, `strong`)
- `score`
- `reason_codes`
- `explanation`
- `strategy_version`
- `created_at`

#### `strategy_configs`
Configurações versionadas para estratégias e backtests.
- `id`
- `name`
- `version`
- `parameters_json`
- `description`
- `is_active`
- `created_at`

#### `backtest_runs`
Registro reproduzível de cada execução.
- `id`
- `strategy_config_id`
- `asset_id`
- `started_at`
- `ended_at`
- `initial_capital`
- `final_equity`
- `total_return_pct`
- `max_drawdown_pct`
- `sharpe_ratio`
- `win_rate_pct`
- `trade_count`
- `transaction_cost_bps`
- `slippage_bps`
- `parameters_snapshot_json`
- `engine_version`
- `created_at`

#### `backtest_trades`
Operações simuladas dentro de um backtest.
- `id`
- `backtest_run_id`
- `entry_timestamp`
- `exit_timestamp`
- `entry_price`
- `exit_price`
- `quantity`
- `gross_pnl`
- `net_pnl`
- `reason_entry`
- `reason_exit`

#### `watchlists` e `watchlist_items`
Organização de ativos do usuário ou da demonstração.

#### `report_runs`
Relatórios gerados e seus metadados.
- `id`
- `asset_id`
- `report_type`
- `input_snapshot_json`
- `generated_text`
- `model_name`
- `created_at`

### 6.2 Migrações
- Nunca alterar schema manualmente em produção.
- Toda mudança estrutural deve gerar migration Alembic.
- A migration deve ser revisada e testada em banco vazio.
- A cada sprint com mudança de banco, atualizar `docs/data-model.md`.

---

## 7. Indicadores e lógica de análise

### 7.1 Indicadores do MVP
Implementar e testar:

1. **SMA 20 e SMA 50**
2. **EMA 20**
3. **RSI 14**
4. **MACD (12, 26, 9)**
5. **Bandas de Bollinger (20, 2)**
6. **Volume médio de 20 períodos**
7. **Retorno de 1, 5, 20 e 60 períodos**
8. **Volatilidade anualizada**
9. **Máxima queda (drawdown) da janela selecionada**

### 7.2 Regras de qualidade para indicadores
- Definir quantidade mínima de candles por indicador.
- Caso haja histórico insuficiente, retornar `null` e um estado explícito.
- Não preencher dados faltantes silenciosamente.
- Não calcular indicador com séries desalinhadas.
- Arredondamento apenas na camada de apresentação; cálculos mantêm precisão.

### 7.3 Score analítico inicial
O score deve ser transparente, entre `0` e `100`.

Exemplo de composição configurável:

| Pilar | Peso inicial | Exemplo de evidência |
|---|---:|---|
| Tendência | 30 | preço acima de médias, inclinação das médias |
| Momentum | 25 | RSI e MACD |
| Volume | 15 | volume acima da média |
| Volatilidade/Risco | 15 | volatilidade e drawdown |
| Estrutura de preço | 15 | posição nas Bandas de Bollinger |

Regras:
- O score é um mecanismo de ranking, não recomendação.
- Cada contribuição deve gerar um `reason_code`.
- O dashboard deve exibir os fatores positivos e negativos.
- Pesos e thresholds pertencem a uma versão de estratégia.

### 7.4 Sinais iniciais
Exemplos de estados:
- `bullish`
- `bearish`
- `neutral`
- `insufficient_data`

Exemplo de classificação:
- **Bullish moderado:** SMA 20 acima da SMA 50, MACD positivo e RSI entre 50 e 70.
- **Bearish moderado:** SMA 20 abaixo da SMA 50, MACD negativo e RSI abaixo de 50.
- **Neutral:** evidências conflitantes ou falta de confirmação.
- **Insufficient data:** histórico ou campos necessários indisponíveis.

Não chamar um sinal de “compre” ou “venda” no MVP.

---

## 8. Backtesting profissional e responsável

### 8.1 Objetivo
Validar como uma regra teria se comportado em dados passados, sem sugerir que o resultado se repetirá.

### 8.2 Requisitos mínimos
- períodos configuráveis;
- capital inicial configurável;
- custos de transação simulados;
- slippage configurável;
- sem uso de dados futuros;
- operações registradas;
- curva de patrimônio;
- benchmark simples;
- métricas claras;
- seed de dados e parâmetros registrados.

### 8.3 Métricas
- retorno total;
- retorno anualizado;
- volatilidade;
- Sharpe ratio;
- maximum drawdown;
- win rate;
- profit factor;
- número de trades;
- exposição ao mercado;
- comparação com buy-and-hold.

### 8.4 Proteções contra resultados enganosos
- não usar dados futuros acidentalmente (look-ahead bias);
- não otimizar parâmetros com todo o período e apresentar como previsão;
- incluir custos e slippage;
- separar período de validação e teste quando aplicável;
- exibir amostra insuficiente;
- registrar versão da estratégia e parâmetros;
- colocar disclaimer de que performance passada não garante resultado futuro.

---

## 9. API REST

### 9.1 Convenções
- prefixo `/api/v1`;
- JSON em `snake_case`;
- mensagens de erro padronizadas;
- paginação em endpoints de lista;
- validação com Pydantic;
- OpenAPI disponível automaticamente;
- versionamento explícito;
- testes de contrato para endpoints principais.

### 9.2 Endpoints iniciais

```text
GET    /api/v1/health
GET    /api/v1/assets
POST   /api/v1/assets
GET    /api/v1/assets/{symbol}
GET    /api/v1/assets/{symbol}/prices
GET    /api/v1/assets/{symbol}/analysis
GET    /api/v1/assets/{symbol}/signals
GET    /api/v1/rankings
POST   /api/v1/ingestion/run
POST   /api/v1/backtests/run
GET    /api/v1/backtests/{run_id}
GET    /api/v1/backtests/{run_id}/trades
POST   /api/v1/reports/generate
GET    /api/v1/watchlists
POST   /api/v1/watchlists
```

### 9.3 Segurança
No MVP local:
- proteger endpoints mutáveis com uma chave administrativa simples em variável de ambiente, se necessário;
- não expor dados sensíveis em erros;
- limitar CORS aos ambientes permitidos.

Fase posterior:
- autenticação via Supabase Auth/JWT;
- usuários e watchlists privadas;
- rate limiting;
- auditoria de ações relevantes.

---

## 10. Dashboard

### 10.1 Páginas
1. **Overview**
   - KPIs de mercado monitorado
   - ranking de ativos
   - últimas atualizações
   - disclaimer visível

2. **Watchlist**
   - tabela de ativos
   - score, sinal, preço, variação, volatilidade
   - filtros por mercado, score e sinal

3. **Detalhe do ativo**
   - gráfico de preço
   - indicadores sobrepostos
   - cards de métricas
   - explicação do score
   - linha do tempo de sinais
   - relatório por IA
   - botão de executar backtest

4. **Backtests**
   - lista de execuções
   - configuração de estratégia
   - curva de patrimônio
   - métricas e trades simulados
   - comparação com buy-and-hold

5. **Configurações**
   - parâmetros de score
   - escolha de ativos
   - preferências de alerta
   - status das fontes de dados

### 10.2 Direção visual
- linguagem visual de terminal financeiro moderno, sem excesso de elementos;
- fundo escuro premium;
- dados em destaque e boa hierarquia;
- cores sem depender apenas de vermelho/verde;
- responsivo;
- acessibilidade mínima: contraste, labels e navegação por teclado.

### 10.3 Estados obrigatórios
Toda página deve considerar:
- carregando;
- vazio;
- erro;
- dados insuficientes;
- sucesso;
- fonte indisponível.

---

## 11. IA para relatórios

### 11.1 Uso correto
A IA será usada para converter dados estruturados em linguagem humana.

Entrada exemplo:

```json
{
  "symbol": "EXAMPLE",
  "as_of": "2026-06-23",
  "score": 72,
  "signal": "bullish",
  "indicators": {
    "rsi_14": 58.2,
    "macd_histogram": 1.23,
    "sma_20": 100.4,
    "sma_50": 95.1
  },
  "risk": {
    "annualized_volatility": 0.31,
    "max_drawdown_60d": -0.12
  },
  "reason_codes": [
    "price_above_sma_20",
    "sma_20_above_sma_50",
    "volume_above_average"
  ]
}
```

### 11.2 Regras para prompt de IA
A IA deve:
- explicar apenas o que recebeu;
- mencionar limitações;
- não inventar preços, eventos ou notícias;
- não afirmar certeza;
- não dizer “compre” ou “venda”;
- retornar seções consistentes: resumo, fatores, riscos e dados insuficientes;
- usar tom analítico e educativo.

### 11.3 Fallback
Se a IA falhar:
- salvar falha no log;
- mostrar uma explicação determinística baseada em `reason_codes`;
- não bloquear o restante do dashboard.

---

## 12. Jobs e alertas

### 12.1 Jobs iniciais
1. Atualização diária de dados.
2. Recalcular indicadores após ingestão.
3. Gerar score e sinais.
4. Atualizar ranking.
5. Verificar regras de alerta.
6. Gerar relatório diário opcional.

### 12.2 Alertas
Começar com Telegram **ou** e-mail, não ambos na primeira implementação.

Exemplo de alerta:
- ativo entrou no top 10 do ranking;
- score variou mais de X pontos;
- sinal mudou de neutral para bullish/bearish;
- ingestão falhou;
- dados estão desatualizados.

Todo alerta deve conter:
- data/hora;
- ativo;
- resumo objetivo;
- link para dashboard;
- disclaimer.

### 12.3 Idempotência
Jobs não devem duplicar:
- candles já armazenados;
- snapshots para o mesmo ativo/período/versão;
- alertas para a mesma condição dentro da janela configurada.

---

## 13. Observabilidade e qualidade

### 13.1 Logs
Logs estruturados devem incluir:
- `request_id`;
- serviço/módulo;
- operação;
- ativo;
- duração;
- status;
- erro sanitizado.

Nunca registrar:
- chaves de API;
- tokens;
- senhas;
- conteúdo sensível integral.

### 13.2 Métricas técnicas
No mínimo, registrar:
- sucesso/falha de ingestão;
- quantidade de candles processados;
- tempo de cálculo de análise;
- tempo de endpoint;
- quantidade de alertas enviados;
- falhas de provedor.

### 13.3 Health checks
Criar:
- `GET /health` para processo vivo;
- `GET /ready` para dependências essenciais.

---

## 14. Testes e gates de qualidade

### 14.1 Pirâmide de testes
- **Unitários:** indicadores, score, regras de sinais, backtesting.
- **Integração:** banco, migrations, ingestão e endpoints.
- **End-to-end básico:** fluxo de listar ativo → abrir análise → executar backtest.

### 14.2 Cobertura e qualidade
Meta progressiva:
- fase inicial: testes dos módulos críticos;
- antes do portfólio: cobertura significativa dos domínios de cálculo;
- CI precisa falhar se lint, typecheck ou testes falharem.

### 14.3 Comandos padronizados
O projeto deve oferecer comandos simples, idealmente via `Makefile`:

```bash
make setup
make dev
make test
make lint
make format
make typecheck
make migrate
make seed
make verify
```

### 14.4 Definition of Done para qualquer tarefa
Uma tarefa só pode ser marcada como concluída quando:
1. requisito funcional entregue;
2. testes adicionados/atualizados;
3. lint e typecheck aprovados;
4. documentação afetada atualizada;
5. comportamento validado manualmente quando houver UI;
6. status registrado em `AUTOMATION_PROGRESS.md`;
7. não houver segredo versionado.

---

## 15. Sprints de implementação

> **Regra:** executar uma sprint por vez. Não pular para interface avançada antes de a fundação estar validada.

### Sprint 0 — Fundação e governança
**Objetivo:** criar repositório limpo, documentação, ambiente e regras de trabalho.

Entregas:
- estrutura inicial do repositório;
- `PROJECT_CONTEXT.md`;
- `AUTOMATION_PROGRESS.md`;
- `README.md` inicial;
- `.gitignore`, `.env.example`, `docker-compose.yml`;
- `Makefile`;
- backend FastAPI com `/health`;
- frontend Next.js mínimo;
- CI básico;
- testes smoke;
- verificação de ambiente.

Critérios de aceite:
- `docker compose up` sobe dependências;
- backend responde health check;
- frontend inicia;
- lint e testes básicos passam;
- progresso inicial registrado.

### Sprint 1 — Dados e banco
**Objetivo:** modelar banco e ingerir séries históricas de forma idempotente.

Entregas:
- entidades `assets` e `price_bars`;
- migrations Alembic;
- adaptador de fonte de dados;
- normalização de OHLCV;
- serviço de ingestão;
- seed de ativos de demonstração;
- endpoint de consulta de preços;
- testes para duplicidade, dados inválidos e histórico vazio.

Critérios de aceite:
- dado histórico é salvo corretamente;
- segunda ingestão não duplica registros;
- fonte indisponível gera erro controlado;
- documentação do modelo de dados atualizada.

### Sprint 2 — Motor de indicadores
**Objetivo:** calcular e persistir indicadores com dados confiáveis.

Entregas:
- SMA, EMA, RSI, MACD e Bollinger;
- snapshots de indicadores;
- endpoint `/analysis`;
- validação de histórico mínimo;
- testes de valores esperados com fixtures conhecidas.

Critérios de aceite:
- valores batem com fixtures e cálculos de referência;
- dados insuficientes têm estado explícito;
- nenhum cálculo gera NaN exposto sem tratamento.

### Sprint 3 — Scoring e sinais explicáveis
**Objetivo:** gerar ranking transparente e sinais não prescritivos.

Entregas:
- módulo de score versionado;
- `reason_codes`;
- tabela de sinais;
- ranking;
- endpoint `/rankings`;
- explicação determinística dos fatores;
- testes de regras e casos conflitantes.

Critérios de aceite:
- score sempre entre 0 e 100;
- cada sinal possui justificativa;
- ranking ordena corretamente;
- casos sem dados retornam `insufficient_data`.

### Sprint 4 — Backtesting
**Objetivo:** testar estratégia em histórico, com auditabilidade.

Entregas:
- motor de backtest;
- custos e slippage simulados;
- curva de patrimônio;
- métricas;
- registros de operações;
- endpoint para executar e consultar backtests;
- comparação buy-and-hold;
- testes contra look-ahead bias.

Critérios de aceite:
- parâmetros ficam registrados;
- trades e métricas podem ser reproduzidos;
- custo afeta resultado conforme esperado;
- documentação explica limitações.

### Sprint 5 — API profissional e segurança inicial
**Objetivo:** estabilizar contratos e preparar integração com frontend.

Entregas:
- rotas versionadas;
- paginação;
- erros padronizados;
- OpenAPI revisado;
- CORS configurado;
- validação de entrada;
- rate limit simples, se necessário;
- testes de integração de API.

Critérios de aceite:
- endpoints documentados e testados;
- nenhuma rota mutável fica aberta acidentalmente;
- respostas de erro não expõem detalhes internos.

### Sprint 6 — Dashboard
**Objetivo:** entregar experiência visual de portfólio.

Entregas:
- overview;
- watchlist;
- detalhe de ativo;
- gráficos;
- visualização de score e sinais;
- estados de carregamento/erro/vazio;
- página de backtests;
- responsividade mínima.

Critérios de aceite:
- dashboard consome dados reais da API;
- métricas são coerentes com API;
- telas funcionam em desktop e mobile básico;
- screenshots salvos em `docs/screenshots/`.

### Sprint 7 — IA, relatórios e alertas
**Objetivo:** incorporar IA de forma segura e diferenciada.

Entregas:
- provider de LLM desacoplado;
- prompt versionado;
- relatório baseado em JSON estruturado;
- fallback determinístico;
- alerta por um canal;
- job agendado;
- logs e tratamento de falhas.

Critérios de aceite:
- IA não inventa dados em testes de segurança;
- alerta não duplica;
- falha de IA não derruba análise;
- disclaimer presente.

### Sprint 8 — Deploy, observabilidade e portfólio
**Objetivo:** finalizar produto demonstrável.

Entregas:
- Docker revisado;
- CI completo;
- documentação de deploy;
- logs e health checks;
- README de alto nível;
- arquitetura e decisões técnicas;
- screenshots/GIF curto;
- dados de demonstração;
- checklist de segurança;
- apresentação de projeto para currículo.

Critérios de aceite:
- projeto reproduzível em máquina limpa;
- CI verde;
- deploy de demonstração funcional, se escolhido;
- README permite avaliador iniciar o projeto;
- documentação de limitações e ética financeira concluída.

---

## 16. Regras obrigatórias para Claude Code

### 16.1 Antes de alterar código
1. Ler `PROJECT_CONTEXT.md`.
2. Ler `AUTOMATION_PROGRESS.md`.
3. Confirmar sprint e tarefa atual.
4. Inspecionar estrutura e arquivos existentes.
5. Não assumir que uma feature existe sem verificar.
6. Propor plano curto da sessão antes de implementar.

### 16.2 Durante a implementação
- Trabalhar em tarefas pequenas e verificáveis.
- Não substituir arquivos inteiros sem necessidade.
- Preservar código e documentação existente.
- Preferir módulos puros para regras de negócio.
- Criar ou atualizar testes junto da implementação.
- Executar comandos de validação reais.
- Não afirmar que algo foi validado sem executar o comando.
- Não expor segredos.
- Não adicionar bibliotecas sem justificar em documentação ou PR/commit.

### 16.3 Ao encerrar uma sessão/sprint
1. Executar testes, lint e typecheck aplicáveis.
2. Registrar comandos executados e resultado.
3. Atualizar documentação afetada.
4. Atualizar `CHANGELOG.md` quando houver entrega relevante.
5. Atualizar `AUTOMATION_PROGRESS.md` conforme o protocolo abaixo.
6. Informar pendências e próximo passo concreto.

---

## 17. Protocolo do arquivo `AUTOMATION_PROGRESS.md`

O arquivo de progresso é a fonte operacional de continuidade entre sessões.

### 17.1 Atualizar sempre que
- uma sessão de trabalho for encerrada;
- uma tarefa for concluída;
- uma tarefa falhar ou ficar bloqueada;
- uma decisão técnica mudar;
- uma migration for aplicada;
- uma dependência importante for adicionada;
- uma sprint for iniciada ou encerrada.

### 17.2 O que registrar
- data/hora;
- sprint atual;
- status;
- itens concluídos;
- arquivos criados/alterados;
- migrations aplicadas;
- comandos executados e resultados;
- testes realizados;
- decisões;
- riscos, bugs e bloqueios;
- próximo passo único e acionável.

### 17.3 O que nunca registrar
- segredos;
- valores de tokens/chaves;
- dados pessoais sensíveis;
- afirmações sem evidência;
- tarefas vagas como “continuar projeto”.

---

## 18. Git e fluxo de trabalho

### 18.1 Branches
- `main`: sempre estável.
- `develop`: integração, se necessário.
- `feature/<sprint>-<descricao>`: desenvolvimento de cada feature.
- `fix/<descricao>`: correções.

Para começar sozinho, pode usar `main` com commits pequenos, desde que CI esteja verde.

### 18.2 Commits
Formato recomendado:

```text
feat(ingestion): add idempotent daily price ingestion
test(indicators): cover RSI insufficient-history case
docs(backtesting): document transaction-cost assumptions
fix(api): return explicit insufficient-data state
```

### 18.3 Pull requests
Mesmo em projeto pessoal, usar PRs pode fortalecer portfólio:
- resumo;
- motivação;
- testes;
- screenshots;
- riscos;
- checklist.

---

## 19. README final esperado

O README final precisa conter:
1. descrição do projeto;
2. principais funcionalidades;
3. arquitetura;
4. stack;
5. screenshots;
6. como executar localmente;
7. variáveis de ambiente;
8. comandos úteis;
9. testes;
10. limitações;
11. disclaimer financeiro;
12. roadmap;
13. decisões técnicas;
14. créditos/fontes de dados;
15. licença.

---

## 20. Critérios de conclusão do projeto

O projeto será considerado pronto para currículo quando:
- dashboard exibir dados reais ou de demonstração de forma consistente;
- API estiver documentada;
- ingestão, indicadores, score, sinais e backtesting funcionarem ponta a ponta;
- alertas ou relatório de IA estiverem integrados com fallback;
- testes críticos estiverem verdes;
- ambiente subir via documentação;
- não existirem chaves no Git;
- README e documentação estiverem completos;
- screenshots e/ou vídeo curto demonstrem a aplicação;
- limitações e disclaimer estejam explícitos.

---

## 21. Prompt de início sugerido para Claude Code

Copie este comando ao abrir o projeto pela primeira vez:

```text
Leia integralmente PROJECT_CONTEXT.md. Em seguida, localize e leia AUTOMATION_PROGRESS.md. Trabalhe apenas na sprint e na próxima tarefa indicada no arquivo de progresso.

Antes de editar qualquer arquivo:
1. Resuma o estado atual encontrado.
2. Liste o plano de execução da sessão em etapas pequenas.
3. Identifique riscos, dependências e critérios de aceite.
4. Aguarde minha confirmação caso a mudança envolva arquitetura, novas dependências relevantes, banco de dados, custos externos ou qualquer integração com conta real.

Durante a sessão:
- implemente de forma incremental;
- escreva/atualize testes;
- execute validações reais;
- preserve a arquitetura definida;
- não invente resultados;
- não use nem solicite segredos no código.

Ao terminar:
- apresente arquivos alterados;
- mostre comandos executados e resultados;
- atualize AUTOMATION_PROGRESS.md seguindo o protocolo deste documento;
- deixe um próximo passo único, específico e verificável.
```

---

## 22. Próximo passo imediato

1. Criar o repositório `stock-intelligence-platform`.
2. Adicionar este arquivo como `PROJECT_CONTEXT.md`.
3. Adicionar o arquivo `00_CREATE_AUTOMATION_PROGRESS.md`.
4. Abrir o repositório no Claude Code.
5. Executar o prompt do arquivo `00_CREATE_AUTOMATION_PROGRESS.md`.
6. Depois de criado o tracker, iniciar a **Sprint 0 — Fundação e governança**.
