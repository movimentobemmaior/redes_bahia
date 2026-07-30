# `data/` — as camadas da base

| Pasta | O que é | No git? | Quem escreve | Quem lê |
|---|---|:-:|---|---|
| `raw/` | planilha original de cada dia, intocada | sim | **você** | pipeline |
| `interim/` | rascunho descartável | não | pipeline | ninguém |
| `processed/` | base completa e limpa, com dado sigiloso | sim | pipeline | análise interna |
| `published/` | base do painel, sem dado sigiloso | sim | pipeline | painel, terceiros |

**Você só mexe em `raw/`.** Todo o resto é gerado por `make dados` e
sobrescrito na próxima execução.

`raw/` ser versionado é o que torna qualquer publicação refazível: com a
planilha daquele dia e o código daquele dia, o resultado é idêntico.

Detalhes: [arquitetura de dados](../docs/01-arquitetura-de-dados.md).
