import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { EmptyState } from "@/components/ui/EmptyState";

describe("EmptyState", () => {
  it("exibe título padrão", () => {
    render(<EmptyState />);
    expect(screen.getByText("Nenhum dado disponível")).toBeInTheDocument();
  });

  it("exibe título personalizado", () => {
    render(<EmptyState title="Nenhum ativo encontrado" />);
    expect(screen.getByText("Nenhum ativo encontrado")).toBeInTheDocument();
  });

  it("exibe descrição quando fornecida", () => {
    render(<EmptyState title="Vazio" description="Ingira dados primeiro." />);
    expect(screen.getByText("Ingira dados primeiro.")).toBeInTheDocument();
  });

  it("não exibe descrição quando ausente", () => {
    const { container } = render(<EmptyState title="Vazio" />);
    // Não deve ter segundo parágrafo de descrição
    const paragraphs = container.querySelectorAll("p");
    expect(paragraphs).toHaveLength(1);
  });

  it("tem role status para acessibilidade", () => {
    render(<EmptyState title="Watchlist vazia" />);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });
});
