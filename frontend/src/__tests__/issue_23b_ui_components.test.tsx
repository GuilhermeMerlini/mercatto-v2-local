import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import {
  EmptyState,
  ErrorMessage,
  Pagination,
  Price,
  Spinner,
  StarRating,
} from "../components/ui";

const norm = (s: string | null | undefined) => (s ?? "").replace(/\s+/g, " ").trim();

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
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
