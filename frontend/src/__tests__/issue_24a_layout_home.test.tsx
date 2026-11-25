import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { MemoryRouter, useLocation } from "react-router-dom";

import App from "../App";
import { getToken, setToken } from "../api/token";
import type { Product } from "../api/types";
import { ProductCard } from "../components/ProductCard";

// ---------- helpers ----------

type Handler = (url: URL, init: RequestInit | undefined) => Response | Promise<Response>;

const BUYER = {
  id: 1, name: "Ana Compradora", email: "ana@ex.com", role: "BUYER",
  created_at: "2026-01-01T00:00:00Z",
};
const SELLER = { ...BUYER, id: 2, name: "Seu Vendedor", email: "vend@ex.com", role: "SELLER" };

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

function hrefOf(link: HTMLElement): URL {
  return new URL(link.getAttribute("href") ?? "", "http://app");
}

const norm = (s: string | null | undefined) => (s ?? "").replace(/\s+/g, " ").trim();

beforeEach(() => {
  localStorage.clear();
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

// ---------- Layout e Header ----------

describe("Layout", () => {
  it("tem header, main e footer em volta da página", async () => {
    mockApi({});
    renderApp("/rota-que-nao-existe");
    const main = await screen.findByRole("main");
    expect(
      within(main).getByRole("heading", { level: 1, name: "Página não encontrada" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("banner")).toBeInTheDocument();
    expect(screen.getByRole("contentinfo")).toBeInTheDocument();
  });

  it("deslogado: logo para /, busca e link Entrar", async () => {
    mockApi({});
    renderApp("/rota-que-nao-existe");
    const header = await screen.findByRole("banner");
    expect(hrefOf(within(header).getByRole("link", { name: /Mercatto/ })).pathname).toBe("/");
    const search = within(header).getByRole("search");
    expect(within(search).getByRole("textbox", { name: "Buscar produtos" })).toBeInTheDocument();
    expect(within(search).getByRole("button", { name: "Buscar" })).toBeInTheDocument();
    expect(hrefOf(within(header).getByRole("link", { name: "Entrar" })).pathname).toBe("/signin");
    expect(within(header).queryByRole("button", { name: "Sair" })).not.toBeInTheDocument();
  });

  it("a busca navega para /search?q=", async () => {
    mockApi({ "GET /api/search/products": () => json(200, searchResult([])) });
    renderApp("/rota-que-nao-existe");
    const header = await screen.findByRole("banner");
    await userEvent.type(within(header).getByRole("textbox", { name: "Buscar produtos" }), "fone bluetooth");
    await userEvent.click(within(header).getByRole("button", { name: "Buscar" }));
    await waitFor(() => expect(currentLocation().pathname).toBe("/search"));
    expect(currentLocation().searchParams.get("q")).toBe("fone bluetooth");
  });

  it("logado como comprador: nome, Meus pedidos, Minha conta e Sair", async () => {
    setToken("tok-buyer");
    mockApi({ "GET /api/users/me": () => json(200, BUYER) });
    renderApp("/rota-que-nao-existe");
    const header = await screen.findByRole("banner");
    expect(await within(header).findByText("Ana Compradora")).toBeInTheDocument();
    expect(hrefOf(within(header).getByRole("link", { name: "Meus pedidos" })).pathname).toBe("/orders");
    expect(hrefOf(within(header).getByRole("link", { name: "Minha conta" })).pathname).toBe("/account");
    expect(within(header).getByRole("button", { name: "Sair" })).toBeInTheDocument();
    expect(within(header).queryByRole("link", { name: "Entrar" })).not.toBeInTheDocument();
    expect(within(header).queryByRole("link", { name: "Painel do vendedor" })).not.toBeInTheDocument();
  });

  it("logado como vendedor: também o Painel do vendedor", async () => {
    setToken("tok-seller");
    mockApi({ "GET /api/users/me": () => json(200, SELLER) });
    renderApp("/rota-que-nao-existe");
    const header = await screen.findByRole("banner");
    const link = await within(header).findByRole("link", { name: "Painel do vendedor" });
    expect(hrefOf(link).pathname).toBe("/seller");
  });

  it("Sair desloga", async () => {
    setToken("tok-buyer");
    mockApi({ "GET /api/users/me": () => json(200, BUYER) });
    renderApp("/rota-que-nao-existe");
    const header = await screen.findByRole("banner");
    await userEvent.click(await within(header).findByRole("button", { name: "Sair" }));
    expect(await within(header).findByRole("link", { name: "Entrar" })).toBeInTheDocument();
    expect(getToken()).toBeFalsy();
  });
});

// ---------- ProductCard ----------

function renderCard(p: Product) {
  return render(
    <MemoryRouter>
      <ProductCard product={p} />
    </MemoryRouter>,
  );
}

describe("ProductCard", () => {
  it("é um article com imagem, nome como link e preço", () => {
    renderCard(product());
    const card = screen.getByRole("article");
    const img = within(card).getByRole("img", { name: "Fone Bluetooth Zumbido" });
    expect(img).toHaveAttribute("src", "https://img.ex/fone.jpg");
    expect(img).toHaveAttribute("loading", "lazy");
    // A imagem também pode ser link; todo link com o nome do produto leva a ele.
    const links = within(card).getAllByRole("link", { name: /Fone Bluetooth Zumbido/ });
    for (const link of links) expect(hrefOf(link).pathname).toBe("/products/7");
    expect(norm(card.textContent)).toContain("R$ 13,20");
  });

  it("mostra o desconto quando há preço original", () => {
    renderCard(product({ price_cents: 1500, list_price_cents: 2000 }));
    const card = screen.getByRole("article");
    expect(norm(card.querySelector("s")?.textContent)).toBe("R$ 20,00");
    expect(card.textContent).toContain("-25%");
  });

  it("sem image_url, mostra um placeholder sem imagem quebrada", () => {
    const { container } = renderCard(product({ image_url: null }));
    expect(screen.getByRole("article")).toBeInTheDocument();
    expect(container.querySelector('img:not([src]), img[src=""], img[src="null"]')).toBeNull();
  });

  it("só mostra a nota quando há avaliações", () => {
    renderCard(product({ average_rating: 0, review_count: 0 }));
    expect(screen.queryByRole("img", { name: /^Nota/ })).not.toBeInTheDocument();
    cleanup();
    renderCard(product({ average_rating: 4.5, review_count: 3 }));
    expect(screen.getByRole("img", { name: "Nota 4,5 de 5" })).toBeInTheDocument();
    expect(screen.getByRole("article").textContent).toContain("(3)");
  });

  it("mostra Esgotado só sem estoque", () => {
    renderCard(product({ stock: 5 }));
    expect(screen.queryByText("Esgotado")).not.toBeInTheDocument();
    cleanup();
    renderCard(product({ stock: 0 }));
    expect(screen.getByText("Esgotado")).toBeInTheDocument();
  });
});

// ---------- Home ----------

describe("Home", () => {
  it("mostra as categorias como links para a busca", async () => {
    mockApi({
      "GET /api/catalog/categories": () => json(200, ["Livros", "Casa e Jardim"]),
      "GET /api/catalog/products": () => json(200, { items: [], total: 0, page: 1, page_size: 12 }),
    });
    renderApp("/");
    const livros = await screen.findByRole("link", { name: "Livros" });
    expect(hrefOf(livros).pathname).toBe("/search");
    expect(hrefOf(livros).searchParams.get("category")).toBe("Livros");
    const casa = screen.getByRole("link", { name: "Casa e Jardim" });
    expect(hrefOf(casa).searchParams.get("category")).toBe("Casa e Jardim");
  });

  it("carrega 12 produtos e mostra um card para cada", async () => {
    const fetchMock = mockApi({
      "GET /api/catalog/categories": () => json(200, []),
      "GET /api/catalog/products": () =>
        json(200, {
          items: [product({ id: 1, name: "Caderno Kraft" }), product({ id: 2, name: "Panela de Ferro" })],
          total: 2, page: 1, page_size: 12,
        }),
    });
    renderApp("/");
    expect((await screen.findAllByRole("link", { name: /Caderno Kraft/ })).length).toBeGreaterThan(0);
    expect(screen.getAllByRole("link", { name: /Panela de Ferro/ }).length).toBeGreaterThan(0);
    expect(screen.getAllByRole("article")).toHaveLength(2);
    expect(callsTo(fetchMock, "/api/catalog/products")[0].searchParams.get("page_size")).toBe("12");
  });

  it("mostra o Spinner enquanto carrega", async () => {
    mockApi({
      "GET /api/catalog/categories": () => new Promise<Response>(() => {}),
      "GET /api/catalog/products": () => new Promise<Response>(() => {}),
    });
    renderApp("/");
    expect(await screen.findByRole("status")).toBeInTheDocument();
  });

  it("mostra ErrorMessage quando a API falha", async () => {
    mockApi({
      "GET /api/catalog/categories": () => json(500, { detail: "Erro interno" }),
      "GET /api/catalog/products": () => json(500, { detail: "Erro interno" }),
    });
    renderApp("/");
    expect((await screen.findAllByRole("alert")).length).toBeGreaterThan(0);
  });
});

// ---------- estilos ----------

describe("estilos", () => {
  it("toda className usada nos componentes e páginas existe em algum .css", () => {
    const SRC = join(process.cwd(), "src");
    const files: string[] = [];
    const walk = (dir: string) => {
      for (const name of readdirSync(dir)) {
        const full = join(dir, name);
        if (statSync(full).isDirectory()) {
          if (name !== "__tests__") walk(full);
        } else files.push(full);
      }
    };
    walk(SRC);
    const css = files.filter((f) => f.endsWith(".css")).map((f) => readFileSync(f, "utf-8")).join("\n");
    const defined = new Set(Array.from(css.matchAll(/\.([a-zA-Z][\w-]*)/g), (m) => m[1]));
    const missing: string[] = [];
    for (const file of files.filter((f) => f.endsWith(".tsx"))) {
      const source = readFileSync(file, "utf-8");
      for (const m of source.matchAll(/className=(?:"([^"]*)"|\{`([^`]*)`\})/g)) {
        const classes = (m[1] ?? m[2]).replace(/\$\{[^}]*\}/g, " ").split(/\s+/).filter(Boolean);
        for (const c of classes) if (!defined.has(c)) missing.push(`${file.slice(SRC.length + 1)}: ${c}`);
      }
    }
    expect(missing).toEqual([]);
  });
});
