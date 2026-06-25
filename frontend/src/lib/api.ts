import type {
  Asset,
  BacktestRunDetail,
  BacktestRunSummary,
  BacktestTrade,
  HealthResponse,
  IndicatorSnapshot,
  PaginatedResponse,
  RankingEntry,
  Signal,
} from "@/types/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ---------------------------------------------------------------------------
// Erro tipado — preserva request_id para exibição no ErrorState
// ---------------------------------------------------------------------------

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
    public readonly requestId: string | null,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// ---------------------------------------------------------------------------
// Fetch base — normaliza envelope de erro e propaga request_id
// ---------------------------------------------------------------------------

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });

  const requestId = res.headers.get("x-request-id");

  if (!res.ok) {
    let code = "api_error";
    let message = `Erro ${res.status}`;
    try {
      const body = (await res.json()) as { error?: { code?: string; message?: string } };
      code = body?.error?.code ?? code;
      message = body?.error?.message ?? message;
    } catch {
      // resposta sem JSON — mantém defaults acima
    }
    throw new ApiError(res.status, code, message, requestId);
  }

  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Health
// ---------------------------------------------------------------------------

export function fetchHealth(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>("/api/v1/health");
}

// ---------------------------------------------------------------------------
// Assets
// ---------------------------------------------------------------------------

export function fetchAssets(params?: {
  limit?: number;
  offset?: number;
}): Promise<PaginatedResponse<Asset>> {
  const q = new URLSearchParams();
  if (params?.limit !== undefined) q.set("limit", String(params.limit));
  if (params?.offset !== undefined) q.set("offset", String(params.offset));
  return apiFetch<PaginatedResponse<Asset>>(`/api/v1/assets?${q}`);
}

// ---------------------------------------------------------------------------
// Prices
// ---------------------------------------------------------------------------

export function fetchPrices(
  symbol: string,
  params?: { limit?: number; offset?: number },
): Promise<PaginatedResponse<{ timestamp: string; close: number; volume: number }>> {
  const q = new URLSearchParams();
  if (params?.limit !== undefined) q.set("limit", String(params.limit));
  if (params?.offset !== undefined) q.set("offset", String(params.offset));
  return apiFetch(`/api/v1/assets/${encodeURIComponent(symbol)}/prices?${q}`);
}

// ---------------------------------------------------------------------------
// Analysis (IndicatorSnapshot)
// ---------------------------------------------------------------------------

export function fetchAnalysis(symbol: string): Promise<IndicatorSnapshot> {
  return apiFetch<IndicatorSnapshot>(
    `/api/v1/assets/${encodeURIComponent(symbol)}/analysis`,
  );
}

// ---------------------------------------------------------------------------
// Signal
// ---------------------------------------------------------------------------

export function fetchSignal(symbol: string): Promise<Signal> {
  return apiFetch<Signal>(`/api/v1/assets/${encodeURIComponent(symbol)}/signal`);
}

// ---------------------------------------------------------------------------
// Rankings / Watchlist
// ---------------------------------------------------------------------------

export function fetchRankings(params?: {
  signal_type?: string;
  min_score?: number;
  max_score?: number;
  sort_order?: "asc" | "desc";
  limit?: number;
  offset?: number;
}): Promise<PaginatedResponse<RankingEntry>> {
  const q = new URLSearchParams();
  if (params?.signal_type) q.set("signal_type", params.signal_type);
  if (params?.min_score !== undefined) q.set("min_score", String(params.min_score));
  if (params?.max_score !== undefined) q.set("max_score", String(params.max_score));
  if (params?.sort_order) q.set("sort_order", params.sort_order);
  if (params?.limit !== undefined) q.set("limit", String(params.limit));
  if (params?.offset !== undefined) q.set("offset", String(params.offset));
  return apiFetch<PaginatedResponse<RankingEntry>>(`/api/v1/rankings?${q}`);
}

// ---------------------------------------------------------------------------
// Backtests
// ---------------------------------------------------------------------------

export function fetchBacktestRuns(params?: {
  symbol?: string;
  strategy_name?: string;
  sort_by?: "created_at" | "total_return_pct" | "sharpe_ratio";
  sort_order?: "asc" | "desc";
  limit?: number;
  offset?: number;
}): Promise<PaginatedResponse<BacktestRunSummary>> {
  const q = new URLSearchParams();
  if (params?.symbol) q.set("symbol", params.symbol);
  if (params?.strategy_name) q.set("strategy_name", params.strategy_name);
  if (params?.sort_by) q.set("sort_by", params.sort_by);
  if (params?.sort_order) q.set("sort_order", params.sort_order);
  if (params?.limit !== undefined) q.set("limit", String(params.limit));
  if (params?.offset !== undefined) q.set("offset", String(params.offset));
  return apiFetch<PaginatedResponse<BacktestRunSummary>>(`/api/v1/backtests?${q}`);
}

export function fetchBacktestDetail(runId: number): Promise<BacktestRunDetail> {
  return apiFetch<BacktestRunDetail>(`/api/v1/backtests/${runId}`);
}

export function fetchBacktestTrades(
  runId: number,
  params?: { limit?: number; offset?: number },
): Promise<PaginatedResponse<BacktestTrade>> {
  const q = new URLSearchParams();
  if (params?.limit !== undefined) q.set("limit", String(params.limit));
  if (params?.offset !== undefined) q.set("offset", String(params.offset));
  return apiFetch<PaginatedResponse<BacktestTrade>>(
    `/api/v1/backtests/${runId}/trades?${q}`,
  );
}
