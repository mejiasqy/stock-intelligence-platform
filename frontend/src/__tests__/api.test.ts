import { describe, it, expect, vi, afterEach } from "vitest";
import { ApiError } from "@/lib/api";

// ---------------------------------------------------------------------------
// Testes unitários da camada de API — sem chamadas de rede reais
// ---------------------------------------------------------------------------

afterEach(() => {
  vi.restoreAllMocks();
});

describe("ApiError", () => {
  it("preserva status, code, message e requestId", () => {
    const err = new ApiError(404, "asset_not_found", "Asset not found.", "req-123");
    expect(err.status).toBe(404);
    expect(err.code).toBe("asset_not_found");
    expect(err.message).toBe("Asset not found.");
    expect(err.requestId).toBe("req-123");
    expect(err.name).toBe("ApiError");
  });

  it("aceita requestId null quando ausente", () => {
    const err = new ApiError(500, "internal_server_error", "Erro.", null);
    expect(err.requestId).toBeNull();
  });

  it("é instanceof Error", () => {
    const err = new ApiError(400, "bad_request", "msg", null);
    expect(err instanceof Error).toBe(true);
    expect(err instanceof ApiError).toBe(true);
  });
});

describe("envelope de erro da API", () => {
  it("parseia envelope {error: {code, message, request_id}}", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      headers: { get: () => "req-abc" },
      json: async () => ({
        error: {
          code: "asset_not_found",
          message: "Asset not found.",
          request_id: "req-abc",
        },
      }),
    });
    vi.stubGlobal("fetch", mockFetch);

    const { fetchAnalysis } = await import("@/lib/api");
    await expect(fetchAnalysis("TEST")).rejects.toMatchObject({
      status: 404,
      code: "asset_not_found",
      message: "Asset not found.",
      requestId: "req-abc",
    });
  });

  it("usa fallback de mensagem quando envelope está malformado", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 503,
      headers: { get: () => null },
      json: async () => ({}),
    });
    vi.stubGlobal("fetch", mockFetch);

    const { fetchAnalysis } = await import("@/lib/api");
    await expect(fetchAnalysis("TEST")).rejects.toMatchObject({
      status: 503,
      code: "api_error",
    });
  });

  it("não quebra quando resposta de erro não tem JSON", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 503,
      headers: { get: () => null },
      json: async () => { throw new SyntaxError("not json"); },
    });
    vi.stubGlobal("fetch", mockFetch);

    const { fetchHealth } = await import("@/lib/api");
    await expect(fetchHealth()).rejects.toBeInstanceOf(ApiError);
  });
});

describe("resposta paginada", () => {
  it("items e pagination.total são preservados", async () => {
    const mockResponse = {
      items: [{ asset_id: 1, symbol: "PETR4.SA", signal_type: "bullish", score: 72, strength: 0.6, strategy_version: "1.0.0", calculated_at: "2026-01-01T00:00:00Z" }],
      pagination: { limit: 10, offset: 0, total: 1 },
    };
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: { get: () => "req-ok" },
      json: async () => mockResponse,
    });
    vi.stubGlobal("fetch", mockFetch);

    const { fetchRankings } = await import("@/lib/api");
    const result = await fetchRankings({ limit: 10 });
    expect(result.items).toHaveLength(1);
    expect(result.pagination.total).toBe(1);
    expect(result.items[0].symbol).toBe("PETR4.SA");
  });
});
