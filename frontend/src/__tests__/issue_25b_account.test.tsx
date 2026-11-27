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

/** Abre /account logado. O /me devolve sempre o usuário "atual" do mock (muda depois do PATCH). */
function renderAccount(routes: Record<string, Handler> = {}) {
  setToken("tok-conta");
  let me = { ...BUYER };
  const fetchMock = mockApi({
    "GET /api/users/me": () => json(200, me),
    "PATCH /api/users/me": (_url, init) => {
      me = { ...me, ...JSON.parse(String(init?.body)) };
      return json(200, me);
    },
    ...routes,
  });
  render(
    <MemoryRouter initialEntries={["/account"]}>
      <App />
      <LocationProbe />
    </MemoryRouter>,
  );
  return fetchMock;
}

const page = () => within(screen.getByRole("main"));
const section = (name: string) => page().getByRole("region", { name });

beforeEach(() => {
  localStorage.clear();
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

// ---------- Personal details ----------

describe("Personal details", () => {
  it("vem preenchido com o usuário atual", async () => {
    renderAccount();
    const details = await page().findByRole("region", { name: "Personal details" });
    expect(await within(details).findByLabelText("Name")).toHaveValue("Ana Compradora");
    expect(within(details).getByLabelText("Email")).toHaveValue("ana@ex.com");
  });

  it("Save envia o PATCH, mostra Details updated e atualiza o nome no cabeçalho", async () => {
    const fetchMock = renderAccount();
    await page().findByRole("region", { name: "Personal details" });
    const name = await within(section("Personal details")).findByLabelText("Name");
    await userEvent.clear(name);
    await userEvent.type(name, "Ana Souza");
    await userEvent.click(within(section("Personal details")).getByRole("button", { name: "Save" }));
    const message = await page().findByText("Details updated");
    expect(message.closest('[role="status"]')).not.toBeNull();
    expect(bodyOf(callsTo(fetchMock, "PATCH", "/api/users/me")[0])).toMatchObject({
      name: "Ana Souza", email: "ana@ex.com",
    });
    expect(await within(screen.getByRole("banner")).findByText("Ana Souza")).toBeInTheDocument();
  });

  it("409 mostra o erro no campo Email", async () => {
    renderAccount({ "PATCH /api/users/me": () => json(409, { detail: "Email already registered" }) });
    await page().findByRole("region", { name: "Personal details" });
    const email = await within(section("Personal details")).findByLabelText("Email");
    await userEvent.clear(email);
    await userEvent.type(email, "outro@ex.com");
    await userEvent.click(within(section("Personal details")).getByRole("button", { name: "Save" }));
    await waitFor(() => expect(email).toHaveAttribute("aria-invalid", "true"));
    expect(email).toHaveAccessibleDescription("This email is already registered");
  });
});

// ---------- Change password ----------

async function fillPassword(current: string, next: string, confirm: string) {
  const area = await page().findByRole("region", { name: "Change password" });
  await userEvent.type(within(area).getByLabelText("Current password"), current);
  await userEvent.type(within(area).getByLabelText("New password"), next);
  await userEvent.type(within(area).getByLabelText("Confirm new password"), confirm);
  await userEvent.click(within(area).getByRole("button", { name: "Change password" }));
  return area;
}

describe("Change password", () => {
  it("envia o PUT, mostra Password changed e limpa os campos", async () => {
    const fetchMock = renderAccount({ "PUT /api/users/me/password": () => new Response(null, { status: 204 }) });
    const area = await fillPassword("segredo123", "novasenha456", "novasenha456");
    expect(await within(area).findByText("Password changed")).toBeInTheDocument();
    expect(bodyOf(callsTo(fetchMock, "PUT", "/api/users/me/password")[0])).toEqual({
      current_password: "segredo123", new_password: "novasenha456",
    });
    expect(within(area).getByLabelText("Current password")).toHaveValue("");
    expect(within(area).getByLabelText("New password")).toHaveValue("");
    expect(within(area).getByLabelText("Confirm new password")).toHaveValue("");
  });

  it("confirmação diferente: erro no campo e não chama a API", async () => {
    const fetchMock = renderAccount();
    const area = await fillPassword("segredo123", "novasenha456", "novasenha789");
    const confirm = within(area).getByLabelText("Confirm new password");
    expect(confirm).toHaveAttribute("aria-invalid", "true");
    expect(confirm).toHaveAccessibleDescription("Passwords do not match");
    expect(callsTo(fetchMock, "PUT", "/api/users/me/password")).toHaveLength(0);
  });

  it("400 mostra o detail no campo Current password e não desloga", async () => {
    renderAccount({
      "PUT /api/users/me/password": () => json(400, { detail: "Current password is incorrect" }),
    });
    const area = await fillPassword("errada123", "novasenha456", "novasenha456");
    const current = within(area).getByLabelText("Current password");
    await waitFor(() => expect(current).toHaveAttribute("aria-invalid", "true"));
    expect(current).toHaveAccessibleDescription("Current password is incorrect");
    expect(getToken()).toBe("tok-conta");
    expect(within(screen.getByRole("banner")).getByText("Ana Compradora")).toBeInTheDocument();
    expect(screen.getByTestId("location").textContent).toBe("/account");
  });
});
