"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchBacktestRuns, fetchBacktestDetail, fetchBacktestTrades } from "@/lib/api";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { ErrorState } from "@/components/ui/ErrorState";
import { EmptyState } from "@/components/ui/EmptyState";
import { EquityCurveChart } from "@/components/charts/EquityCurveChart";
import type { BacktestRunSummary } from "@/types/api";

function fmt(v: number | null | undefined, decimals = 2, suffix = ""): string {
  if (v == null) return "—";
  return `${v.toFixed(decimals)}${suffix}`;
}

function fmtDate(s: string): string {
  return new Date(s).toLocaleDateString("pt-BR");
}

function StatusChip({ status }: { status: string }) {
  const completed = status === "completed";
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
        completed
          ? "bg-teal-900/40 text-teal-400 border border-teal-800"
          : "bg-slate-800 text-slate-500 border border-slate-700"
      }`}
    >
      {completed ? "Concluído" : "Dados insuficientes"}
    </span>
  );
}

function MetricRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between py-1.5 border-b border-slate-800/50 last:border-0">
      <span className="text-xs text-slate-500">{label}</span>
      <span className="text-xs font-mono text-slate-200">{value}</span>
    </div>
  );
}

function RunDetail({ runId }: { runId: number }) {
  const detailQ = useQuery({
    queryKey: ["backtest-detail", runId],
    queryFn: () => fetchBacktestDetail(runId),
  });

  const tradesQ = useQuery({
    queryKey: ["backtest-trades", runId],
    queryFn: () => fetchBacktestTrades(runId, { limit: 100 }),
  });

  if (detailQ.isLoading) return <LoadingSpinner label="Carregando detalhes…" />;
  if (detailQ.isError) return <ErrorState error={detailQ.error} />;

  const d = detailQ.data!;
  const equityCurve = d.equity_curve_json ?? [];

  return (
    <div className="mt-4 space-y-4 border-t border-slate-800 pt-4">
      {/* Curva de patrimônio */}
      <section aria-labelledby={`curve-${runId}`} className="rounded-lg border border-slate-800 bg-slate-900 p-4">
        <h3 id={`curve-${runId}`} className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
          Curva de patrimônio
        </h3>
        <EquityCurveChart
          data={equityCurve}
          initialCapital={d.initial_capital}
          benchmarkReturnPct={d.benchmark_return_pct}
        />
      </section>

      {/* Métricas completas */}
      <section aria-labelledby={`metrics-${runId}`}>
        <h3 id={`metrics-${runId}`} className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
          Métricas
        </h3>
        <div className="rounded-lg border border-slate-800 bg-slate-900 p-4 grid grid-cols-1 sm:grid-cols-2 gap-x-8">
          <div>
            <MetricRow label="Retorno total" value={fmt(d.total_return_pct, 2, "%")} />
            <MetricRow label="Retorno anualizado" value={fmt(d.annualized_return_pct, 2, "%")} />
            <MetricRow label="Sharpe ratio" value={fmt(d.sharpe_ratio, 3)} />
            <MetricRow label="Max drawdown" value={fmt(d.max_drawdown_pct, 2, "%")} />
            <MetricRow label="Volatilidade" value={fmt(d.volatility_pct, 2, "%")} />
          </div>
          <div>
            <MetricRow label="Win rate" value={fmt(d.win_rate_pct, 1, "%")} />
            <MetricRow label="Profit factor" value={fmt(d.profit_factor, 2)} />
            <MetricRow label="Exposição" value={fmt(d.exposure_pct, 1, "%")} />
            <MetricRow label="Buy & Hold" value={fmt(d.benchmark_return_pct, 2, "%")} />
            <MetricRow label="Nº de trades" value={d.trade_count != null ? String(d.trade_count) : "—"} />
          </div>
        </div>
      </section>

      {/* Parâmetros */}
      <section aria-labelledby={`params-${runId}`}>
        <h3 id={`params-${runId}`} className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
          Parâmetros da execução
        </h3>
        <div className="rounded-lg border border-slate-800 bg-slate-900 p-4 grid grid-cols-2 gap-x-8">
          <MetricRow label="Capital inicial" value={`R$ ${d.initial_capital.toLocaleString("pt-BR")}`} />
          <MetricRow label="Custo de transação" value={`${d.transaction_cost_bps} bps`} />
          <MetricRow label="Slippage" value={`${d.slippage_bps} bps`} />
          <MetricRow label="Equity final" value={d.final_equity != null ? `R$ ${d.final_equity.toLocaleString("pt-BR")}` : "—"} />
          <MetricRow label="Período" value={`${fmtDate(d.data_start)} → ${fmtDate(d.data_end)}`} />
          <MetricRow label="Versão do motor" value={d.engine_version} />
        </div>
      </section>

      {/* Trades */}
      <section aria-labelledby={`trades-${runId}`}>
        <h3 id={`trades-${runId}`} className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
          Trades simulados
        </h3>
        {tradesQ.isLoading && <LoadingSpinner label="Carregando trades…" />}
        {tradesQ.isError && <ErrorState error={tradesQ.error} />}
        {tradesQ.data && tradesQ.data.items.length === 0 && (
          <EmptyState title="Nenhum trade simulado" description="Status: dados insuficientes." />
        )}
        {tradesQ.data && tradesQ.data.items.length > 0 && (
          <div className="overflow-x-auto rounded-lg border border-slate-800">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-900 text-left text-slate-500">
                  <th className="px-3 py-2 font-medium">Entrada</th>
                  <th className="px-3 py-2 font-medium">Saída</th>
                  <th className="px-3 py-2 font-medium text-right">Preço entrada</th>
                  <th className="px-3 py-2 font-medium text-right">Preço saída</th>
                  <th className="px-3 py-2 font-medium text-right">P&amp;L líquido</th>
                  <th className="px-3 py-2 font-medium hidden md:table-cell">Motivo</th>
                </tr>
              </thead>
              <tbody>
                {tradesQ.data.items.map((t) => (
                  <tr key={t.id} className="border-b border-slate-800/50">
                    <td className="px-3 py-2 font-mono text-slate-400">{fmtDate(t.entry_timestamp)}</td>
                    <td className="px-3 py-2 font-mono text-slate-400">{fmtDate(t.exit_timestamp)}</td>
                    <td className="px-3 py-2 font-mono text-right">{t.entry_price.toFixed(2)}</td>
                    <td className="px-3 py-2 font-mono text-right">{t.exit_price.toFixed(2)}</td>
                    <td
                      className={`px-3 py-2 font-mono text-right ${
                        t.net_pnl >= 0 ? "text-teal-400" : "text-amber-400"
                      }`}
                    >
                      {t.net_pnl >= 0 ? "+" : ""}
                      {t.net_pnl.toFixed(2)}
                    </td>
                    <td className="px-3 py-2 text-slate-500 hidden md:table-cell">{t.reason_exit}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {tradesQ.data.pagination.total > 100 && (
              <p className="px-3 py-2 text-xs text-slate-600 border-t border-slate-800">
                Mostrando 100 de {tradesQ.data.pagination.total} trades.
              </p>
            )}
          </div>
        )}
      </section>
    </div>
  );
}

export default function BacktestsPage() {
  const [selectedRunId, setSelectedRunId] = useState<number | null>(null);

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["backtests"],
    queryFn: () => fetchBacktestRuns({ limit: 50 }),
  });

  function toggleRun(id: number) {
    setSelectedRunId((prev) => (prev === id ? null : id));
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-100">Backtests</h1>
        <p className="mt-1 text-sm text-slate-500">
          Histórico de execuções de estratégias em dados históricos.
        </p>
      </div>

      {isLoading && <LoadingSpinner label="Carregando backtests…" />}
      {isError && <ErrorState error={error} />}

      {data && data.items.length === 0 && (
        <EmptyState
          title="Nenhum backtest registrado"
          description="Execute um backtest via API para ver os resultados aqui."
        />
      )}

      {data && data.items.length > 0 && (
        <div className="space-y-2">
          {data.items.map((run: BacktestRunSummary) => (
            <article key={run.id} className="rounded-lg border border-slate-800 bg-slate-900">
              <button
                onClick={() => toggleRun(run.id)}
                aria-expanded={selectedRunId === run.id}
                className="w-full px-4 py-3 text-left"
              >
                <div className="flex items-center justify-between gap-4 flex-wrap">
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-sm font-medium text-teal-400">
                      {run.symbol}
                    </span>
                    <span className="text-xs text-slate-500">{run.strategy_name}</span>
                    <StatusChip status={run.status} />
                  </div>
                  <div className="flex items-center gap-6 text-xs text-slate-400">
                    <span>
                      <span className="text-slate-600">Retorno </span>
                      <span className="font-mono">{fmt(run.total_return_pct, 2, "%")}</span>
                    </span>
                    <span>
                      <span className="text-slate-600">Sharpe </span>
                      <span className="font-mono">{fmt(run.sharpe_ratio, 2)}</span>
                    </span>
                    <span>
                      <span className="text-slate-600">DD </span>
                      <span className="font-mono">{fmt(run.max_drawdown_pct, 2, "%")}</span>
                    </span>
                    <span className="text-slate-600">
                      {fmtDate(run.data_start)} → {fmtDate(run.data_end)}
                    </span>
                    <span
                      aria-hidden="true"
                      className={`text-slate-500 transition-transform ${
                        selectedRunId === run.id ? "rotate-180" : ""
                      }`}
                    >
                      ▾
                    </span>
                  </div>
                </div>
              </button>

              {selectedRunId === run.id && (
                <div className="px-4 pb-4">
                  <RunDetail runId={run.id} />
                </div>
              )}
            </article>
          ))}

          {data.pagination.total > 50 && (
            <p className="text-xs text-slate-600">
              Mostrando 50 de {data.pagination.total} backtests.
            </p>
          )}
        </div>
      )}

      <p className="text-xs text-slate-600 border-t border-slate-800 pt-4">
        Resultados de backtesting são simulações históricas com custos estimados. Não representam
        desempenho real ou futuro.
      </p>
    </div>
  );
}
