import { ApiError } from "@/lib/api";

interface Props {
  error: unknown;
  className?: string;
}

function safeMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  if (error instanceof Error) return error.message;
  return "Ocorreu um erro inesperado.";
}

function safeRequestId(error: unknown): string | null {
  if (error instanceof ApiError) return error.requestId;
  return null;
}

export function ErrorState({ error, className = "" }: Props) {
  const message = safeMessage(error);
  const requestId = safeRequestId(error);

  return (
    <div
      role="alert"
      className={`rounded-lg border border-amber-800/50 bg-amber-950/30 p-6 ${className}`}
    >
      <p className="text-sm font-medium text-amber-300">Não foi possível carregar os dados</p>
      <p className="mt-1 text-sm text-slate-400">{message}</p>
      {requestId && (
        <p className="mt-3 text-xs text-slate-600">
          ID da requisição:{" "}
          <code className="font-mono text-slate-500">{requestId}</code>
        </p>
      )}
    </div>
  );
}
