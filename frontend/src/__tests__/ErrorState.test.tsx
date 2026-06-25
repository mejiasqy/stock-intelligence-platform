import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ErrorState } from "@/components/ui/ErrorState";
import { ApiError } from "@/lib/api";

describe("ErrorState", () => {
  it("exibe mensagem de erro de ApiError", () => {
    const err = new ApiError(404, "asset_not_found", "Asset not found.", "req-abc");
    render(<ErrorState error={err} />);
    expect(screen.getByText("Asset not found.")).toBeInTheDocument();
  });

  it("exibe request_id de forma discreta quando presente", () => {
    const err = new ApiError(500, "internal_server_error", "Erro interno.", "req-xyz-123");
    render(<ErrorState error={err} />);
    expect(screen.getByText("req-xyz-123")).toBeInTheDocument();
  });

  it("não exibe request_id quando null", () => {
    const err = new ApiError(503, "unavailable", "Serviço indisponível.", null);
    render(<ErrorState error={err} />);
    expect(screen.queryByText(/ID da requisição/)).not.toBeInTheDocument();
  });

  it("exibe mensagem genérica para erro não-ApiError", () => {
    const err = new Error("Falha de rede");
    render(<ErrorState error={err} />);
    expect(screen.getByText("Falha de rede")).toBeInTheDocument();
  });

  it("exibe mensagem padrão para erro desconhecido", () => {
    render(<ErrorState error="unknown" />);
    expect(screen.getByText("Ocorreu um erro inesperado.")).toBeInTheDocument();
  });

  it("tem role alert para acessibilidade", () => {
    render(<ErrorState error={new Error("x")} />);
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });
});
