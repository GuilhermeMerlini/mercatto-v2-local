import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";

import {
  Button,
  Card,
  EmptyState,
  ErrorMessage,
  Input,
  Pagination,
  Price,
  Select,
  Spinner,
  StarRating,
} from "../components/ui";

// O vitest roda de dentro de frontend/ (harness e CI).
const FRONTEND = process.cwd();
const SRC = join(FRONTEND, "src");
const read = (...parts: string[]) => readFileSync(join(...parts), "utf-8");
const norm = (s: string | null | undefined) => (s ?? "").replace(/\s+/g, " ").trim();

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

// ---------- arquivos de design ----------

describe("arquivos de design", () => {
  it("DESIGN.md existe e é curto", () => {
    const lines = read(FRONTEND, "DESIGN.md").trim().split("\n");
    expect(lines.length).toBeGreaterThanOrEqual(30);
    expect(lines.length).toBeLessThanOrEqual(150);
  });

  it("tokens.css declara variáveis CSS em :root", () => {
    const css = read(SRC, "styles", "tokens.css");
    expect(css).toMatch(/:root\s*\{/);
    expect((css.match(/--[\w-]+\s*:/g) ?? []).length).toBeGreaterThanOrEqual(15);
  });

  it("os estilos globais tratam foco visível e movimento reduzido", () => {
    const css = read(SRC, "styles", "tokens.css") + read(SRC, "styles", "global.css");
    expect(css).toContain(":focus-visible");
    expect(css).toContain("prefers-reduced-motion");
  });

  it("main.tsx importa tokens.css e global.css", () => {
    const main = read(SRC, "main.tsx");
    expect(main).toMatch(/import\s+["'][./]*styles\/tokens\.css["']/);
    expect(main).toMatch(/import\s+["'][./]*styles\/global\.css["']/);
  });

  it("os componentes de ui não têm cores soltas (só tokens)", () => {
    const dir = join(SRC, "components", "ui");
    const files: string[] = [];
    const walk = (d: string) => {
      for (const name of readdirSync(d)) {
        const full = join(d, name);
        if (statSync(full).isDirectory()) walk(full);
        else if (/\.(css|tsx?)$/.test(name)) files.push(full);
      }
    };
    walk(dir);
    expect(files.length).toBeGreaterThan(0);
    const offenders = files.filter((f) =>
      /#[0-9a-fA-F]{3,8}\b|\b(?:rgba?|hsla?)\(/.test(read(f).replace(/\/\*[\s\S]*?\*\//g, "")),
    );
    expect(offenders).toEqual([]);
  });
});

// ---------- Button ----------

describe("Button", () => {
  it("é um botão que repassa as props de <button>", async () => {
    const onClick = vi.fn();
    render(<Button type="submit" name="salvar" onClick={onClick}>Salvar</Button>);
    const button = screen.getByRole("button", { name: "Salvar" });
    expect(button).toHaveAttribute("type", "submit");
    expect(button).toHaveAttribute("name", "salvar");
    await userEvent.click(button);
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it("aceita as três variantes", () => {
    render(
      <>
        <Button variant="primary">Um</Button>
        <Button variant="secondary">Dois</Button>
        <Button variant="ghost">Três</Button>
      </>,
    );
    expect(screen.getAllByRole("button")).toHaveLength(3);
  });

  it("com loading fica desabilitado, com aria-busy, e não dispara o clique", async () => {
    const onClick = vi.fn();
    render(<Button loading onClick={onClick}>Enviar</Button>);
    const button = screen.getByRole("button");
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute("aria-busy", "true");
    await userEvent.click(button);
    expect(onClick).not.toHaveBeenCalled();
  });

  it("sem loading não fica ocupado", () => {
    render(<Button>Ok</Button>);
    const button = screen.getByRole("button", { name: "Ok" });
    expect(button).toBeEnabled();
    expect(button).not.toHaveAttribute("aria-busy", "true");
  });
});

// ---------- Input e Select ----------

describe("Input", () => {
  it("liga o rótulo ao campo e repassa as props", async () => {
    render(<Input label="Nome" name="nome" defaultValue="" />);
    const input = screen.getByLabelText("Nome");
    expect(input.tagName).toBe("INPUT");
    expect(input).toHaveAttribute("name", "nome");
    await userEvent.type(input, "Ana");
    expect(input).toHaveValue("Ana");
  });

  it("gera ids diferentes para cada campo", () => {
    render(
      <>
        <Input label="Email" />
        <Input label="Email" />
      </>,
    );
    const [a, b] = screen.getAllByLabelText("Email");
    expect(a.id).toBeTruthy();
    expect(b.id).toBeTruthy();
    expect(a.id).not.toBe(b.id);
  });

  it("com erro, marca aria-invalid e descreve o campo com a mensagem", () => {
    render(<Input label="Email" error="Email inválido" />);
    const input = screen.getByLabelText("Email");
    expect(input).toHaveAttribute("aria-invalid", "true");
    expect(input).toHaveAccessibleDescription("Email inválido");
    expect(screen.getByText("Email inválido")).toBeInTheDocument();
  });

  it("sem erro, não fica inválido", () => {
    render(<Input label="Email" />);
    expect(screen.getByLabelText("Email")).not.toHaveAttribute("aria-invalid", "true");
  });
});

describe("Select", () => {
  it("liga o rótulo, mostra as opções e repassa onChange", async () => {
    const onChange = vi.fn();
    render(
      <Select label="Ordenar por" defaultValue="relevance" onChange={onChange}>
        <option value="relevance">Relevância</option>
        <option value="price_asc">Menor preço</option>
      </Select>,
    );
    const select = screen.getByLabelText("Ordenar por");
    expect(select.tagName).toBe("SELECT");
    await userEvent.selectOptions(select, "price_asc");
    expect(select).toHaveValue("price_asc");
    expect(onChange).toHaveBeenCalled();
  });

  it("com erro, marca aria-invalid e descreve o campo com a mensagem", () => {
    render(
      <Select label="Quantidade" error="Escolha uma quantidade">
        <option value="1">1</option>
      </Select>,
    );
    const select = screen.getByLabelText("Quantidade");
    expect(select).toHaveAttribute("aria-invalid", "true");
    expect(select).toHaveAccessibleDescription("Escolha uma quantidade");
  });
});

// ---------- Card ----------

describe("Card", () => {
  it("renderiza os filhos e aceita o elemento em `as`", () => {
    render(
      <Card as="article">
        <p>conteúdo</p>
      </Card>,
    );
    const article = screen.getByRole("article");
    expect(article).toHaveTextContent("conteúdo");
  });

  it("é uma div por padrão", () => {
    const { container } = render(<Card>texto</Card>);
    expect(container.firstElementChild?.tagName).toBe("DIV");
    expect(container).toHaveTextContent("texto");
  });
});

// ---------- Price ----------

describe("Price", () => {
  it("mostra o preço em reais", () => {
    const { container } = render(<Price cents={1320} />);
    expect(norm(container.textContent)).toContain("R$ 13,20");
    expect(container.querySelector("s")).toBeNull();
    expect(container.textContent).not.toContain("%");
  });

  it("com listCents maior, mostra o preço antigo riscado e o desconto", () => {
    const { container } = render(<Price cents={1500} listCents={2000} />);
    expect(norm(container.textContent)).toContain("R$ 15,00");
    expect(norm(container.querySelector("s")?.textContent)).toBe("R$ 20,00");
    expect(container.textContent).toContain("-25%");
  });

  it("arredonda o desconto", () => {
    // 1 - 1000/3000 = 66,67% → "-67%" (arredondado, não truncado)
    const { container } = render(<Price cents={1000} listCents={3000} />);
    expect(container.textContent).toContain("-67%");
  });

  it("com listCents igual ou menor, não mostra desconto", () => {
    const { container } = render(
      <>
        <Price cents={1000} listCents={1000} />
        <Price cents={1000} listCents={800} />
      </>,
    );
    expect(container.querySelector("s")).toBeNull();
    expect(container.textContent).not.toContain("%");
  });
});

// ---------- StarRating ----------

describe("StarRating", () => {
  it("tem role img com a nota em português", () => {
    render(<StarRating value={4.5} />);
    expect(screen.getByRole("img", { name: "Nota 4,5 de 5" })).toBeInTheDocument();
  });

  it("usa uma casa decimal", () => {
    render(
      <>
        <StarRating value={4} />
        <StarRating value={3.26} />
      </>,
    );
    expect(screen.getByRole("img", { name: "Nota 4,0 de 5" })).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "Nota 3,3 de 5" })).toBeInTheDocument();
  });

  it("mostra a contagem quando vier", () => {
    const { container } = render(<StarRating value={4.5} count={12} />);
    expect(container.textContent).toContain("(12)");
  });

  it("sem count, não mostra contagem", () => {
    const { container } = render(<StarRating value={4.5} />);
    expect(container.textContent).not.toContain("(");
  });
});

// ---------- Spinner, EmptyState, ErrorMessage ----------

describe("Spinner", () => {
  it("tem role status e o texto acessível Carregando", () => {
    render(<Spinner />);
    const status = screen.getByRole("status");
    const name = status.getAttribute("aria-label") ?? "";
    expect(`${name} ${status.textContent}`).toContain("Carregando");
  });
});

describe("EmptyState", () => {
  it("mostra o título como heading e os filhos", () => {
    render(
      <EmptyState title="Seu carrinho está vazio">
        <a href="/">Continuar comprando</a>
      </EmptyState>,
    );
    expect(screen.getByRole("heading", { name: "Seu carrinho está vazio" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Continuar comprando" })).toBeInTheDocument();
  });
});

describe("ErrorMessage", () => {
  it("tem role alert com a mensagem", () => {
    render(<ErrorMessage>Estoque insuficiente</ErrorMessage>);
    expect(screen.getByRole("alert")).toHaveTextContent("Estoque insuficiente");
  });
});

// ---------- Pagination ----------

describe("Pagination", () => {
  it("mostra a página atual e navega", async () => {
    const onChange = vi.fn();
    render(<Pagination page={2} total={50} pageSize={10} onChange={onChange} />);
    expect(screen.getByText("Página 2 de 5")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Próxima" }));
    expect(onChange).toHaveBeenLastCalledWith(3);
    await userEvent.click(screen.getByRole("button", { name: "Anterior" }));
    expect(onChange).toHaveBeenLastCalledWith(1);
  });

  it("desabilita Anterior na primeira página", () => {
    render(<Pagination page={1} total={50} pageSize={10} onChange={() => {}} />);
    expect(screen.getByRole("button", { name: "Anterior" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Próxima" })).toBeEnabled();
  });

  it("desabilita Próxima na última página e arredonda o total para cima", () => {
    render(<Pagination page={3} total={21} pageSize={10} onChange={() => {}} />);
    expect(screen.getByText("Página 3 de 3")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Próxima" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Anterior" })).toBeEnabled();
  });

  it("não renderiza nada com uma página só", () => {
    const { container } = render(
      <>
        <Pagination page={1} total={10} pageSize={10} onChange={() => {}} />
        <Pagination page={1} total={0} pageSize={10} onChange={() => {}} />
      </>,
    );
    expect(container).toBeEmptyDOMElement();
  });
});
