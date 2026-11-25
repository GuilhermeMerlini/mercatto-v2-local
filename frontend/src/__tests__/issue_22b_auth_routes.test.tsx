import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { MemoryRouter, useLocation } from "react-router-dom";

import App from "../App";
import { ApiError, api } from "../api/client";
import { getToken, setToken } from "../api/token";
import { AuthProvider, useAuth } from "../auth/AuthContext";

// ---------- helpers ----------

type Handler = (init: RequestInit | undefined) => Response | Promise<Response>;

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
// As páginas são trocadas pelas issues seguintes, então estes testes verificam a URL final
// (onde o usuário termina), e não o título de cada página.

const PUBLIC = ["/", "/search?q=livro", "/products/1", "/signin", "/register"];
const PROTECTED = ["/cart", "/checkout", "/orders", "/orders/7", "/account"];

/** Espera o app assentar (efeitos e redirecionamentos) antes de olhar a URL. */
const settle = () => new Promise((resolve) => setTimeout(resolve, 50));

describe("App", () => {
  it.each(PUBLIC)("rota pública %s abre sem login", async (path) => {
    mockApi({});
    renderApp(path);
    await settle();
    const location = currentLocation();
    expect(location.pathname + location.search).toBe(path);
  });

  it("rota desconhecida mostra Página não encontrada", async () => {
    mockApi({});
    renderApp("/rota-que-nao-existe");
    expect(
      await screen.findByRole("heading", { level: 1, name: "Página não encontrada" }),
    ).toBeInTheDocument();
  });

  it.each([...PROTECTED, "/seller"])("deslogado, %s redireciona para /signin?next=", async (path) => {
    mockApi({});
    renderApp(path);
    await waitFor(() => expect(currentLocation().pathname).toBe("/signin"));
    expect(currentLocation().searchParams.get("next")).toBe(path);
  });

  it.each(PROTECTED)("logado, %s abre sem redirecionar", async (path) => {
    setToken("tok-buyer");
    const fetchMock = mockApi({ "GET /api/users/me": () => json(200, BUYER) });
    renderApp(path);
    await waitFor(() =>
      expect(fetchMock.mock.calls.some(([input]) => String(input).endsWith("/api/users/me"))).toBe(true),
    );
    await settle();
    expect(currentLocation().pathname).toBe(path);
  });

  it("comprador em /seller volta para /", async () => {
    setToken("tok-buyer");
    mockApi({ "GET /api/users/me": () => json(200, BUYER) });
    renderApp("/seller");
    await waitFor(() => expect(currentLocation().pathname).toBe("/"));
  });

  it("vendedor acessa /seller", async () => {
    setToken("tok-seller");
    mockApi({ "GET /api/users/me": () => json(200, SELLER) });
    renderApp("/seller");
    await settle();
    await settle();
    expect(currentLocation().pathname).toBe("/seller");
  });

  it("enquanto carrega o usuário, a rota protegida não renderiza nem redireciona", async () => {
    setToken("tok-lento");
    mockApi({ "GET /api/users/me": () => new Promise<Response>(() => {}) });
    renderApp("/cart");
    await settle();
    expect(screen.queryByRole("heading", { level: 1, name: "Carrinho" })).not.toBeInTheDocument();
    expect(currentLocation().pathname).toBe("/cart");
  });

  it("token salvo inválido: desloga e manda para /signin", async () => {
    setToken("tok-velho");
    mockApi({ "GET /api/users/me": () => json(401, { detail: "Token expired" }) });
    renderApp("/orders");
    await waitFor(() => expect(currentLocation().pathname).toBe("/signin"));
    expect(currentLocation().searchParams.get("next")).toBe("/orders");
    await waitFor(() => expect(getToken()).toBeFalsy());
  });
});
