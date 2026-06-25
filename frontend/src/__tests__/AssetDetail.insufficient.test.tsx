import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";

// Testa o comportamento de formatação de campos nulos (insufficient_data)
// sem precisar montar a página completa com React Query.

function fmt(v: number | null | undefined, decimals = 2, suffix = ""): string {
  if (v == null) return "—";
  return `${v.toFixed(decimals)}${suffix}`;
}

function fmtPct(v: number | null | undefined): string {
  if (v == null) return "—";
  return `${v >= 0 ? "+" : ""}${(v * 100).toFixed(2)}%`;
}

// Componente mínimo que representa um card de indicador
function IndicatorCard({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p>{label}</p>
      <p data-testid={`value-${label}`}>{value}</p>
    </div>
  );
}

describe("Detalhe do ativo — estado insufficient_data", () => {
  it("campos null rendem '—' e não 'undefined' ou NaN", () => {
    const snap = {
      rsi_14: null,
      sma_20: null,
      return_1d: null,
      vol_annualized_20d: null,
      last_close: null,
    };

    render(
      <div>
        <IndicatorCard label="RSI 14" value={fmt(snap.rsi_14)} />
        <IndicatorCard label="SMA 20" value={fmt(snap.sma_20)} />
        <IndicatorCard label="Retorno 1d" value={fmtPct(snap.return_1d)} />
        <IndicatorCard label="Volatilidade" value={fmt(snap.vol_annualized_20d)} />
        <IndicatorCard label="Fechamento" value={fmt(snap.last_close)} />
      </div>
    );

    const values = screen.getAllByTestId(/value-/);
    values.forEach((el) => {
      expect(el.textContent).toBe("—");
      expect(el.textContent).not.toBe("undefined");
      expect(el.textContent).not.toContain("NaN");
    });
  });

  it("campo com valor real não retorna '—'", () => {
    expect(fmt(72.4, 2)).toBe("72.40");
    expect(fmt(72.4, 2)).not.toBe("—");
  });

  it("fmtPct com valor positivo retorna '+'", () => {
    expect(fmtPct(0.05)).toBe("+5.00%");
  });

  it("fmtPct com valor negativo não adiciona '+'", () => {
    expect(fmtPct(-0.03)).toBe("-3.00%");
    expect(fmtPct(-0.03)).not.toContain("+");
  });
});
