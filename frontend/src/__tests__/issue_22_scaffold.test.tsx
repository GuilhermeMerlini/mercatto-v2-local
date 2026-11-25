import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { MemoryRouter, useLocation } from "react-router-dom";

import App from "../App";
import { ApiError, api, onUnauthorized } from "../api/client";
import { clearToken, getToken, setToken } from "../api/token";
import { AuthProvider, useAuth } from "../auth/AuthContext";
import { formatCents } from "../lib/money";

// ---------- helpers ----------

type Handler = (init: RequestInit | undefined) => Response | Promise<Response>;

const BASE = "http://localhost:8000";

const BUYER = {
  id: 1, name: "Ana Compradora", email: "ana@ex.com", role: "BUYER",
  created_at: "2026-01-01T00:00:00Z",
};
const SELLER = { ...BUYER, id: 2, name: "Seu Vendedor", email: "vend@ex.com", role: "SELLER" };

function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status, headers: { "Content-Type": "application/json" },
  });
}

function loginOut(user: typeof BUYER, token: string) {
  return { ...user, access_token: token, token_type: "bearer", expires_at: "2026-12-31T00:00:00Z" };
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

function LocationProbe() {
  const location = useLocation();
  return <div data-testid="location">{location.pathname + location.search}</div>;
}

function renderApp(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
      <LocationProbe />
    </MemoryRouter>,
  );
}

function currentLocation(): URL {
  return new URL(screen.getByTestId("location").textContent ?? "", "http://app");
}

