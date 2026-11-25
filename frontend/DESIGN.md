# Identidade Visual do Mercatto

## 1. Personalidade

A identidade visual do Mercatto é inspirada em uma **feira de bairro vintage com elementos industriais**, misturando nostalgia e funcionalidade. A marca é acolhedora, com um toque de charme urbano e um estilo de vida que valoriza o encontro com o cotidiano. Ela **não é** uma plataforma fria e comercial, nem uma interface de e-commerce genérica. Ela é **viva, com história, e encoraja a descoberta de produtos com personalidade**. É uma experiência de compra com alma, e não apenas uma transação.

## 2. Paleta

- `--color-primary`: #1d4e8c (azul escuro para ações principais, como botões e links)
- `--color-primary-hover`: #1e3a8a (um tom mais escuro para hover e foco)
- `--color-on-primary`: #ffffff (branco para texto em botões primários)
- `--color-secondary`: #d97706 (laranja amarelado para ações secundárias e destaque)
- `--color-background`: #fafafa (cinza claro para o fundo da página)
- `--color-surface`: #ffffff (branco para superfícies como cards e formulários)
- `--color-error`: #dc2626 (vermelho para erros e alertas)
- `--color-success`: #15803d (verde para feedbacks positivos)
- `--color-border`: #8b8f97 (cinza para bordas)
- `--color-text`: #1f2937 (cinza escuro para texto principal)
- `--color-text-light`: #6b7280 (cinza médio para texto secundário)

Contraste WCAG AA (texto normal ≥ 4.5:1; gráficos e bordas de campo ≥ 3:1):
- `--color-text` com `--color-background`: 14.06:1
- `--color-text-light` com `--color-background`: 4.63:1
- `--color-on-primary` com `--color-primary`: 8.33:1
- `--color-text` com `--color-secondary` (botão secundário): 4.61:1
- `--color-secondary` com `--color-surface` (estrelas): 3.19:1
- `--color-error` com `--color-background`: 4.63:1
- `--color-on-primary` com `--color-error`: 4.83:1
- `--color-success` com `--color-background`: 4.81:1
- `--color-on-primary` com `--color-success` (selo de desconto): 5.02:1
- `--color-border` com `--color-surface` (borda de campo): 3.24:1

## 3. Tipografia

Família de fonte: **Inter** (Google Fonts, pesos 400, 600 e 700, carregada no `index.html`), com fallback para a fonte do sistema.

- `--font-size-h1`: 2.25rem (36px)
- `--font-size-h2`: 1.875rem (30px)
- `--font-size-h3`: 1.5rem (24px)
- `--font-size-body-large`: 1.25rem (20px)
- `--font-size-body`: 1rem (16px)
- `--font-size-body-small`: 0.875rem (14px)
- `--font-size-caption`: 0.75rem (12px)
- `--line-height-h1`: 1.2
- `--line-height-h2`: 1.25
- `--line-height-h3`: 1.3
- `--line-height-body-large`: 1.4
- `--line-height-body`: 1.5
- `--line-height-body-small`: 1.4
- `--line-height-caption`: 1.3
- `--font-weight-bold`: 700
- `--font-weight-semibold`: 600
- `--font-weight-normal`: 400

## 4. Espaçamento

- `--spacing-xs`: 0.25rem (4px)
- `--spacing-sm`: 0.5rem (8px)
- `--spacing-md`: 1rem (16px)
- `--spacing-lg`: 1.5rem (24px)
- `--spacing-xl`: 2rem (32px)
- `--spacing-xxl`: 3rem (48px)

### Layout

- `--layout-max-width`: 75rem (1200px), largura máxima do conteúdo
- `--card-min-width`: 15.5rem (248px), largura mínima de um card na grade
- `--card-image-height`: 12.5rem (200px), altura da imagem do card de produto
- `--border-width`: 1px, espessura de todas as bordas

## 5. Raios e sombras

- `--radius-small`: 0.25rem (4px)
- `--radius-medium`: 0.5rem (8px)
- `--radius-large`: 0.75rem (12px)
- `--shadow-small`: 0 1px 2px 0 rgba(0, 0, 0, 0.05)
- `--shadow-medium`: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)
- `--shadow-large`: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)

## 6. Movimento

- `--transition`: 0.2s ease-in-out
- `--transition-reduced`: none

Animações:
- Efeitos de hover em botões e cards.
- Transições suaves de estado em formulários e navegação.
- Comportamento com `prefers-reduced-motion`: o `tokens.css` troca `--transition` por `--transition-reduced`, e as transições somem. Animações contínuas (como o spinner) param ou ficam bem mais lentas.

## 7. Regras de composição

### Card de produto
- Imagem com bordas arredondadas (--radius-medium)
- Nome em `--font-size-body-large` em `--color-text`
- Preço em `--font-size-h3` com `--color-primary`
- Nota em estrelas com `--color-secondary` e texto em `--font-size-body-small`
- "Out of stock" com fundo em `--color-error` e texto em `--color-on-primary`

### Preço com desconto
- Preço atual em `--font-size-h3` com `--color-primary`
- Preço antigo riscado em `--color-text-light`
- Selos de desconto em `--color-success` e texto em `--color-on-primary`

### Nota em estrelas
- Estrelas em `--color-secondary`
- Texto com contagem em `--font-size-body-small` e `--color-text`

### Botões
- Primary: `--color-primary` com `--color-on-primary` (usado em ações principais)
- Secondary: `--color-secondary` com `--color-text` (usado em ações secundárias)
- Ghost: sem fundo, apenas borda em `--color-border` e `--color-text`

### Campos de formulário
- Input com borda em `--color-border`, fundo em `--color-surface`
- Mensagem de erro em `--color-error` com `--font-size-caption`

### Estado vazio
- Título em `--font-size-h3` em `--color-text`
- Botão secundário com `--color-secondary`

### Mensagem de erro geral
- Fundo em `--color-error`, texto em `--color-on-primary`

### Carregando
- Spinner com animação de rotação de 0.8s, com `--color-primary`

### Paginação
- Botão "Previous" e "Next" com borda em `--color-border`
- Texto de página em `--font-size-body` e `--color-text`

## 8. O que NÃO fazer

- Não usar cor, tamanho, espaçamento, raio ou sombra sem token: nada de hex, `rgb()` ou `px` soltos nos componentes.
- Não usar branco (`--color-on-primary`) sobre `--color-secondary`: dá 3.19:1. O texto sobre ele é sempre `--color-text`.
- Não usar `--color-secondary` nem `--color-border` como cor de texto (abaixo de 4.5:1 no fundo).
- Não usar `--color-text-light` sobre fundos coloridos (`--color-secondary`, `--color-error`, `--color-success`).
- Não remover o contorno de foco (`outline: none`) sem pôr outro indicador igualmente visível.
- Não comunicar estado só por cor: erro tem texto, desconto tem o percentual, "Out of stock" tem a palavra.
- Não usar bibliotecas de ícones ou de componentes; ícones simples são caracteres ou CSS.
- Não animar layout (largura, altura, posição); anime só cor, opacidade, sombra e `transform`.
- Não imitar cores, logo ou cabeçalho de outros varejistas.
