# `design/` — identidade visual

| Arquivo | Para quê |
|---|---|
| `tokens/tokens.css` | variáveis CSS usadas pelo painel no navegador |
| `tokens/tokens.json` | os mesmos valores, para código que gera gráfico (Python, JS) |

Os ativos de marca ficam junto do painel, porque é ele quem os serve:

| Pasta | Conteúdo |
|---|---|
| `dashboard/assets/marca/` | logos da coalizão, extraídos do regulamento |
| `dashboard/assets/fontes/` | Raleway (woff2) e a licença SIL OFL |

**O CSS é a referência.** Mudou um, muda o outro — os dois fora de sincronia
deixam a tela e os gráficos com cores diferentes.

As regras de uso (quando usar cada rampa, limites de série, tipografia,
acessibilidade) estão em
[`docs/05-identidade-visual.md`](../docs/05-identidade-visual.md).

## Antes de mudar uma cor

A paleta de séries foi verificada para daltonismo (protanopia, deuteranopia,
tritanopia) e contraste sobre o fundo branco do painel — que é o único, porque
o painel tem um modo só ([ADR 0007](../docs/adr/0007-um-modo-so.md)). **A ordem
dos slots faz parte dessa verificação**: ela é o que garante que cores vizinhas
continuem distinguíveis. Reordenar por gosto quebra a acessibilidade sem
quebrar nenhum teste.

Trocar qualquer hex exige revalidar a paleta inteira. A paleta atual vem do
regulamento do edital; os números da verificação estão em
`docs/05-identidade-visual.md`.