beforeEach(() => {
  localStorage.clear();
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

// ---------- lib/money ----------

describe("formatCents", () => {
  const norm = (s: string) => s.replace(/\s/g, " ");

  it("formata centavos em reais", () => {
    expect(norm(formatCents(1320))).toBe("R$ 13,20");
    expect(norm(formatCents(0))).toBe("R$ 0,00");
    expect(norm(formatCents(123456))).toBe("R$ 1.234,56");
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
          { loc: ["body", "email"], msg: "email inválido", type: "value_error" },
          { loc: ["body", "password"], msg: "senha curta", type: "value_error" },
        ],
      }),
    });
    const err = await api("/api/x", { method: "POST", body: {} }).catch((e: unknown) => e);
    expect(err).toMatchObject({ status: 422, detail: "email inválido; senha curta" });
  });

  it("usa 'Erro <status>' quando a resposta não é JSON", async () => {
    mockApi({ "GET /api/x": () => new Response("Internal Server Error", { status: 500 }) });
    const err = await api("/api/x").catch((e: unknown) => e);
    expect(err).toMatchObject({ status: 500, detail: "Erro 500" });
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

// ---------- auth/AuthContext ----------

function AuthProbe() {
  const { user, loading, login, register, logout } = useAuth();
  const [error, setError] = useState("");
  const run = (fn: () => Promise<unknown>) => () => {
    setError("");
    fn().catch((e: unknown) => setError(e instanceof ApiError ? e.detail : "falhou"));
  };
  return (
    <div>
      <p data-testid="user">{loading ? "carregando" : user ? `${user.name}|${user.role}` : "anônimo"}</p>
      <p data-testid="error">{error}</p>
      <button onClick={run(() => login("ana@ex.com", "segredo123"))}>login</button>
      <button
        onClick={run(() => register({ name: "Ana Compradora", email: "ana@ex.com", password: "segredo123", role: "BUYER" }))}
      >
        register
      </button>
      <button onClick={() => logout()}>logout</button>
      <button onClick={run(() => api("/api/cart"))}>protegido</button>
    </div>
  );
}

function renderAuth() {
  return render(
    <MemoryRouter>
      <AuthProvider>
        <AuthProbe />
      </AuthProvider>
    </MemoryRouter>,
  );
}

describe("AuthProvider / useAuth", () => {
  it("começa anônimo sem token salvo", async () => {
    const fetchMock = mockApi({});
    renderAuth();
    expect(await screen.findByText("anônimo")).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("login chama a API, guarda o token e define o usuário", async () => {
    const fetchMock = mockApi({ "POST /api/users/login": () => json(200, loginOut(BUYER, "tok-login")) });
    renderAuth();
    await userEvent.click(screen.getByRole("button", { name: "login" }));
    expect(await screen.findByText("Ana Compradora|BUYER")).toBeInTheDocument();
    expect(getToken()).toBe("tok-login");
    expect(JSON.parse(String(fetchMock.mock.calls[0][1]?.body))).toEqual({
      email: "ana@ex.com", password: "segredo123",
    });
  });

  it("login com erro propaga o ApiError e continua anônimo", async () => {
    mockApi({ "POST /api/users/login": () => json(401, { detail: "Invalid email or password" }) });
    renderAuth();
    await userEvent.click(screen.getByRole("button", { name: "login" }));
    expect(await screen.findByText("Invalid email or password")).toBeInTheDocument();
    expect(screen.getByTestId("user")).toHaveTextContent("anônimo");
    expect(getToken()).toBeFalsy();
  });

  it("register cadastra e depois faz login", async () => {
    const fetchMock = mockApi({
      "POST /api/users/register": () => json(201, BUYER),
      "POST /api/users/login": () => json(200, loginOut(BUYER, "tok-reg")),
    });
    renderAuth();
    await userEvent.click(screen.getByRole("button", { name: "register" }));
    expect(await screen.findByText("Ana Compradora|BUYER")).toBeInTheDocument();
    const paths = fetchMock.mock.calls.map(([input]) => new URL(String(input)).pathname);
    expect(paths).toEqual(["/api/users/register", "/api/users/login"]);
    expect(JSON.parse(String(fetchMock.mock.calls[0][1]?.body))).toEqual({
      name: "Ana Compradora", email: "ana@ex.com", password: "segredo123", role: "BUYER",
    });
    expect(getToken()).toBe("tok-reg");
  });

  it("logout limpa o usuário e o token", async () => {
    mockApi({ "POST /api/users/login": () => json(200, loginOut(BUYER, "tok-out")) });
    renderAuth();
    await userEvent.click(screen.getByRole("button", { name: "login" }));
    await screen.findByText("Ana Compradora|BUYER");
    await userEvent.click(screen.getByRole("button", { name: "logout" }));
    expect(await screen.findByText("anônimo")).toBeInTheDocument();
    expect(getToken()).toBeFalsy();
  });

  it("carrega /api/users/me com o token salvo", async () => {
    setToken("tok-salvo");
    const fetchMock = mockApi({ "GET /api/users/me": () => json(200, SELLER) });
    renderAuth();
    expect(await screen.findByText("Seu Vendedor|SELLER")).toBeInTheDocument();
    expect(header(fetchMock.mock.calls[0][1], "Authorization")).toBe("Bearer tok-salvo");
  });

  it("um 401 em qualquer chamada desloga", async () => {
    mockApi({
      "POST /api/users/login": () => json(200, loginOut(BUYER, "tok-401")),
      "GET /api/cart": () => json(401, { detail: "Token expired" }),
    });
    renderAuth();
    await userEvent.click(screen.getByRole("button", { name: "login" }));
    await screen.findByText("Ana Compradora|BUYER");
    await userEvent.click(screen.getByRole("button", { name: "protegido" }));
    expect(await screen.findByText("anônimo")).toBeInTheDocument();
    expect(getToken()).toBeFalsy();
  });
});

// ---------- App: rotas e RequireAuth ----------

const PUBLIC: [string, string][] = [
  ["/", "Home"],
  ["/search?q=livro", "Busca"],
  ["/products/1", "Produto"],
  ["/signin", "Entrar"],
  ["/register", "Criar conta"],
  ["/rota-que-nao-existe", "Página não encontrada"],
];

const PROTECTED: [string, string][] = [
  ["/cart", "Carrinho"],
  ["/checkout", "Finalizar compra"],
  ["/orders", "Meus pedidos"],
  ["/orders/7", "Pedido"],
  ["/account", "Minha conta"],
];

describe("App", () => {
  it.each(PUBLIC)("rota pública %s mostra o título %s", async (path, title) => {
    mockApi({});
    renderApp(path);
    expect(await screen.findByRole("heading", { level: 1, name: title })).toBeInTheDocument();
  });

  it.each([...PROTECTED, ["/seller", "Painel do vendedor"]])(
    "deslogado, %s redireciona para /signin?next=",
    async (path) => {
      mockApi({});
      renderApp(path);
      expect(await screen.findByRole("heading", { level: 1, name: "Entrar" })).toBeInTheDocument();
      const location = currentLocation();
      expect(location.pathname).toBe("/signin");
      expect(location.searchParams.get("next")).toBe(path);
    },
  );

  it.each(PROTECTED)("logado, %s mostra o título %s", async (path, title) => {
    setToken("tok-buyer");
    mockApi({ "GET /api/users/me": () => json(200, BUYER) });
    renderApp(path);
    expect(await screen.findByRole("heading", { level: 1, name: title })).toBeInTheDocument();
    expect(currentLocation().pathname).toBe(path);
  });

  it("comprador em /seller volta para /", async () => {
    setToken("tok-buyer");
    mockApi({ "GET /api/users/me": () => json(200, BUYER) });
    renderApp("/seller");
    expect(await screen.findByRole("heading", { level: 1, name: "Home" })).toBeInTheDocument();
    expect(currentLocation().pathname).toBe("/");
  });

  it("vendedor acessa /seller", async () => {
    setToken("tok-seller");
    mockApi({ "GET /api/users/me": () => json(200, SELLER) });
    renderApp("/seller");
    expect(
      await screen.findByRole("heading", { level: 1, name: "Painel do vendedor" }),
    ).toBeInTheDocument();
  });

  it("enquanto carrega o usuário, a rota protegida não renderiza nem redireciona", async () => {
    setToken("tok-lento");
    mockApi({ "GET /api/users/me": () => new Promise<Response>(() => {}) });
    renderApp("/cart");
    await new Promise((resolve) => setTimeout(resolve, 50));
    expect(screen.queryByRole("heading", { level: 1 })).not.toBeInTheDocument();
    expect(currentLocation().pathname).toBe("/cart");
  });

  it("token salvo inválido: desloga e manda para /signin", async () => {
    setToken("tok-velho");
    mockApi({ "GET /api/users/me": () => json(401, { detail: "Token expired" }) });
    renderApp("/orders");
    expect(await screen.findByRole("heading", { level: 1, name: "Entrar" })).toBeInTheDocument();
    expect(currentLocation().searchParams.get("next")).toBe("/orders");
    await waitFor(() => expect(getToken()).toBeFalsy());
  });
});
