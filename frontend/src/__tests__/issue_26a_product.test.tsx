import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import App from "../App";
import type { Product } from "../api/types";

// ---------- helpers ----------

type Handler = (url: URL, init: RequestInit | undefined) => Response | Promise<Response>;

function product(overrides: Partial<Product> = {}): Product {
  return {
    id: 7, name: "Fone Bluetooth Zumbido", description: "Fone sem fio com 30 horas de bateria.",
    price_cents: 1320, list_price_cents: null, stock: 50, category: "Eletrônicos",
    image_url: "https://img.ex/fone.jpg", brand: "Zumbido", warranty_months: null,
    model_number: null, seller_id: 2, average_rating: 0, review_count: 0,
    created_at: "2026-01-01T00:00:00Z",
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

/** Abre /products/7 (deslogado) com o produto do mock. */
function renderProduct(overrides: Partial<Product> = {}) {
  const fetchMock = mockApi({
    "GET /api/catalog/products/7": () => json(200, product(overrides)),
  });
  render(
    <MemoryRouter initialEntries={["/products/7"]}>
      <App />
    </MemoryRouter>,
  );
  return fetchMock;
}

const page = () => within(screen.getByRole("main"));

/** Espera o produto carregar (o <h1> com o nome). */
const loaded = () => page().findByRole("heading", { level: 1, name: "Fone Bluetooth Zumbido" });

beforeEach(() => {
  localStorage.clear();
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

// ---------- carregamento ----------

describe("carregamento", () => {
  it("busca o produto pelo id da URL", async () => {
    const fetchMock = renderProduct();
    await loaded();
    expect(callsTo(fetchMock, "GET", "/api/catalog/products/7")).toHaveLength(1);
  });

  it("404 mostra Product not found", async () => {
    mockApi({});
    render(
      <MemoryRouter initialEntries={["/products/999"]}>
        <App />
      </MemoryRouter>,
    );
    expect(await page().findByRole("heading", { name: "Product not found" })).toBeInTheDocument();
    expect(page().queryByRole("heading", { level: 1 })).toBeNull();
  });

  it("a página fica dentro do único <main> do Layout", async () => {
    renderProduct();
    await loaded();
    expect(screen.getAllByRole("main")).toHaveLength(1);
  });
});

// ---------- informações ----------

describe("informações do produto", () => {
  it("mostra imagem, nome em <h1>, marca, preço e descrição", async () => {
    renderProduct();
    await loaded();
    expect(page().getByRole("img", { name: "Fone Bluetooth Zumbido" })).toHaveAttribute(
      "src", "https://img.ex/fone.jpg",
    );
    expect(page().getByText("Zumbido")).toBeInTheDocument();
    expect(page().getByText("$13.20")).toBeInTheDocument();
    expect(page().getByText("Fone sem fio com 30 horas de bateria.")).toBeInTheDocument();
  });

  it("preço de lista maior mostra o preço antigo e o desconto", async () => {
    renderProduct({ list_price_cents: 2000 });
    await loaded();
    expect(page().getByText("$13.20")).toBeInTheDocument();
    expect(page().getByText("$20.00")).toBeInTheDocument();
    expect(page().getByText("-34%")).toBeInTheDocument();
  });

  it("com avaliações mostra o StarRating com a contagem", async () => {
    renderProduct({ average_rating: 4.5, review_count: 12 });
    await loaded();
    expect(page().getByRole("img", { name: "Rated 4.5 out of 5" })).toBeInTheDocument();
    expect(page().getByText("(12)")).toBeInTheDocument();
  });

  it("sem avaliações não mostra o StarRating", async () => {
    renderProduct({ average_rating: 0, review_count: 0 });
    await loaded();
    expect(page().queryByRole("img", { name: /^Rated / })).toBeNull();
  });
});

// ---------- detalhes ----------

describe("detalhes", () => {
  it("mostra modelo e garantia em meses quando existem", async () => {
    renderProduct({ model_number: "ZB-300", warranty_months: 12 });
    await loaded();
    expect(page().getByText("Model")).toBeInTheDocument();
    expect(page().getByText("ZB-300")).toBeInTheDocument();
    expect(page().getByText("Warranty")).toBeInTheDocument();
    expect(page().getByText("12 months")).toBeInTheDocument();
  });

  it("mostra só os detalhes que existem", async () => {
    renderProduct({ model_number: "ZB-300", warranty_months: null });
    await loaded();
    expect(page().getByText("ZB-300")).toBeInTheDocument();
    expect(page().queryByText("Warranty")).toBeNull();
  });

  it("sem modelo nem garantia, nenhum dos dois aparece", async () => {
    renderProduct({ model_number: null, warranty_months: null });
    await loaded();
    expect(page().queryByText("Model")).toBeNull();
    expect(page().queryByText("Warranty")).toBeNull();
  });
});

// ---------- disponibilidade ----------

describe("disponibilidade", () => {
  it("estoque alto: In stock, sem Only N left", async () => {
    renderProduct({ stock: 50 });
    await loaded();
    expect(page().getByText("In stock")).toBeInTheDocument();
    expect(page().queryByText(/^Only \d+ left$/)).toBeNull();
    expect(page().queryByText("Out of stock")).toBeNull();
  });

  it("estoque abaixo de 10: In stock e Only N left", async () => {
    renderProduct({ stock: 3 });
    await loaded();
    expect(page().getByText("In stock")).toBeInTheDocument();
    expect(page().getByText("Only 3 left")).toBeInTheDocument();
  });

  it("estoque 10 ainda não mostra Only N left", async () => {
    renderProduct({ stock: 10 });
    await loaded();
    expect(page().getByText("In stock")).toBeInTheDocument();
    expect(page().queryByText(/^Only \d+ left$/)).toBeNull();
  });

  it("estoque zero: Out of stock", async () => {
    renderProduct({ stock: 0 });
    await loaded();
    expect(page().getByText("Out of stock")).toBeInTheDocument();
    expect(page().queryByText("In stock")).toBeNull();
    expect(page().queryByText(/^Only \d+ left$/)).toBeNull();
  });
});

// ---------- buy-box ----------

describe("buy-box", () => {
  it("tem um único contêiner data-slot=buy-box, que a issue 27 preenche", async () => {
    renderProduct();
    await loaded();
    const slots = screen.getByRole("main").querySelectorAll('[data-slot="buy-box"]');
    expect(slots).toHaveLength(1);
    expect(slots[0].tagName).toBe("DIV");
  });
});
