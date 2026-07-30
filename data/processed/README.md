# `data/processed/` — base interna completa

**Gerado automaticamente. Não edite à mão.**

Mesma base de `data/published/`, mas **com as colunas sigilosas** (CNPJ,
e-mail). Serve para conferência e análise interna.

## Regras

- Nada daqui vai para o painel. O painel lê apenas `data/published/`.
- Se o repositório algum dia for tornado público, esta pasta sai antes —
  e sai do histórico do git, não só da última versão.
- Ver [governança e LGPD](../../docs/06-governanca-e-lgpd.md).

## Formatos

- `.csv` — abre em qualquer lugar.
- `.parquet` — tipado e compacto; preserva a diferença entre "vazio" e "zero",
  o que o CSV não faz.
