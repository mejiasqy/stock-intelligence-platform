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

interface DataPoint {
  timestamp: string;
  close: number;
}

interface Props {
  data: DataPoint[];
  symbol: string;
}

function formatDate(ts: string): string {
  const d = new Date(ts);
  return d.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" });
}

function formatPrice(v: number): string {
  return v.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export function PriceChart({ data, symbol }: Props) {
  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-sm text-slate-500">
        Histórico de preços indisponível.
      </div>
    );
  }

  // Apresenta do mais antigo para o mais recente
  const sorted = [...data].reverse();

  return (
    <div>
      <p className="mb-2 text-xs text-slate-500">
        Fechamento histórico — {symbol}
        <span className="ml-2 text-slate-600">
          (SMA/EMA indisponíveis como série histórica nesta versão)
        </span>
      </p>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={sorted} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis
            dataKey="timestamp"
            tickFormatter={formatDate}
            tick={{ fill: "#64748b", fontSize: 11 }}
            interval="preserveStartEnd"
          />
          <YAxis
            tickFormatter={formatPrice}
            tick={{ fill: "#64748b", fontSize: 11 }}
            width={70}
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
            formatter={(v) => [typeof v === "number" ? formatPrice(v) : "—", "Fechamento"]}
          />
          <Legend
            wrapperStyle={{ fontSize: "11px", color: "#64748b" }}
          />
          <Line
            type="monotone"
            dataKey="close"
            name="Fechamento"
            stroke="#2dd4bf"
            dot={false}
            strokeWidth={1.5}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
