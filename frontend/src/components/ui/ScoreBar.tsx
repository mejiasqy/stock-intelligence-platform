interface Props {
  score: number; // 0–100
  showLabel?: boolean;
  className?: string;
}

function scoreLabel(score: number): string {
  if (score >= 70) return "Alto";
  if (score >= 40) return "Médio";
  return "Baixo";
}

function scoreColor(score: number): string {
  if (score >= 70) return "bg-teal-500";
  if (score >= 40) return "bg-amber-500";
  return "bg-slate-500";
}

export function ScoreBar({ score, showLabel = true, className = "" }: Props) {
  const clamped = Math.max(0, Math.min(100, score));
  const label = scoreLabel(clamped);
  const color = scoreColor(clamped);

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <span className="w-8 text-right text-sm font-mono font-semibold text-slate-100">
        {Math.round(clamped)}
      </span>
      <div
        role="progressbar"
        aria-valuenow={clamped}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`Score: ${Math.round(clamped)} — ${label}`}
        className="flex-1 h-1.5 rounded-full bg-slate-700"
      >
        <div
          className={`h-1.5 rounded-full transition-all ${color}`}
          style={{ width: `${clamped}%` }}
        />
      </div>
      {showLabel && (
        <span className="w-12 text-xs text-slate-400">{label}</span>
      )}
    </div>
  );
}
