"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { fetchRankings } from "@/lib/api";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { ScoreBar } from "@/components/ui/ScoreBar";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { ErrorState } from "@/components/ui/ErrorState";
import { EmptyState } from "@/components/ui/EmptyState";
import type { SignalType } from "@/types/api";

const SIGNAL_FILTERS = [
  { value: "", label: "Todos" },
  { value: "bullish", label: "Alta" },
  { value: "bearish", label: "Baixa" },
  { value: "neutral", label: "Neutro" },
] as const;

export default function WatchlistPage() {
  const [signalFilter, setSignalFilter] = useState("");

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["rankings", { signal_type: signalFilter }],
    queryFn: () =>
      fetchRankings({
        signal_type: signalFilter || undefined,
        limit: 100,
      }),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-semibold text-slate-100">Watchlist</h1>
          <p className="mt-1 text-sm text-slate-500">
            Ativos com sinal calculado, ordenados por score.
          </p>
        </div>

        {/* Filtro por sinal */}
        <fieldset aria-label="Filtrar por tipo de sinal" className="flex gap-1">
          {SIGNAL_FILTERS.map(({ value, label }) => (
            <button
              key={value}
              onClick={() => setSignalFilter(value)}
              aria-pressed={signalFilter === value}
              className={`rounded px-3 py-1.5 text-xs font-medium transition-colors ${
                signalFilter === value
                  ? "bg-slate-700 text-slate-100"
                  : "bg-slate-900 text-slate-400 hover:bg-slate-800 hover:text-slate-200"
              }`}
            >
              {label}
            </button>
          ))}
        </fieldset>
      </div>

      {isLoading && <LoadingSpinner label="Carregando watchlist…" />}
      {isError && <ErrorState error={error} />}

      {data && data.items.length === 0 && (
        <EmptyState
          title="Nenhum ativo encontrado"
          description={
            signalFilter
              ? `Não há ativos com sinal "${signalFilter}" calculado.`
              : "Ingira dados e recalcule os indicadores para ver a watchlist."
          }
        />
      )}

      {data && data.items.length > 0 && (
        <>
          <p className="text-xs text-slate-600">
            {data.pagination.total} ativo{data.pagination.total !== 1 ? "s" : ""} encontrado
            {data.pagination.total !== 1 ? "s" : ""}
          </p>
          <div className="overflow-x-auto rounded-lg border border-slate-800">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-900 text-left text-xs text-slate-500">
                  <th className="px-4 py-3 font-medium">Ativo</th>
                  <th className="px-4 py-3 font-medium">Sinal</th>
                  <th className="px-4 py-3 font-medium">Score</th>
                  <th
                    className="px-4 py-3 font-medium text-right"
                    title="Disponível apenas na página de detalhe do ativo"
                  >
                    Preço ¹
                  </th>
                  <th
                    className="px-4 py-3 font-medium text-right hidden sm:table-cell"
                    title="Disponível apenas na página de detalhe do ativo"
                  >
                    Var. 1d ¹
                  </th>
                  <th
                    className="px-4 py-3 font-medium text-right hidden md:table-cell"
                    title="Disponível apenas na página de detalhe do ativo"
                  >
                    Volatilidade ¹
                  </th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((entry) => (
                  <tr
                    key={entry.asset_id}
                    className="border-b border-slate-800/50 transition-colors hover:bg-slate-900/50"
                  >
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
                    <td className="px-4 py-3 w-44">
                      <ScoreBar score={entry.score} />
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-slate-600">—</td>
                    <td className="px-4 py-3 text-right font-mono text-slate-600 hidden sm:table-cell">
                      —
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-slate-600 hidden md:table-cell">
                      —
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="text-xs text-slate-600">
            ¹ Preço, variação e volatilidade disponíveis na{" "}
            <Link href="/assets" className="text-slate-500 underline hover:text-slate-400">
              página de detalhe
            </Link>{" "}
            de cada ativo. O endpoint de ranking não inclui esses campos nesta versão.
          </p>
        </>
      )}
    </div>
  );
}
