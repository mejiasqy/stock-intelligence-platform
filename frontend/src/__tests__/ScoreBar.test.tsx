import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ScoreBar } from "@/components/ui/ScoreBar";

describe("ScoreBar", () => {
  it("exibe o valor numérico do score", () => {
    render(<ScoreBar score={72} />);
    expect(screen.getByText("72")).toBeInTheDocument();
  });

  it("exibe label 'Alto' para score >= 70", () => {
    render(<ScoreBar score={80} />);
    expect(screen.getByText("Alto")).toBeInTheDocument();
  });

  it("exibe label 'Médio' para score entre 40 e 69", () => {
    render(<ScoreBar score={55} />);
    expect(screen.getByText("Médio")).toBeInTheDocument();
  });

  it("exibe label 'Baixo' para score < 40", () => {
    render(<ScoreBar score={20} />);
    expect(screen.getByText("Baixo")).toBeInTheDocument();
  });

  it("inclui role progressbar com aria-valuenow", () => {
    render(<ScoreBar score={65} />);
    const bar = screen.getByRole("progressbar");
    expect(bar).toHaveAttribute("aria-valuenow", "65");
    expect(bar).toHaveAttribute("aria-valuemin", "0");
    expect(bar).toHaveAttribute("aria-valuemax", "100");
  });

  it("clampeia score acima de 100 para 100", () => {
    render(<ScoreBar score={150} />);
    expect(screen.getByText("100")).toBeInTheDocument();
  });

  it("clampeia score abaixo de 0 para 0", () => {
    render(<ScoreBar score={-10} />);
    expect(screen.getByText("0")).toBeInTheDocument();
  });

  it("omite label textual quando showLabel=false", () => {
    render(<ScoreBar score={50} showLabel={false} />);
    expect(screen.queryByText("Médio")).not.toBeInTheDocument();
  });
});
