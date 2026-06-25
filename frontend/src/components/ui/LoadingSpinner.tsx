interface Props {
  label?: string;
  className?: string;
}

export function LoadingSpinner({ label = "Carregando…", className = "" }: Props) {
  return (
    <div
      role="status"
      aria-label={label}
      className={`flex flex-col items-center justify-center gap-3 py-12 text-slate-500 ${className}`}
    >
      <div className="h-6 w-6 animate-spin rounded-full border-2 border-slate-600 border-t-teal-400" />
      <span className="text-sm">{label}</span>
    </div>
  );
}
