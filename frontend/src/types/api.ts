// Tipos derivados dos contratos reais da API (Sprint 5).
// Não adicionar campos que não existam nos schemas do backend.

// ---------------------------------------------------------------------------
// Envelope genérico
// ---------------------------------------------------------------------------

export interface PaginationMeta {
  limit: number;
  offset: number;
  total: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  pagination: PaginationMeta;
}

export interface ApiErrorDetail {
  code: string;
  message: string;
  request_id: string | null;
  fields?: Array<{ field: string; message: string; type: string }>;
}

export interface ApiErrorEnvelope {
  error: ApiErrorDetail;
}

// ---------------------------------------------------------------------------
// Assets — GET /api/v1/assets
// ---------------------------------------------------------------------------

export interface Asset {
  id: number;
  symbol: string;
  name: string;
  exchange: string;
  asset_type: string;
  created_at: string;
}

// ---------------------------------------------------------------------------
// PriceBar — GET /api/v1/assets/{symbol}/prices
// ---------------------------------------------------------------------------

export interface PriceBar {
  id: number;
  asset_id: number;
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

// ---------------------------------------------------------------------------
// IndicatorSnapshot — GET /api/v1/assets/{symbol}/analysis
// ---------------------------------------------------------------------------

export interface IndicatorSnapshot {
  id: number;
  asset_id: number;
  timeframe: string;
  source: string;
  calculated_at: string;
  calculation_version: string;
  candles_used: number;
  status: string; // "ok" | "insufficient_data" | etc.

  // Todos os campos de indicadores são nullable
  sma_20: number | null;
  sma_50: number | null;
  ema_20: number | null;
  rsi_14: number | null;
  macd: number | null;
  macd_signal: number | null;
  macd_histogram: number | null;
  bollinger_upper: number | null;
  bollinger_middle: number | null;
  bollinger_lower: number | null;
  volume_avg_20: number | null;
  last_volume: number | null;
  last_close: number | null;
  vol_annualized_20d: number | null;
  max_drawdown_60d: number | null;
  current_drawdown_60d: number | null;
  return_1d: number | null;
  return_5d: number | null;
  return_20d: number | null;
  return_60d: number | null;
  insufficient_fields: Record<string, number> | null;
}

// ---------------------------------------------------------------------------
// Signal — GET /api/v1/assets/{symbol}/signal
// ---------------------------------------------------------------------------

export type SignalType = "bullish" | "bearish" | "neutral" | "insufficient_data";
export type SignalStrength = number; // 0.0–1.0, float

export interface Signal {
  id: number;
  asset_id: number;
  snapshot_id: number | null;
  strategy_version: string;
  signal_type: SignalType;
  strength: SignalStrength;
  score: number;
  reason_codes: Record<string, boolean>;
  pillar_scores: Record<string, number>;
  calculated_at: string;
}

// ---------------------------------------------------------------------------
// RankingEntry — GET /api/v1/rankings
// ---------------------------------------------------------------------------

export interface RankingEntry {
  asset_id: number;
  symbol: string;
  signal_type: SignalType;
  score: number;
  strength: number;
  strategy_version: string;
  calculated_at: string;
  // Nota: last_close, return_1d, vol_annualized_20d NÃO existem neste endpoint.
  // Exibir "—" nas colunas de preço/variação/volatilidade na watchlist.
}

// ---------------------------------------------------------------------------
// Backtest — GET /api/v1/backtests e GET /api/v1/backtests/{id}
// ---------------------------------------------------------------------------

export interface BacktestRunSummary {
  id: number;
  asset_id: number;
  symbol: string; // adicionado na Sprint 6 (Lacuna 1 — Opção B)
  strategy_name: string;
  strategy_version: string;
  engine_version: string;
  data_start: string;
  data_end: string;
  initial_capital: number;
  status: string; // "completed" | "insufficient_data"
  total_return_pct: number | null;
  sharpe_ratio: number | null;
  max_drawdown_pct: number | null;
  trade_count: number | null;
  created_at: string;
}

export interface BacktestRunDetail extends BacktestRunSummary {
  timeframe: string;
  source: string;
  transaction_cost_bps: number;
  slippage_bps: number;
  risk_free_rate_pct: number;
  parameters_snapshot_json: Record<string, unknown>;
  final_equity: number | null;
  annualized_return_pct: number | null;
  volatility_pct: number | null;
  win_rate_pct: number | null;
  profit_factor: number | null;
  exposure_pct: number | null;
  benchmark_return_pct: number | null;
  equity_curve_json: Array<{ timestamp: string; equity: number }> | null;
}

export interface BacktestTrade {
  id: number;
  backtest_run_id: number;
  entry_timestamp: string;
  exit_timestamp: string;
  entry_price: number;
  exit_price: number;
  executed_entry_price: number;
  executed_exit_price: number;
  quantity: number;
  gross_pnl: number;
  net_pnl: number;
  fees_paid: number;
  reason_entry: string;
  reason_exit: string;
}

// ---------------------------------------------------------------------------
// Health — GET /api/v1/health
// ---------------------------------------------------------------------------

export interface HealthResponse {
  status: string;
  version: string;
}
