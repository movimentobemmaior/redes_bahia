# `data/published/` — a base do painel

**Gerado automaticamente. Não edite nada aqui à mão** — a próxima execução de
`make dados` sobrescreve.

É a única pasta que o painel lê, e a única que pode sair do repositório.
Colunas marcadas como `sensivel: true` no contrato nunca chegam aqui.

## O que tem

| Arquivo | O que é |
|---|---|
| `<tabela>.csv` | tabela para download e conferência |
| `<tabela>.parquet` | tabela tipada, para análise (Python, R, Power BI) |
| `<tabela>.json` | o que o painel consome no navegador |
| `historico.csv` | contagens diárias acumuladas (formato longo) |
| `manifest.json` | metadados: procedência, contagens e resultado da validação |

## `manifest.json`

O painel lê o manifesto **antes** dos dados: dá para saber se a base pode ser
confiada sem carregar uma linha.

```jsonc
{
  "data_execucao": "2026-08-01",
  "fonte": { "arquivo": "...xlsx", "hash_sha256": "...", "bytes": 11512 },
  "validacao": { "status": "com_avisos", "erros": 0, "avisos": 3, "problemas": [...] },
  "datasets": [
    { "nome": "credenciamento", "n_linhas": 13,
      "colunas_omitidas_por_sigilo": ["respondente_nome", "respondente_email"],
      "colunas": [ { "nome": "...", "tipo": "...", "preenchimento": 1.0 } ] }
  ]
}
```

`validacao.status` vale `aprovado`, `com_avisos` ou `reprovado`.

## `historico.csv`

Formato longo, uma linha por dia × tabela × agrupamento × categoria:

```csv
data_execucao,arquivo_fonte,dataset,agrupamento,categoria,metrica,valor
2026-07-30,2026-07-30_redes_bahia.xlsx,credenciamento,total,todos,n_linhas,13
2026-07-30,2026-07-30_redes_bahia.xlsx,credenciamento,status_credenciamento,Aprovado automaticamente,n_linhas,8
```

É o que permite gráfico de evolução, já que a planilha é sempre a foto de hoje.
Reexecutar no mesmo dia substitui as linhas daquele dia.

Os agrupamentos são definidos em `historico.agrupar_por`, no contrato.
