"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

interface EquityPoint {
  timestamp: string;
  equity: number;
}

interface Props {
  data: EquityPoint[];
  initialCapital: number;
  benchmarkReturnPct: number | null;
}

function formatDate(ts: string): string {
  const d = new Date(ts);
  return d.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" });
}

function formatCurrency(v: number): string {
  return v.toLocaleString("pt-BR", { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}

export function EquityCurveChart({ data, initialCapital, benchmarkReturnPct }: Props) {
  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-sm text-slate-500">
        Curva de patrimônio indisponível.
      </div>
    );
  }

  // Adiciona benchmark como linha derivada do capital inicial
  const withBenchmark = data.map((pt, i) => {
    let benchmark: number | null = null;
    if (benchmarkReturnPct !== null) {
      const fraction = i / Math.max(data.length - 1, 1);
      benchmark = initialCapital * (1 + (benchmarkReturnPct / 100) * fraction);
    }
    return { ...pt, benchmark };
  });

  return (
    <div>
      <p className="mb-2 text-xs text-slate-500">
        Patrimônio simulado ao longo do período
      </p>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={withBenchmark} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis
            dataKey="timestamp"
            tickFormatter={formatDate}
            tick={{ fill: "#64748b", fontSize: 11 }}
            interval="preserveStartEnd"
          />
          <YAxis
            tickFormatter={formatCurrency}
            tick={{ fill: "#64748b", fontSize: 11 }}
            width={80}
            domain={["auto", "auto"]}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#0f172a",
              border: "1px solid #1e293b",
              borderRadius: "6px",
              fontSize: "12px",
            }}
            labelStyle={{ color: "#94a3b8" }}
            itemStyle={{ color: "#e2e8f0" }}
            labelFormatter={(v) => new Date(v as string).toLocaleDateString("pt-BR")}
            formatter={(v, name) => [
              typeof v === "number" ? `R$ ${formatCurrency(v)}` : "—",
              name === "equity" ? "Estratégia" : "Buy & Hold",
            ]}
          />
          <Legend wrapperStyle={{ fontSize: "11px", color: "#64748b" }} />
          <Line
            type="monotone"
            dataKey="equity"
            name="Estratégia"
            stroke="#2dd4bf"
            dot={false}
            strokeWidth={1.5}
          />
          {benchmarkReturnPct !== null && (
            <Line
              type="monotone"
              dataKey="benchmark"
              name="Buy & Hold"
              stroke="#94a3b8"
              dot={false}
              strokeWidth={1}
              strokeDasharray="4 2"
            />
          )}
        </LineChart>
      </ResponsiveContainer>
      <p className="mt-2 text-xs text-slate-600">
        Performance passada não garante resultado futuro. Simulação educacional com custos estimados.
      </p>
    </div>
  );
}
