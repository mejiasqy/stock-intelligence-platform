import type { SignalType } from "@/types/api";

interface Props {
  type: SignalType;
  className?: string;
}

const CONFIG: Record<
  SignalType,
  { label: string; symbol: string; bg: string; text: string; border: string }
> = {
  bullish: {
    label: "Alta",
    symbol: "▲",
    bg: "bg-teal-900/40",
    text: "text-teal-300",
    border: "border-teal-700",
  },
  bearish: {
    label: "Baixa",
    symbol: "▼",
    bg: "bg-amber-900/40",
    text: "text-amber-300",
    border: "border-amber-700",
  },
  neutral: {
    label: "Neutro",
    symbol: "◆",
    bg: "bg-slate-800",
    text: "text-slate-300",
    border: "border-slate-600",
  },
  insufficient_data: {
    label: "Dados insuficientes",
    symbol: "—",
    bg: "bg-slate-900",
    text: "text-slate-500",
    border: "border-slate-700",
  },
};

export function StatusBadge({ type, className = "" }: Props) {
  const c = CONFIG[type] ?? CONFIG.insufficient_data;
  return (
    <span
      role="status"
      aria-label={c.label}
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium ${c.bg} ${c.text} ${c.border} ${className}`}
    >
      <span aria-hidden="true">{c.symbol}</span>
      {c.label}
    </span>
  );
}
