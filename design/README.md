# `design/` — identidade visual

| Arquivo | Para quê |
|---|---|
| `tokens/tokens.css` | variáveis CSS usadas pelo painel no navegador |
| `tokens/tokens.json` | os mesmos valores, para código que gera gráfico (Python, JS) |

**O CSS é a referência.** Mudou um, muda o outro — os dois fora de sincronia
deixam a tela e os gráficos com cores diferentes.

As regras de uso (quando usar cada rampa, limites de série, tipografia,
acessibilidade) estão em
[`docs/05-identidade-visual.md`](../docs/05-identidade-visual.md).

## Antes de mudar uma cor

A paleta de séries foi verificada para daltonismo (protanopia, deuteranopia,
tritanopia) e contraste, nos modos claro e escuro. **A ordem dos slots faz
parte dessa verificação**: ela é o que garante que cores vizinhas continuem
distinguíveis. Reordenar por gosto quebra a acessibilidade sem quebrar nenhum
teste.

Trocar qualquer hex exige revalidar a paleta inteira nos dois modos.
