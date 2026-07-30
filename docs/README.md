# Documentação — Painel Redes Bahia

| # | Documento | Para quem |
|---|---|---|
| 01 | [Arquitetura de dados](01-arquitetura-de-dados.md) | quem mexe no pipeline |
| 02 | [Rotina de atualização](02-rotina-de-atualizacao.md) | quem sobe a planilha todo dia |
| 03 | [Dicionário de dados](03-dicionario-de-dados.md) _(gerado)_ | todo mundo |
| 04 | [Indicadores do painel](04-indicadores.md) | quem define o que medir |
| 05 | [Identidade visual](05-identidade-visual.md) | quem constrói telas e gráficos |
| 06 | [Governança e LGPD](06-governanca-e-lgpd.md) | coordenação e jurídico |
| 07 | [Roteiro](07-roteiro.md) | coordenação |
| 08 | [Publicação do painel](08-publicacao-do-painel.md) | quem for hospedar o painel |
| — | [Decisões de arquitetura (ADR)](adr/) | quem precisa entender "por que assim" |

## Convenções

- **Documento gerado** traz o aviso no topo e não deve ser editado à mão. Hoje
  só o 03 é gerado (a partir de `config/fontes.yml`).
- **Decisão que muda o rumo do projeto** vira um ADR em `adr/`, com data e
  alternativas consideradas. Decisão sem ADR é preferência, não decisão.
- Tudo em português. Nomes técnicos (colunas, arquivos, comandos) em minúsculas,
  sem acento e sem espaço.
