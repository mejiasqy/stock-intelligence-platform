interface Props {
  title?: string;
  description?: string;
  className?: string;
}

export function EmptyState({
  title = "Nenhum dado disponível",
  description,
  className = "",
}: Props) {
  return (
    <div
      role="status"
      aria-label={title}
      className={`flex flex-col items-center justify-center gap-2 py-16 text-center ${className}`}
    >
      <span className="text-2xl text-slate-600" aria-hidden="true">
        ◻
      </span>
      <p className="text-sm font-medium text-slate-400">{title}</p>
      {description && (
        <p className="text-xs text-slate-600 max-w-xs">{description}</p>
      )}
    </div>
  );
}
