import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, api, onUnauthorized } from "../api/client";
import { clearToken, getToken, setToken } from "../api/token";
import { formatCents } from "../lib/money";

// ---------- helpers ----------

type Handler = (init: RequestInit | undefined) => Response | Promise<Response>;

const BASE = "http://localhost:8000";

function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status, headers: { "Content-Type": "application/json" },
  });
}

/** Mocka o fetch. As chaves são "MÉTODO /caminho" (sem query); rota desconhecida → 404. */
function mockApi(routes: Record<string, Handler>) {
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = new URL(String(input));
    const key = `${(init?.method ?? "GET").toUpperCase()} ${url.pathname}`;
    const handler = routes[key];
    return handler ? handler(init) : json(404, { detail: "Not found" });
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function header(init: RequestInit | undefined, name: string): string | null {
  return new Headers(init?.headers).get(name);
}

beforeEach(() => {
  localStorage.clear();
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

// ---------- lib/money ----------

describe("formatCents", () => {
  const norm = (s: string) => s.replace(/\s/g, " ");

  it("formata centavos em reais", () => {
    expect(norm(formatCents(1320))).toBe("$13.20");
    expect(norm(formatCents(0))).toBe("$0.00");
    expect(norm(formatCents(123456))).toBe("$1,234.56");
  });
});

// ---------- api/token ----------

describe("token", () => {
  it("guarda, lê e apaga o token na chave mercatto.token", () => {
    setToken("abc");
    expect(getToken()).toBe("abc");
    expect(localStorage.getItem("mercatto.token")).toBe("abc");
    clearToken();
    expect(getToken()).toBeFalsy();
    expect(localStorage.getItem("mercatto.token")).toBeNull();
  });

  it("não lança erro quando o localStorage falha", () => {
    const boom = () => { throw new Error("storage indisponível"); };
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(boom);
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(boom);
    vi.spyOn(Storage.prototype, "removeItem").mockImplementation(boom);
    expect(() => setToken("x")).not.toThrow();
    expect(() => getToken()).not.toThrow();
    expect(getToken()).toBeFalsy();
    expect(() => clearToken()).not.toThrow();
  });
});

// ---------- api/client ----------

describe("api", () => {
  it("faz GET na URL base e devolve o JSON", async () => {
    const fetchMock = mockApi({ "GET /api/ping": () => json(200, { ok: true }) });
    await expect(api<{ ok: boolean }>("/api/ping")).resolves.toEqual({ ok: true });
    expect(String(fetchMock.mock.calls[0][0])).toBe(`${BASE}/api/ping`);
  });

  it("envia body como JSON com o método pedido", async () => {
    const fetchMock = mockApi({ "POST /api/echo": () => json(201, { id: 9 }) });
    await expect(api("/api/echo", { method: "POST", body: { a: 1 } })).resolves.toEqual({ id: 9 });
    const init = fetchMock.mock.calls[0][1];
    expect(header(init, "Content-Type")).toContain("application/json");
    expect(JSON.parse(String(init?.body))).toEqual({ a: 1 });
  });

  it("manda o token salvo no Authorization e omite sem token", async () => {
    const fetchMock = mockApi({ "GET /api/ping": () => json(200, {}) });
    await api("/api/ping");
    expect(header(fetchMock.mock.calls[0][1], "Authorization")).toBeNull();
    setToken("tok-1");
    await api("/api/ping");
    expect(header(fetchMock.mock.calls[1][1], "Authorization")).toBe("Bearer tok-1");
  });

  it("devolve undefined em 204", async () => {
    mockApi({ "DELETE /api/x": () => new Response(null, { status: 204 }) });
    await expect(api("/api/x", { method: "DELETE" })).resolves.toBeUndefined();
  });

  it("lança ApiError com o detail em texto", async () => {
    mockApi({ "POST /api/x": () => json(409, { detail: "Email already registered" }) });
    const err = await api("/api/x", { method: "POST", body: {} }).catch((e: unknown) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect(err).toBeInstanceOf(Error);
    expect(err).toMatchObject({ status: 409, detail: "Email already registered" });
  });

  it("une as mensagens de um 422 do FastAPI com '; '", async () => {
    mockApi({
      "POST /api/x": () => json(422, {
        detail: [
          { loc: ["body", "email"], msg: "invalid email", type: "value_error" },
          { loc: ["body", "password"], msg: "password too short", type: "value_error" },
        ],
      }),
    });
    const err = await api("/api/x", { method: "POST", body: {} }).catch((e: unknown) => e);
    expect(err).toMatchObject({ status: 422, detail: "invalid email; password too short" });
  });

  it("usa 'Erro <status>' quando a resposta não é JSON", async () => {
    mockApi({ "GET /api/x": () => new Response("Internal Server Error", { status: 500 }) });
    const err = await api("/api/x").catch((e: unknown) => e);
    expect(err).toMatchObject({ status: 500, detail: "Error 500" });
  });

  it("chama os callbacks de onUnauthorized em 401 e permite removê-los", async () => {
    mockApi({ "GET /api/x": () => json(401, { detail: "Not authenticated" }) });
    const kept = vi.fn();
    const removed = vi.fn();
    const offKept = onUnauthorized(kept);
    const offRemoved = onUnauthorized(removed);
    offRemoved();
    const err = await api("/api/x").catch((e: unknown) => e);
    expect(err).toMatchObject({ status: 401 });
    expect(kept).toHaveBeenCalledTimes(1);
    expect(removed).not.toHaveBeenCalled();
    offKept();
  });
});
