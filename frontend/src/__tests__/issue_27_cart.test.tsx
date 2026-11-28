import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, useLocation } from "react-router-dom";

import App from "../App";
import { AuthProvider } from "../auth/AuthContext";
import { CartProvider, useCart } from "../cart/CartContext";
import { setToken } from "../api/token";
import type { Product } from "../api/types";

// ---------- helpers ----------

type Handler = (url: URL, init: RequestInit | undefined) => Response | Promise<Response>;

const BUYER = {
  id: 1, name: "Ana Compradora", email: "ana@ex.com", role: "BUYER",
  created_at: "2026-01-01T00:00:00Z",
};

function product(overrides: Partial<Product> = {}): Product {
  return {
    id: 7, name: "Fone Bluetooth Zumbido", description: null, price_cents: 1320,
    list_price_cents: null, stock: 50, category: "Eletrônicos", image_url: "https://img.ex/fone.jpg",
    brand: "Zumbido", warranty_months: null, model_number: null, seller_id: 2,
    average_rating: 0, review_count: 0, created_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

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

function cartCalls(fetchMock: ReturnType<typeof mockApi>) {
  return fetchMock.mock.calls.filter(([input]) => new URL(String(input)).pathname.startsWith("/api/cart"));
}

function bodyOf(call: [RequestInfo | URL, RequestInit | undefined]) {
  return JSON.parse(String(call[1]?.body));
}

// ---------- carrinho falso (imita o backend) ----------

interface Line {
  product_id: number; product_name: string; image_url: string | null;
  unit_price_cents: number; quantity: number; saved_for_later: boolean;
}

const FONE: Line = {
  product_id: 7, product_name: "Fone Bluetooth Zumbido", image_url: "https://img.ex/fone.jpg",
  unit_price_cents: 1320, quantity: 2, saved_for_later: false,
};
const CABO: Line = {
  product_id: 8, product_name: "Cabo USB-C Trançado", image_url: "https://img.ex/cabo.jpg",
  unit_price_cents: 2500, quantity: 1, saved_for_later: false,
};

function view(lines: Line[]) {
  const asItem = (l: Line) => ({ ...l, line_total_cents: l.unit_price_cents * l.quantity });
  const items = lines.filter((l) => !l.saved_for_later);
  return {
    user_id: 1,
    items: items.map(asItem),
    saved_for_later: lines.filter((l) => l.saved_for_later).map(asItem),
    item_count: items.reduce((n, l) => n + l.quantity, 0),
    total_cents: items.reduce((n, l) => n + l.unit_price_cents * l.quantity, 0),
  };
}

/** Rotas /api/cart/1/... sobre um carrinho em memória, para os produtos 7 e 8. */
function cartRoutes(initial: Line[]): Record<string, Handler> {
  let lines = initial.map((l) => ({ ...l }));
  const find = (id: number) => lines.find((l) => l.product_id === id);
  const routes: Record<string, Handler> = {
    "GET /api/cart/1": () => json(200, view(lines)),
    "DELETE /api/cart/1": () => {
      lines = [];
      return json(200, view(lines));
    },
    "POST /api/cart/1/items": (_url, init) => {
      const { product_id, quantity } = JSON.parse(String(init?.body));
      const line = find(product_id);
      if (line) {
        line.quantity += quantity;
        line.saved_for_later = false;
      } else {
        lines.push({ ...FONE, product_id, quantity });
      }
      return json(200, view(lines));
    },
  };
  for (const id of [7, 8]) {
    routes[`PUT /api/cart/1/items/${id}`] = (_url, init) => {
      find(id)!.quantity = JSON.parse(String(init?.body)).quantity;
      return json(200, view(lines));
    };
    routes[`DELETE /api/cart/1/items/${id}`] = () => {
      lines = lines.filter((l) => l.product_id !== id);
      return json(200, view(lines));
    };
    routes[`POST /api/cart/1/items/${id}/save-for-later`] = () => {
      find(id)!.saved_for_later = true;
      return json(200, view(lines));
    };
    routes[`POST /api/cart/1/items/${id}/move-to-cart`] = () => {
      find(id)!.saved_for_later = false;
      return json(200, view(lines));
    };
  }
  return routes;
}

// ---------- render ----------

function LocationProbe() {
  const location = useLocation();
  return <div data-testid="location">{location.pathname + location.search}</div>;
}

function renderApp(path: string, routes: Record<string, Handler>, { loggedIn = true } = {}) {
  if (loggedIn) setToken("tok-carrinho");
  const fetchMock = mockApi({
    ...(loggedIn ? { "GET /api/users/me": () => json(200, BUYER) } : {}),
    ...routes,
  });
  render(
    <MemoryRouter initialEntries={[path]}>
      <App />
      <LocationProbe />
    </MemoryRouter>,
  );
  return fetchMock;
}

function currentLocation(): URL {
  return new URL(screen.getByTestId("location").textContent ?? "", "http://app");
}

function hrefOf(link: HTMLElement): URL {
  return new URL(link.getAttribute("href") ?? "", "http://app");
}

const header = () => within(screen.getByRole("banner"));
const page = () => within(screen.getByRole("main"));

/** A linha (<li>) do carrinho que tem o link com o nome do produto. */
function row(name: string, scope = page()) {
  const li = scope.getByRole("link", { name }).closest("li");
  if (!li) throw new Error(`O link "${name}" não está dentro de um <li>`);
  return within(li);
}

beforeEach(() => {
  localStorage.clear();
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

// ---------- CartContext ----------

/** Mostra o estado do useCart() e expõe as operações em botões. */
function CartProbe() {
  const cart = useCart();
  return (
    <div>
      <div data-testid="count">{cart.cart ? String(cart.cart.item_count) : "null"}</div>
      <button onClick={() => cart.addItem(7, 1)}>probe-add</button>
      <button onClick={() => cart.updateQuantity(7, 5)}>probe-update</button>
      <button onClick={() => cart.removeItem(7)}>probe-remove</button>
      <button onClick={() => cart.saveForLater(7)}>probe-save</button>
      <button onClick={() => cart.moveToCart(7)}>probe-move</button>
      <button onClick={() => cart.clear()}>probe-clear</button>
      <button onClick={() => cart.refresh()}>probe-refresh</button>
    </div>
  );
}

function renderProbe(routes: Record<string, Handler>, { loggedIn = true } = {}) {
  if (loggedIn) setToken("tok-carrinho");
  const fetchMock = mockApi({
    ...(loggedIn ? { "GET /api/users/me": () => json(200, BUYER) } : {}),
    ...routes,
  });
  render(
    <MemoryRouter>
      <AuthProvider>
        <CartProvider>
          <CartProbe />
        </CartProvider>
      </AuthProvider>
    </MemoryRouter>,
  );
  return fetchMock;
}

const count = () => screen.getByTestId("count").textContent;

describe("CartContext", () => {
  it("logado: carrega GET /api/cart/{user.id}", async () => {
    const fetchMock = renderProbe(cartRoutes([FONE, CABO]));
    await waitFor(() => expect(count()).toBe("3"));
    expect(callsTo(fetchMock, "GET", "/api/cart/1")).toHaveLength(1);
  });

  it("deslogado: cart é null e as operações não chamam a API", async () => {
    const fetchMock = renderProbe(cartRoutes([FONE]), { loggedIn: false });
    for (const name of ["probe-add", "probe-update", "probe-remove", "probe-save", "probe-move", "probe-clear", "probe-refresh"]) {
      await userEvent.click(screen.getByRole("button", { name }));
    }
    expect(count()).toBe("null");
    expect(cartCalls(fetchMock)).toHaveLength(0);
  });

  it("cada operação chama a rota certa e troca o cart pela resposta", async () => {
    const fetchMock = renderProbe(cartRoutes([FONE]));
    await waitFor(() => expect(count()).toBe("2"));

    await userEvent.click(screen.getByRole("button", { name: "probe-add" }));
    await waitFor(() => expect(count()).toBe("3"));
    expect(bodyOf(callsTo(fetchMock, "POST", "/api/cart/1/items")[0])).toEqual({ product_id: 7, quantity: 1 });

    await userEvent.click(screen.getByRole("button", { name: "probe-update" }));
    await waitFor(() => expect(count()).toBe("5"));
    expect(bodyOf(callsTo(fetchMock, "PUT", "/api/cart/1/items/7")[0])).toEqual({ quantity: 5 });

    await userEvent.click(screen.getByRole("button", { name: "probe-save" }));
    await waitFor(() => expect(count()).toBe("0"));
    expect(callsTo(fetchMock, "POST", "/api/cart/1/items/7/save-for-later")).toHaveLength(1);

    await userEvent.click(screen.getByRole("button", { name: "probe-move" }));
    await waitFor(() => expect(count()).toBe("5"));
    expect(callsTo(fetchMock, "POST", "/api/cart/1/items/7/move-to-cart")).toHaveLength(1);

    await userEvent.click(screen.getByRole("button", { name: "probe-remove" }));
    await waitFor(() => expect(count()).toBe("0"));
    expect(callsTo(fetchMock, "DELETE", "/api/cart/1/items/7")).toHaveLength(1);
  });

  it("clear() chama DELETE /api/cart/{user.id} e refresh() recarrega", async () => {
    const fetchMock = renderProbe(cartRoutes([FONE, CABO]));
    await waitFor(() => expect(count()).toBe("3"));
    await userEvent.click(screen.getByRole("button", { name: "probe-clear" }));
    await waitFor(() => expect(count()).toBe("0"));
    expect(callsTo(fetchMock, "DELETE", "/api/cart/1")).toHaveLength(1);
    await userEvent.click(screen.getByRole("button", { name: "probe-refresh" }));
    await waitFor(() => expect(callsTo(fetchMock, "GET", "/api/cart/1")).toHaveLength(2));
  });
});

// ---------- Header ----------

describe("Header", () => {
  it("logado: link Cart para /cart com o número de itens no nome acessível", async () => {
    renderApp("/rota-que-nao-existe", cartRoutes([FONE, CABO]));
    const link = await header().findByRole("link", { name: "Cart, 3 items" });
    expect(hrefOf(link).pathname).toBe("/cart");
    expect(link).toHaveTextContent("3");
  });

  it("com 1 item usa o singular", async () => {
    renderApp("/rota-que-nao-existe", cartRoutes([CABO]));
    expect(await header().findByRole("link", { name: "Cart, 1 item" })).toBeInTheDocument();
  });

  it("deslogado: Cart com 0 itens e nenhuma chamada ao carrinho", async () => {
    const fetchMock = renderApp("/rota-que-nao-existe", {}, { loggedIn: false });
    const link = await header().findByRole("link", { name: "Cart, 0 items" });
    expect(hrefOf(link).pathname).toBe("/cart");
    expect(cartCalls(fetchMock)).toHaveLength(0);
  });

  it("erro ao carregar o carrinho não desloga: Cart com 0 itens", async () => {
    renderApp("/rota-que-nao-existe", { "GET /api/cart/1": () => json(500, { detail: "Internal error" }) });
    expect(await header().findByText("Ana Compradora")).toBeInTheDocument();
    expect(header().getByRole("link", { name: "Cart, 0 items" })).toBeInTheDocument();
  });

  it("Sign out zera o contador", async () => {
    renderApp("/rota-que-nao-existe", cartRoutes([FONE, CABO]));
    await header().findByRole("link", { name: "Cart, 3 items" });
    await userEvent.click(header().getByRole("button", { name: "Sign out" }));
    expect(await header().findByRole("link", { name: "Cart, 0 items" })).toBeInTheDocument();
  });

  it("ao entrar, carrega o carrinho do usuário novo", async () => {
    const fetchMock = renderApp("/signin", {
      ...cartRoutes([FONE, CABO]),
      "POST /api/users/login": () =>
        json(200, { ...BUYER, access_token: "tok-novo", token_type: "bearer", expires_at: "2026-12-31T00:00:00Z" }),
    }, { loggedIn: false });
    await userEvent.type(await page().findByLabelText("Email"), "ana@ex.com");
    await userEvent.type(page().getByLabelText("Password"), "segredo123");
    await userEvent.click(page().getByRole("button", { name: "Sign in" }));
    expect(await header().findByRole("link", { name: "Cart, 3 items" })).toBeInTheDocument();
    expect(callsTo(fetchMock, "GET", "/api/cart/1")).toHaveLength(1);
  });
});

// ---------- Produto: buy-box ----------

function renderProductPage(overrides: Partial<Product> = {}, opts = { loggedIn: true }, lines: Line[] = []) {
  return renderApp("/products/7", {
    ...cartRoutes(lines),
    "GET /api/catalog/products/7": () => json(200, product(overrides)),
  }, opts);
}

async function buyBox() {
  await page().findByRole("heading", { level: 1, name: "Fone Bluetooth Zumbido" });
  const slot = screen.getByRole("main").querySelector<HTMLElement>('[data-slot="buy-box"]');
  if (!slot) throw new Error('Não achei o [data-slot="buy-box"]');
  return within(slot);
}

const optionValues = (select: HTMLElement) =>
  within(select).getAllByRole("option").map((o) => (o as HTMLOptionElement).value);

describe("buy-box do produto", () => {
  it("Quantity vai de 1 até 10 quando há estoque de sobra", async () => {
    renderProductPage({ stock: 50 });
    const box = await buyBox();
    const select = box.getByLabelText("Quantity");
    expect(optionValues(select)).toEqual(["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]);
    expect(select).toHaveValue("1");
  });

  it("Quantity vai só até o estoque quando ele é menor que 10", async () => {
    renderProductPage({ stock: 3 });
    const box = await buyBox();
    expect(optionValues(box.getByLabelText("Quantity"))).toEqual(["1", "2", "3"]);
  });

  it("Add to cart envia a quantidade, mostra Added to cart com View cart e atualiza o header", async () => {
    const fetchMock = renderProductPage({ stock: 50 });
    const box = await buyBox();
    await userEvent.selectOptions(box.getByLabelText("Quantity"), "2");
    await userEvent.click(box.getByRole("button", { name: "Add to cart" }));
    const message = await page().findByText("Added to cart");
    expect(message.closest('[role="status"]')).not.toBeNull();
    expect(hrefOf(page().getByRole("link", { name: "View cart" })).pathname).toBe("/cart");
    expect(bodyOf(callsTo(fetchMock, "POST", "/api/cart/1/items")[0])).toEqual({ product_id: 7, quantity: 2 });
    expect(await header().findByRole("link", { name: "Cart, 2 items" })).toBeInTheDocument();
  });

  it("deslogado: Add to cart leva para /signin?next=/products/7 sem chamar a API", async () => {
    const fetchMock = renderProductPage({ stock: 50 }, { loggedIn: false });
    const box = await buyBox();
    await userEvent.click(box.getByRole("button", { name: "Add to cart" }));
    await waitFor(() => expect(currentLocation().pathname).toBe("/signin"));
    expect(currentLocation().searchParams.get("next")).toBe("/products/7");
    expect(cartCalls(fetchMock)).toHaveLength(0);
  });

  it("esgotado: Add to cart desabilitado", async () => {
    renderProductPage({ stock: 0 });
    const box = await buyBox();
    expect(box.getByRole("button", { name: "Add to cart" })).toBeDisabled();
  });
});

// ---------- Página do carrinho ----------

function renderCart(lines: Line[]) {
  return renderApp("/cart", cartRoutes(lines));
}

async function loadedCart() {
  return page().findByRole("heading", { level: 1, name: "Cart" });
}

describe("página do carrinho", () => {
  it("lista os itens com imagem, nome como link, preço unitário e quantidade", async () => {
    renderCart([FONE, CABO]);
    await loadedCart();
    const fone = row("Fone Bluetooth Zumbido");
    expect(fone.getByRole("img", { name: "Fone Bluetooth Zumbido" })).toHaveAttribute("src", "https://img.ex/fone.jpg");
    expect(hrefOf(fone.getByRole("link", { name: "Fone Bluetooth Zumbido" })).pathname).toBe("/products/7");
    expect(fone.getByText("$13.20")).toBeInTheDocument();
    expect(fone.getByLabelText("Quantity for Fone Bluetooth Zumbido")).toHaveValue("2");
    expect(row("Cabo USB-C Trançado").getByLabelText("Quantity for Cabo USB-C Trançado")).toHaveValue("1");
  });

  it("resumo: Subtotal (N items) com o total e Proceed to checkout leva para /checkout", async () => {
    renderCart([FONE, CABO]);
    await loadedCart();
    expect(page().getByText("Subtotal (3 items)")).toBeInTheDocument();
    expect(page().getByText("$51.40")).toBeInTheDocument();
    await userEvent.click(page().getByRole("button", { name: "Proceed to checkout" }));
    await waitFor(() => expect(currentLocation().pathname).toBe("/checkout"));
  });

  it("com 1 item o resumo usa o singular", async () => {
    renderCart([CABO]);
    await loadedCart();
    expect(page().getByText("Subtotal (1 item)")).toBeInTheDocument();
  });

  it("mudar a quantidade chama o PUT e atualiza o resumo", async () => {
    const fetchMock = renderCart([FONE, CABO]);
    await loadedCart();
    await userEvent.selectOptions(row("Fone Bluetooth Zumbido").getByLabelText("Quantity for Fone Bluetooth Zumbido"), "3");
    expect(await page().findByText("Subtotal (4 items)")).toBeInTheDocument();
    expect(bodyOf(callsTo(fetchMock, "PUT", "/api/cart/1/items/7")[0])).toEqual({ quantity: 3 });
  });

  it("Remove tira o item do carrinho", async () => {
    const fetchMock = renderCart([FONE, CABO]);
    await loadedCart();
    await userEvent.click(row("Cabo USB-C Trançado").getByRole("button", { name: "Remove" }));
    await waitFor(() => expect(page().queryByRole("link", { name: "Cabo USB-C Trançado" })).toBeNull());
    expect(callsTo(fetchMock, "DELETE", "/api/cart/1/items/8")).toHaveLength(1);
    expect(page().getByText("Subtotal (2 items)")).toBeInTheDocument();
  });

  it("sem itens salvos, a seção Saved for later não aparece", async () => {
    renderCart([FONE]);
    await loadedCart();
    expect(page().queryByRole("region", { name: "Saved for later" })).toBeNull();
  });

  it("Save for later move o item para a seção Saved for later", async () => {
    const fetchMock = renderCart([FONE, CABO]);
    await loadedCart();
    await userEvent.click(row("Cabo USB-C Trançado").getByRole("button", { name: "Save for later" }));
    const saved = await page().findByRole("region", { name: "Saved for later" });
    expect(within(saved).getByRole("link", { name: "Cabo USB-C Trançado" })).toBeInTheDocument();
    expect(callsTo(fetchMock, "POST", "/api/cart/1/items/8/save-for-later")).toHaveLength(1);
    expect(page().getByText("Subtotal (2 items)")).toBeInTheDocument();
  });

  it("na seção Saved for later, Move to cart volta o item para o carrinho", async () => {
    const fetchMock = renderCart([FONE, { ...CABO, saved_for_later: true }]);
    const saved = await page().findByRole("region", { name: "Saved for later" });
    await userEvent.click(row("Cabo USB-C Trançado", within(saved)).getByRole("button", { name: "Move to cart" }));
    await waitFor(() => expect(page().queryByRole("region", { name: "Saved for later" })).toBeNull());
    expect(callsTo(fetchMock, "POST", "/api/cart/1/items/8/move-to-cart")).toHaveLength(1);
    expect(page().getByText("Subtotal (3 items)")).toBeInTheDocument();
  });

  it("na seção Saved for later, Remove apaga o item", async () => {
    const fetchMock = renderCart([FONE, { ...CABO, saved_for_later: true }]);
    const saved = await page().findByRole("region", { name: "Saved for later" });
    await userEvent.click(row("Cabo USB-C Trançado", within(saved)).getByRole("button", { name: "Remove" }));
    await waitFor(() => expect(page().queryByRole("link", { name: "Cabo USB-C Trançado" })).toBeNull());
    expect(callsTo(fetchMock, "DELETE", "/api/cart/1/items/8")).toHaveLength(1);
  });

  it("carrinho vazio: Your cart is empty, Continue shopping e checkout desabilitado", async () => {
    renderCart([]);
    expect(await page().findByRole("heading", { name: "Your cart is empty" })).toBeInTheDocument();
    expect(hrefOf(page().getByRole("link", { name: "Continue shopping" })).pathname).toBe("/");
    expect(page().getByRole("button", { name: "Proceed to checkout" })).toBeDisabled();
  });

  it("carrinho vazio com itens salvos: mostra o vazio e a seção Saved for later", async () => {
    renderCart([{ ...FONE, saved_for_later: true }]);
    expect(await page().findByRole("heading", { name: "Your cart is empty" })).toBeInTheDocument();
    const saved = page().getByRole("region", { name: "Saved for later" });
    expect(within(saved).getByRole("link", { name: "Fone Bluetooth Zumbido" })).toBeInTheDocument();
  });
});
