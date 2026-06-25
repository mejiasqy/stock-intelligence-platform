import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { StatusBadge } from "@/components/ui/StatusBadge";

describe("StatusBadge", () => {
  it("exibe rótulo de alta para bullish", () => {
    render(<StatusBadge type="bullish" />);
    expect(screen.getByRole("status", { name: "Alta" })).toBeInTheDocument();
    expect(screen.getByText("Alta")).toBeInTheDocument();
  });

  it("exibe rótulo de baixa para bearish", () => {
    render(<StatusBadge type="bearish" />);
    expect(screen.getByRole("status", { name: "Baixa" })).toBeInTheDocument();
    expect(screen.getByText("Baixa")).toBeInTheDocument();
  });

  it("exibe rótulo neutro para neutral", () => {
    render(<StatusBadge type="neutral" />);
    expect(screen.getByRole("status", { name: "Neutro" })).toBeInTheDocument();
    expect(screen.getByText("Neutro")).toBeInTheDocument();
  });

  it("exibe dados insuficientes para insufficient_data", () => {
    render(<StatusBadge type="insufficient_data" />);
    expect(screen.getByRole("status", { name: "Dados insuficientes" })).toBeInTheDocument();
    expect(screen.getByText("Dados insuficientes")).toBeInTheDocument();
  });

  it("inclui símbolo visual além do texto", () => {
    const { container } = render(<StatusBadge type="bullish" />);
    // O símbolo está em aria-hidden e não aparece no accessible name
    const symbolEl = container.querySelector("[aria-hidden='true']");
    expect(symbolEl).toBeInTheDocument();
    expect(symbolEl?.textContent).toBe("▲");
  });
});
