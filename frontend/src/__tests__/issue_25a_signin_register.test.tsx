import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, useLocation } from "react-router-dom";

import App from "../App";
import { getToken, setToken } from "../api/token";

// ---------- helpers ----------

type Handler = (url: URL, init: RequestInit | undefined) => Response | Promise<Response>;

const BUYER = {
  id: 1, name: "Ana Compradora", email: "ana@ex.com", role: "BUYER",
  created_at: "2026-01-01T00:00:00Z",
};

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
    const handler = routes[`${(init?.method ?? "GET").toUpperCase()} ${url.pathname}`];
    return handler ? handler(url, init) : json(404, { detail: "Not found" });
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function callsTo(fetchMock: ReturnType<typeof mockApi>, method: string, path: string) {
  return fetchMock.mock.calls.filter(
    ([input, init]) => new URL(String(input)).pathname === path && (init?.method ?? "GET").toUpperCase() === method,
  );
}

function bodyOf(call: [RequestInfo | URL, RequestInit | undefined]) {
  return JSON.parse(String(call[1]?.body));
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

/** A página (dentro do <main>), para não confundir com o cabeçalho. */
const page = () => within(screen.getByRole("main"));

beforeEach(() => {
  localStorage.clear();
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

// ---------- Sign in ----------

async function fillSignIn(email: string, password: string) {
  await userEvent.type(await page().findByLabelText("Email"), email);
  await userEvent.type(page().getByLabelText("Password"), password);
  await userEvent.click(page().getByRole("button", { name: "Sign in" }));
}

describe("Sign in", () => {
  it("entra, guarda o token e volta para /", async () => {
    const fetchMock = mockApi({ "POST /api/users/login": () => json(200, loginOut(BUYER, "tok-1")) });
    renderApp("/signin");
    await fillSignIn("ana@ex.com", "segredo123");
    await waitFor(() => expect(currentLocation().pathname).toBe("/"));
    expect(getToken()).toBe("tok-1");
    expect(bodyOf(callsTo(fetchMock, "POST", "/api/users/login")[0])).toEqual({
      email: "ana@ex.com", password: "segredo123",
    });
    expect(await within(screen.getByRole("banner")).findByText("Ana Compradora")).toBeInTheDocument();
  });

  it("volta para o next da URL", async () => {
    mockApi({
      "POST /api/users/login": () => json(200, loginOut(BUYER, "tok-2")),
      "GET /api/users/me": () => json(200, BUYER),
    });
    renderApp("/signin?next=%2Forders");
    await fillSignIn("ana@ex.com", "segredo123");
    await waitFor(() => expect(currentLocation().pathname).toBe("/orders"));
  });

  it("401 mostra Incorrect email or password e continua na página", async () => {
    mockApi({ "POST /api/users/login": () => json(401, { detail: "Invalid email or password" }) });
    renderApp("/signin");
    await fillSignIn("ana@ex.com", "errada123");
    expect(await page().findByRole("alert")).toHaveTextContent("Incorrect email or password");
    expect(currentLocation().pathname).toBe("/signin");
    expect(getToken()).toBeFalsy();
  });

  it("o botão fica ocupado enquanto envia", async () => {
    mockApi({ "POST /api/users/login": () => new Promise<Response>(() => {}) });
    renderApp("/signin");
    await fillSignIn("ana@ex.com", "segredo123");
    const button = page().getByRole("button", { name: "Sign in" });
    await waitFor(() => expect(button).toHaveAttribute("aria-busy", "true"));
    expect(button).toBeDisabled();
  });

  it("o link Create account leva para /register preservando o next", async () => {
    mockApi({});
    renderApp("/signin?next=%2Fcart");
    const link = await page().findByRole("link", { name: "Create account" });
    const href = new URL(link.getAttribute("href") ?? "", "http://app");
    expect(href.pathname).toBe("/register");
    expect(href.searchParams.get("next")).toBe("/cart");
  });

  it("já logado, redireciona para /", async () => {
    setToken("tok-salvo");
    mockApi({ "GET /api/users/me": () => json(200, BUYER) });
    renderApp("/signin");
    await waitFor(() => expect(currentLocation().pathname).toBe("/"));
  });
});

// ---------- Create account ----------

async function fillRegister(fields: { name?: string; email?: string; password?: string; confirm?: string }) {
  const { name = "Ana Compradora", email = "ana@ex.com", password = "segredo123", confirm = password } = fields;
  await userEvent.type(await page().findByLabelText("Name"), name);
  await userEvent.type(page().getByLabelText("Email"), email);
  await userEvent.type(page().getByLabelText("Password"), password);
  await userEvent.type(page().getByLabelText("Confirm password"), confirm);
}

const submitRegister = () => userEvent.click(page().getByRole("button", { name: "Create account" }));

describe("Create account", () => {
  it("tem os campos, a dica de senha e o tipo de conta com comprador marcado", async () => {
    mockApi({});
    renderApp("/register");
    expect(await page().findByLabelText("Name")).toBeInTheDocument();
    expect(page().getByLabelText("Confirm password")).toBeInTheDocument();
    expect(page().getByText("At least 8 characters")).toBeInTheDocument();
    const group = page().getByRole("group", { name: "Account type" });
    expect(within(group).getByRole("radio", { name: "I want to buy" })).toBeChecked();
    expect(within(group).getByRole("radio", { name: "I want to sell" })).not.toBeChecked();
  });

  it("cadastra, já entra e navega para o next", async () => {
    const fetchMock = mockApi({
      "POST /api/users/register": () => json(201, { ...BUYER, role: "SELLER" }),
      "POST /api/users/login": () => json(200, loginOut({ ...BUYER, role: "SELLER" }, "tok-novo")),
    });
    renderApp("/register?next=%2Fseller");
    await fillRegister({});
    await userEvent.click(page().getByRole("radio", { name: "I want to sell" }));
    await submitRegister();
    await waitFor(() => expect(currentLocation().pathname).toBe("/seller"));
    expect(bodyOf(callsTo(fetchMock, "POST", "/api/users/register")[0])).toEqual({
      name: "Ana Compradora", email: "ana@ex.com", password: "segredo123", role: "SELLER",
    });
    expect(getToken()).toBe("tok-novo");
  });

  it("sem next, vai para /", async () => {
    mockApi({
      "POST /api/users/register": () => json(201, BUYER),
      "POST /api/users/login": () => json(200, loginOut(BUYER, "tok-novo")),
    });
    renderApp("/register");
    await fillRegister({});
    await submitRegister();
    await waitFor(() => expect(currentLocation().pathname).toBe("/"));
  });

  it("senha curta: erro no campo e não chama a API", async () => {
    const fetchMock = mockApi({});
    renderApp("/register");
    await fillRegister({ password: "curta", confirm: "curta" });
    await submitRegister();
    const password = page().getByLabelText("Password");
    expect(password).toHaveAttribute("aria-invalid", "true");
    expect(password).toHaveAccessibleDescription("Password must be at least 8 characters");
    expect(callsTo(fetchMock, "POST", "/api/users/register")).toHaveLength(0);
  });

  it("senhas diferentes: erro na confirmação e não chama a API", async () => {
    const fetchMock = mockApi({});
    renderApp("/register");
    await fillRegister({ password: "segredo123", confirm: "segredo456" });
    await submitRegister();
    const confirm = page().getByLabelText("Confirm password");
    expect(confirm).toHaveAttribute("aria-invalid", "true");
    expect(confirm).toHaveAccessibleDescription("Passwords do not match");
    expect(callsTo(fetchMock, "POST", "/api/users/register")).toHaveLength(0);
  });

  it("409 mostra o erro no campo Email", async () => {
    mockApi({ "POST /api/users/register": () => json(409, { detail: "Email already registered" }) });
    renderApp("/register");
    await fillRegister({});
    await submitRegister();
    const email = page().getByLabelText("Email");
    await waitFor(() => expect(email).toHaveAttribute("aria-invalid", "true"));
    expect(email).toHaveAccessibleDescription("This email is already registered");
    expect(currentLocation().pathname).toBe("/register");
  });
});
