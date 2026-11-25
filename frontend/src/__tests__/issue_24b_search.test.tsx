import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, useLocation } from "react-router-dom";

import App from "../App";
import type { Product } from "../api/types";

// ---------- helpers ----------

type Handler = (url: URL, init: RequestInit | undefined) => Response | Promise<Response>;

function product(overrides: Partial<Product> = {}): Product {
  return {
    id: 7, name: "Fone Bluetooth Zumbido", description: null, price_cents: 1320,
    list_price_cents: null, stock: 5, category: "Eletrônicos", image_url: "https://img.ex/fone.jpg",
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

/** URLs das chamadas a um caminho da API, na ordem. */
function callsTo(fetchMock: ReturnType<typeof mockApi>, path: string): URL[] {
  return fetchMock.mock.calls
    .map(([input]) => new URL(String(input)))
    .filter((url) => url.pathname === path);
}

function searchResult(items: Product[], total = items.length, extra: object = {}) {
  return { items, total, page: 1, page_size: 20, corrected_query: null, ...extra };
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

// ---------- Busca ----------

function mockSearch(result: object = searchResult([product()], 37)) {
  return mockApi({ "GET /api/search/products": () => json(200, result) });
}

function lastSearch(fetchMock: ReturnType<typeof mockApi>): URLSearchParams {
  const calls = callsTo(fetchMock, "/api/search/products");
  expect(calls.length).toBeGreaterThan(0);
  return calls[calls.length - 1].searchParams;
}

describe("Busca", () => {
  it("busca pelo q da URL com page_size=20 e mostra título, total e cards", async () => {
    const fetchMock = mockSearch();
    renderApp("/search?q=fone");
    expect(
      await screen.findByRole("heading", { level: 1, name: 'Results for "fone"' }),
    ).toBeInTheDocument();
    expect(await screen.findByText(/37 products/)).toBeInTheDocument();
    expect(screen.getAllByRole("article")).toHaveLength(1);
    const params = lastSearch(fetchMock);
    expect(params.get("q")).toBe("fone");
    expect(params.get("page_size")).toBe("20");
    expect(params.get("page") ?? "1").toBe("1");
  });

  it("sem q, usa o nome da categoria como título", async () => {
    const fetchMock = mockSearch();
    renderApp("/search?category=Livros");
    expect(await screen.findByRole("heading", { level: 1, name: "Livros" })).toBeInTheDocument();
    expect(lastSearch(fetchMock).get("category")).toBe("Livros");
  });

  it("sem q nem categoria, o título é Todos os produtos", async () => {
    mockSearch();
    renderApp("/search");
    expect(
      await screen.findByRole("heading", { level: 1, name: "All products" }),
    ).toBeInTheDocument();
  });

  it("mostra a correção da busca quando vier", async () => {
    mockSearch(searchResult([product()], 1, { corrected_query: "fone de ouvido" }));
    renderApp("/search?q=fone%20de%20ouvdo");
    expect(
      await screen.findByText('Showing results for "fone de ouvido"'),
    ).toBeInTheDocument();
    expect(screen.getByText(/^1 product$/)).toBeInTheDocument();
  });

  it("converte preços em reais para centavos e repassa nota e ordem", async () => {
    const fetchMock = mockSearch();
    renderApp("/search?q=panela&min_price=10&max_price=99.9&min_rating=4&sort=price_asc");
    await screen.findAllByRole("article");
    const params = lastSearch(fetchMock);
    expect(params.get("min_price_cents")).toBe("1000");
    expect(params.get("max_price_cents")).toBe("9990");
    expect(params.get("min_rating")).toBe("4");
    expect(params.get("sort")).toBe("price_asc");
  });

  it("o Select de ordem tem as quatro opções e atualiza a URL voltando para a página 1", async () => {
    const fetchMock = mockSearch(searchResult([product()], 60));
    renderApp("/search?q=fone&page=3");
    const select = await screen.findByLabelText("Sort by");
    const labels = within(select).getAllByRole("option").map((o) => o.textContent);
    expect(labels).toEqual(["Relevance", "Price: low to high", "Price: high to low", "Top rated"]);
    await userEvent.selectOptions(select, "Price: high to low");
    await waitFor(() => expect(currentLocation().searchParams.get("sort")).toBe("price_desc"));
    expect(currentLocation().searchParams.get("q")).toBe("fone");
    expect(currentLocation().searchParams.get("page") ?? "1").toBe("1");
    await waitFor(() => expect(lastSearch(fetchMock).get("sort")).toBe("price_desc"));
  });

  it("o Select de avaliação mínima atualiza a URL", async () => {
    mockSearch();
    renderApp("/search?q=fone");
    const select = await screen.findByLabelText("Minimum rating");
    const labels = within(select).getAllByRole("option").map((o) => o.textContent);
    expect(labels).toEqual(["Any", "4+", "3+", "2+"]);
    await userEvent.selectOptions(select, "4+");
    await waitFor(() => expect(currentLocation().searchParams.get("min_rating")).toBe("4"));
  });

  it("o preço mínimo atualiza a URL em reais", async () => {
    mockSearch();
    renderApp("/search?q=fone&page=2");
    const input = await screen.findByLabelText("Min price");
    await userEvent.type(input, "50");
    await userEvent.tab();
    await waitFor(() => expect(currentLocation().searchParams.get("min_price")).toBe("50"));
    expect(currentLocation().searchParams.get("page") ?? "1").toBe("1");
    expect(screen.getByLabelText("Max price")).toBeInTheDocument();
  });

  it("sem resultados, mostra o EmptyState", async () => {
    mockSearch(searchResult([], 0));
    renderApp("/search?q=xyzzy");
    expect(
      await screen.findByRole("heading", { name: "No products found" }),
    ).toBeInTheDocument();
  });

  it("pagina pela URL", async () => {
    const fetchMock = mockSearch(searchResult([product()], 45));
    renderApp("/search?q=fone");
    expect(await screen.findByText("Page 1 of 3")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Next" }));
    await waitFor(() => expect(currentLocation().searchParams.get("page")).toBe("2"));
    await waitFor(() => expect(lastSearch(fetchMock).get("page")).toBe("2"));
  });

  it("mostra Spinner enquanto carrega e ErrorMessage no erro", async () => {
    mockApi({ "GET /api/search/products": () => new Promise<Response>(() => {}) });
    renderApp("/search?q=fone");
    expect(await screen.findByRole("status")).toBeInTheDocument();
    cleanup();
    mockApi({ "GET /api/search/products": () => json(500, { detail: "Internal error" }) });
    renderApp("/search?q=fone");
    expect(await screen.findByRole("alert")).toBeInTheDocument();
  });
});

