"use client";

import { use } from "react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { fetchAnalysis, fetchSignal, fetchPrices } from "@/lib/api";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { ScoreBar } from "@/components/ui/ScoreBar";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { ErrorState } from "@/components/ui/ErrorState";
import { PriceChart } from "@/components/charts/PriceChart";
import type { SignalType } from "@/types/api";

interface Props {
  params: Promise<{ symbol: string }>;
}

function fmt(v: number | null | undefined, decimals = 2, suffix = ""): string {
  if (v == null) return "—";
  return `${v.toFixed(decimals)}${suffix}`;
}

function fmtPct(v: number | null | undefined): string {
  if (v == null) return "—";
  return `${v >= 0 ? "+" : ""}${(v * 100).toFixed(2)}%`;
}

function IndicatorCard({
  label,
  value,
  sub,
}: {
  label: string;
  value: string;
  sub?: string;
}) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900 p-3">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="mt-0.5 text-lg font-mono font-semibold text-slate-100">{value}</p>
      {sub && <p className="mt-0.5 text-xs text-slate-600">{sub}</p>}
    </div>
  );
}

export default function AssetDetailPage({ params }: Props) {
  const { symbol } = use(params);
  const upperSymbol = symbol.toUpperCase();

  const analysisQ = useQuery({
    queryKey: ["analysis", upperSymbol],
    queryFn: () => fetchAnalysis(upperSymbol),
  });

  const signalQ = useQuery({
    queryKey: ["signal", upperSymbol],
    queryFn: () => fetchSignal(upperSymbol),
  });

  const pricesQ = useQuery({
    queryKey: ["prices", upperSymbol, { limit: 120 }],
    queryFn: () => fetchPrices(upperSymbol, { limit: 120 }),
  });

  const snap = analysisQ.data;
  const sig = signalQ.data;
  const prices = pricesQ.data?.items ?? [];

  const isInsufficientData = snap?.status === "insufficient_data";

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <nav aria-label="Caminho" className="text-xs text-slate-600">
        <Link href="/watchlist" className="hover:text-slate-400">
          Watchlist
        </Link>
        <span className="mx-2">›</span>
        <span className="text-slate-400">{upperSymbol}</span>
      </nav>

      {/* Header */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-mono font-semibold text-slate-100">{upperSymbol}</h1>
          {snap && (
            <p className="mt-0.5 text-xs text-slate-600">
              Calculado em{" "}
              {new Date(snap.calculated_at).toLocaleString("pt-BR")} · {snap.candles_used} candles
              {isInsufficientData && (
                <span className="ml-2 text-amber-500">⚠ dados insuficientes</span>
              )}
            </p>
          )}
        </div>
        {sig && (
          <div className="flex items-center gap-3">
            <StatusBadge type={sig.signal_type as SignalType} />
            <div className="w-40">
              <ScoreBar score={sig.score} />
            </div>
          </div>
        )}
      </div>

      {/* Erros de carregamento */}
      {analysisQ.isError && (
        <ErrorState
          error={analysisQ.error}
          className="mt-2"
        />
      )}
      {signalQ.isError && !analysisQ.isError && (
        <ErrorState error={signalQ.error} className="mt-2" />
      )}

      {analysisQ.isLoading && <LoadingSpinner label="Carregando análise…" />}

      {snap && (
        <>
          {/* Cards de preço e retorno */}
          <section aria-labelledby="price-section">
            <h2 id="price-section" className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
              Preço e retorno
            </h2>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-5">
              <IndicatorCard label="Último fechamento" value={fmt(snap.last_close, 2)} />
              <IndicatorCard label="Retorno 1d" value={fmtPct(snap.return_1d)} />
              <IndicatorCard label="Retorno 5d" value={fmtPct(snap.return_5d)} />
              <IndicatorCard label="Retorno 20d" value={fmtPct(snap.return_20d)} />
              <IndicatorCard label="Retorno 60d" value={fmtPct(snap.return_60d)} />
            </div>
          </section>

          {/* Gráfico de preço */}
          <section
            aria-labelledby="chart-title"
            className="rounded-lg border border-slate-800 bg-slate-900 p-4"
          >
            <h2 id="chart-title" className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
              Histórico de fechamento
            </h2>
            {pricesQ.isLoading && <LoadingSpinner label="Carregando preços…" />}
            {pricesQ.isError && <ErrorState error={pricesQ.error} />}
            {!pricesQ.isLoading && !pricesQ.isError && (
              <PriceChart
                data={prices.map((p) => ({ timestamp: p.timestamp, close: p.close }))}
                symbol={upperSymbol}
              />
            )}
          </section>

          {/* Indicadores técnicos */}
          <section aria-labelledby="indicators-section">
            <h2 id="indicators-section" className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
              Indicadores técnicos
              {isInsufficientData && (
                <span className="ml-2 font-normal text-amber-600">
                  — dados insuficientes para alguns campos
                </span>
              )}
            </h2>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
              <IndicatorCard label="SMA 20" value={fmt(snap.sma_20, 2)} sub="valor pontual" />
              <IndicatorCard label="SMA 50" value={fmt(snap.sma_50, 2)} sub="valor pontual" />
              <IndicatorCard label="EMA 20" value={fmt(snap.ema_20, 2)} sub="valor pontual" />
              <IndicatorCard label="RSI 14" value={fmt(snap.rsi_14, 1)} />
              <IndicatorCard label="MACD" value={fmt(snap.macd, 4)} />
              <IndicatorCard label="MACD Sinal" value={fmt(snap.macd_signal, 4)} />
              <IndicatorCard label="MACD Histograma" value={fmt(snap.macd_histogram, 4)} />
              <IndicatorCard
                label="Bollinger Superior"
                value={fmt(snap.bollinger_upper, 2)}
              />
              <IndicatorCard
                label="Bollinger Médio"
                value={fmt(snap.bollinger_middle, 2)}
              />
              <IndicatorCard
                label="Bollinger Inferior"
                value={fmt(snap.bollinger_lower, 2)}
              />
              <IndicatorCard
                label="Volatilidade anualizada"
                value={fmt(snap.vol_annualized_20d != null ? snap.vol_annualized_20d * 100 : null, 1, "%")}
              />
              <IndicatorCard
                label="Max Drawdown 60d"
                value={fmt(snap.max_drawdown_60d != null ? snap.max_drawdown_60d * 100 : null, 1, "%")}
              />
            </div>
            <p className="mt-2 text-xs text-slate-600">
              SMA/EMA exibidos como valores pontuais. Série histórica de indicadores indisponível nesta versão.
            </p>
          </section>

          {/* Score e reason codes */}
          {sig && (
            <section aria-labelledby="score-section" className="rounded-lg border border-slate-800 bg-slate-900 p-4">
              <h2 id="score-section" className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
                Composição do score — v{sig.strategy_version}
              </h2>
              <div className="mb-4">
                <p className="text-xs text-slate-500 mb-1">Score geral</p>
                <div className="w-56">
                  <ScoreBar score={sig.score} />
                </div>
              </div>

              {/* Pilares */}
              {Object.keys(sig.pillar_scores).length > 0 && (
                <div className="mb-4">
                  <p className="text-xs text-slate-500 mb-2">Score por pilar</p>
                  <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                    {Object.entries(sig.pillar_scores).map(([pillar, score]) => (
                      <div key={pillar} className="flex items-center gap-2">
                        <span className="w-28 text-xs text-slate-400 capitalize">
                          {pillar.replace(/_/g, " ")}
                        </span>
                        <div className="flex-1 max-w-xs">
                          <ScoreBar score={score} showLabel={false} />
                        </div>
                        <span className="text-xs font-mono text-slate-500 w-8 text-right">
                          {score.toFixed(0)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Reason codes */}
              {Object.keys(sig.reason_codes).length > 0 && (
                <div>
                  <p className="text-xs text-slate-500 mb-2">Fatores</p>
                  <div className="flex flex-wrap gap-1.5">
                    {Object.entries(sig.reason_codes).map(([code, active]) => (
                      <span
                        key={code}
                        className={`rounded px-2 py-0.5 text-xs font-mono ${
                          active
                            ? "bg-teal-900/40 text-teal-400 border border-teal-800"
                            : "bg-slate-800 text-slate-600 border border-slate-700"
                        }`}
                        title={active ? "Fator ativo" : "Fator inativo"}
                      >
                        {active ? "✓" : "✗"} {code}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </section>
          )}

          {/* Histórico de sinais — indisponível */}
          <section aria-labelledby="signal-history">
            <h2 id="signal-history" className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
              Histórico de sinais
            </h2>
            <p className="text-sm text-slate-600 italic">
              Histórico de sinais indisponível nesta versão.
            </p>
          </section>
        </>
      )}
    </div>
  );
}
