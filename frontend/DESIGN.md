# Design System - Mercatto

## Personalidade
Mercatto é uma identidade moderna e acolhedora, com foco em simplicidade e clareza. Inspirado em lojas físicas de pequeno porte, busca criar uma experiência acolhedora e acessível, com um toque de originalidade. A estética é minimalista, com atenção aos detalhes e uma tipografia clara e legível.

## Paleta de Cores
- **Primary**: #2563eb (azul escuro para ações principais)
- **Secondary**: #64748b (cinza para textos secundários)
- **Background**: #f8fafc (fundo claro)
- **Surface**: #ffffff (superfície de cards e elementos)
- **Error**: #dc2626 (vermelho para erros)
- **Success**: #16a34a (verde para sucesso)
- **Border**: #e2e8f0 (borda leve)
- **Text**: #1e293b (texto principal)
- **Text Light**: #64748b (texto secundário)

## Escala Tipográfica
- **Heading 1**: 2.25rem / 2.5rem (font-weight: 700)
- **Heading 2**: 1.875rem / 2.25rem (font-weight: 700)
- **Heading 3**: 1.5rem / 1.75rem (font-weight: 600)
- **Body Large**: 1.125rem / 1.75rem (font-weight: 400)
- **Body Regular**: 1rem / 1.5rem (font-weight: 400)
- **Body Small**: 0.875rem / 1.25rem (font-weight: 400)
- **Caption**: 0.75rem / 1rem (font-weight: 400)

## Espaçamento
- **XS**: 0.25rem (4px)
- **SM**: 0.5rem (8px)
- **MD**: 1rem (16px)
- **LG**: 1.5rem (24px)
- **XL**: 2rem (32px)
- **XXL**: 3rem (48px)

## Raios e Sombras
- **Radius Small**: 0.25rem (4px)
- **Radius Medium**: 0.5rem (8px)
- **Radius Large**: 1rem (16px)
- **Shadow Small**: 0 1px 2px 0 rgba(0, 0, 0, 0.05)
- **Shadow Medium**: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1)
- **Shadow Large**: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1)

## Movimento
- **Transições**: todas as transições usam `ease-in-out` com duração de 200ms
- **Hover**: todos os elementos interativos têm transição suave
- **Redução de movimento**: respeita `prefers-reduced-motion` com `transition: none`

## Regras de Composição
- **Cards de produto**: bordas arredondadas, sombra leve, espaçamento interno de MD
- **Preços com desconto**: preço original riscado, preço final em negrito e cor primária
- **Estados vazios**: texto secundário com ícone de estado vazio, espaçamento de LG
- **Erros**: texto de erro em vermelho, borda vermelha no campo afetado

## O que não fazer
- Evitar cores fortes em excesso
- Não usar sombras muito pesadas
- Não usar animações complexas
- Não usar fontes decorativas
- Evitar contrastes muito baixos
