export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-gray-950 p-8 text-gray-100">
      <div className="w-full max-w-2xl space-y-8">
        <div className="space-y-2">
          <h1 className="text-4xl font-bold tracking-tight text-white">
            Stock Intelligence Platform
          </h1>
          <p className="text-gray-400">
            Análise de ações, ranking, backtesting e relatórios por IA.
          </p>
        </div>

        <div className="rounded-lg border border-gray-800 bg-gray-900 p-6 space-y-4">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-gray-500">
            Status do sistema
          </h2>
          <div className="flex items-center gap-3">
            <span className="h-2 w-2 rounded-full bg-green-400" />
            <span className="text-sm text-gray-300">Frontend operacional</span>
          </div>
          <p className="text-xs text-gray-600">
            Sprint 0 — Fundação e governança em andamento.
          </p>
        </div>

        <p className="text-xs text-gray-600 border-t border-gray-800 pt-4">
          Uso educacional e analítico. Não constitui recomendação financeira.
        </p>
      </div>
    </main>
  );
}
