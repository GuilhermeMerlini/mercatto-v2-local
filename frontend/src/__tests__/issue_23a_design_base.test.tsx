import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";

import { Button, Card, Input, Select } from "../components/ui";

// O vitest roda de dentro de frontend/ (harness e CI).
const FRONTEND = process.cwd();
const SRC = join(FRONTEND, "src");
const read = (...parts: string[]) => readFileSync(join(...parts), "utf-8");

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
    render(<Button type="submit" name="save" onClick={onClick}>Save</Button>);
    const button = screen.getByRole("button", { name: "Save" });
    expect(button).toHaveAttribute("type", "submit");
    expect(button).toHaveAttribute("name", "save");
    await userEvent.click(button);
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it("aceita as três variantes", () => {
    render(
      <>
        <Button variant="primary">One</Button>
        <Button variant="secondary">Two</Button>
        <Button variant="ghost">Three</Button>
      </>,
    );
    expect(screen.getAllByRole("button")).toHaveLength(3);
  });

  it("com loading fica desabilitado, com aria-busy, e não dispara o clique", async () => {
    const onClick = vi.fn();
    render(<Button loading onClick={onClick}>Send</Button>);
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
    render(<Input label="Name" name="name" defaultValue="" />);
    const input = screen.getByLabelText("Name");
    expect(input.tagName).toBe("INPUT");
    expect(input).toHaveAttribute("name", "name");
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
    render(<Input label="Email" error="Invalid email" />);
    const input = screen.getByLabelText("Email");
    expect(input).toHaveAttribute("aria-invalid", "true");
    expect(input).toHaveAccessibleDescription("Invalid email");
    expect(screen.getByText("Invalid email")).toBeInTheDocument();
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
      <Select label="Sort by" defaultValue="relevance" onChange={onChange}>
        <option value="relevance">Relevance</option>
        <option value="price_asc">Price: low to high</option>
      </Select>,
    );
    const select = screen.getByLabelText("Sort by");
    expect(select.tagName).toBe("SELECT");
    await userEvent.selectOptions(select, "price_asc");
    expect(select).toHaveValue("price_asc");
    expect(onChange).toHaveBeenCalled();
  });

  it("com erro, marca aria-invalid e descreve o campo com a mensagem", () => {
    render(
      <Select label="Quantity" error="Choose a quantity">
        <option value="1">1</option>
      </Select>,
    );
    const select = screen.getByLabelText("Quantity");
    expect(select).toHaveAttribute("aria-invalid", "true");
    expect(select).toHaveAccessibleDescription("Choose a quantity");
  });
});

// ---------- Card ----------

describe("Card", () => {
  it("renderiza os filhos e aceita o elemento em `as`", () => {
    render(
      <Card as="article">
        <p>content</p>
      </Card>,
    );
    const article = screen.getByRole("article");
    expect(article).toHaveTextContent("content");
  });

  it("é uma div por padrão", () => {
    const { container } = render(<Card>text</Card>);
    expect(container.firstElementChild?.tagName).toBe("DIV");
    expect(container).toHaveTextContent("text");
  });
});

