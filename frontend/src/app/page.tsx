"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { fetchRankings, fetchAssets, fetchHealth } from "@/lib/api";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { ScoreBar } from "@/components/ui/ScoreBar";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { ErrorState } from "@/components/ui/ErrorState";
import { EmptyState } from "@/components/ui/EmptyState";
import type { SignalType } from "@/types/api";

function KpiCard({
  label,
  value,
  sub,
}: {
  label: string;
  value: string | number;
  sub?: string;
}) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900 p-4">
      <p className="text-xs font-medium uppercase tracking-wider text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-slate-100">{value}</p>
      {sub && <p className="mt-0.5 text-xs text-slate-600">{sub}</p>}
    </div>
  );
}

export default function OverviewPage() {
  const rankingsQ = useQuery({
    queryKey: ["rankings", { limit: 10 }],
    queryFn: () => fetchRankings({ limit: 10 }),
  });

  const assetsQ = useQuery({
    queryKey: ["assets", { limit: 1 }],
    queryFn: () => fetchAssets({ limit: 1 }),
  });

  const healthQ = useQuery({
    queryKey: ["health"],
    queryFn: fetchHealth,
  });

  const bullishQ = useQuery({
    queryKey: ["rankings", "bullish-count"],
    queryFn: () => fetchRankings({ signal_type: "bullish", limit: 1 }),
  });

  const bearishQ = useQuery({
    queryKey: ["rankings", "bearish-count"],
    queryFn: () => fetchRankings({ signal_type: "bearish", limit: 1 }),
  });

  const totalAssets = assetsQ.data?.pagination.total ?? "—";
  const bullishCount = bullishQ.data?.pagination.total ?? "—";
  const bearishCount = bearishQ.data?.pagination.total ?? "—";
  const apiStatus = healthQ.data?.status === "ok" ? "Online" : healthQ.isError ? "Offline" : "—";

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold text-slate-100">Overview</h1>
        <p className="mt-1 text-sm text-slate-500">
          Panorama geral dos ativos monitorados.
        </p>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <KpiCard
          label="Ativos cadastrados"
          value={assetsQ.isLoading ? "…" : totalAssets}
        />
        <KpiCard
          label="Sinal de alta"
          value={bullishQ.isLoading ? "…" : bullishCount}
          sub="ativos com sinal bullish"
        />
        <KpiCard
          label="Sinal de baixa"
          value={bearishQ.isLoading ? "…" : bearishCount}
          sub="ativos com sinal bearish"
        />
        <KpiCard
          label="API"
          value={healthQ.isLoading ? "…" : apiStatus}
          sub={healthQ.data ? `v${healthQ.data.version}` : undefined}
        />
      </div>

      {/* Ranking top 10 */}
      <section aria-labelledby="ranking-title">
        <h2 id="ranking-title" className="mb-3 text-sm font-semibold uppercase tracking-wider text-slate-500">
          Ranking — Top 10 por score
        </h2>

        {rankingsQ.isLoading && <LoadingSpinner label="Carregando ranking…" />}
        {rankingsQ.isError && <ErrorState error={rankingsQ.error} />}
        {rankingsQ.data && rankingsQ.data.items.length === 0 && (
          <EmptyState
            title="Nenhum ativo com sinal calculado"
            description="Ingira dados e recalcule os indicadores para ver o ranking."
          />
        )}

        {rankingsQ.data && rankingsQ.data.items.length > 0 && (
          <div className="overflow-x-auto rounded-lg border border-slate-800">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-900 text-left text-xs text-slate-500">
                  <th className="px-4 py-3 font-medium">#</th>
                  <th className="px-4 py-3 font-medium">Ativo</th>
                  <th className="px-4 py-3 font-medium">Sinal</th>
                  <th className="px-4 py-3 font-medium">Score</th>
                  <th className="px-4 py-3 font-medium hidden sm:table-cell">Versão</th>
                </tr>
              </thead>
              <tbody>
                {rankingsQ.data.items.map((entry, i) => (
                  <tr
                    key={entry.asset_id}
                    className="border-b border-slate-800/50 transition-colors hover:bg-slate-900/50"
                  >
                    <td className="px-4 py-3 text-slate-600 tabular-nums">{i + 1}</td>
                    <td className="px-4 py-3">
                      <Link
                        href={`/assets/${entry.symbol}`}
                        className="font-mono font-medium text-teal-400 hover:text-teal-300 hover:underline"
                      >
                        {entry.symbol}
                      </Link>
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge type={entry.signal_type as SignalType} />
                    </td>
                    <td className="px-4 py-3 w-40">
                      <ScoreBar score={entry.score} />
                    </td>
                    <td className="px-4 py-3 hidden sm:table-cell text-xs text-slate-600 font-mono">
                      {entry.strategy_version}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
