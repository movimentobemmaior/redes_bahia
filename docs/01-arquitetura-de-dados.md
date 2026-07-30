# Arquitetura de dados

## O problema

A planilha `.xlsx` do edital é preenchida por pessoas, muda de formato sem
aviso e é a foto de um momento. Um painel construído direto em cima dela quebra
na primeira coluna renomeada e não consegue mostrar evolução no tempo.

A solução aqui é colocar **uma camada de contrato** entre a planilha e o painel.

## O caminho do dado

```
  data/raw/2026-07-30_redes_bahia.xlsx        planilha do dia, como veio
            │
            │  1. leitura         pipeline/ingest.py
            ▼
        células cruas                          nada é limpo ainda
            │
            │  2. padronização    pipeline/transform.py
            ▼
     tabelas previsíveis                       tipos, nomes e formatos corrigidos
            │
            │  3. validação       pipeline/validate.py
            ▼
     erro? ──sim──▶ publicação bloqueada, painel segue com a base de ontem
            │
            não
            │  4. publicação      pipeline/publish.py
            ▼
  data/processed/   base completa (inclui dado sigiloso) — uso interno
  data/published/   base do painel (sem dado sigiloso) + manifesto + histórico
            │
            ▼
        dashboard/                             lê apenas data/published/
```

Cada etapa tem uma responsabilidade e uma só. Quando algo dá errado, o
relatório diz em qual delas.

## As camadas de dados

| Pasta | O que é | Versionado? | Quem lê |
|---|---|---|---|
| `data/raw/` | planilha original de cada dia, intocada | **sim** | pipeline |
| `data/interim/` | rascunho descartável | não | ninguém |
| `data/processed/` | base completa e limpa (`.csv` + `.parquet`) | **sim** | análises internas |
| `data/published/` | base do painel, sem dado sigiloso | **sim** | painel, terceiros |

`data/raw/` ser versionado é o que torna qualquer publicação **refazível**: com
a planilha do dia e a versão do código daquele dia, o resultado é idêntico.

## O contrato de dados

`config/fontes.yml` descreve a planilha: quais abas viram quais tabelas, quais
colunas existem, de que tipo são, quais são obrigatórias, quais são sigilosas e
que regras precisam valer. Dele saem quatro coisas:

1. a leitura da planilha,
2. a validação,
3. o dicionário de dados (`docs/03-dicionario-de-dados.md`),
4. os metadados publicados (`data/published/manifest.json`).

Mudar o comportamento do pipeline é, quase sempre, mudar esse arquivo — não o
código.

## Erro x aviso

A distinção mais importante do projeto:

| | O que é | O que acontece |
|---|---|---|
| **erro** | quebra de estrutura: coluna sumiu, chave duplicada, aba vazia | **bloqueia** a publicação; o painel continua com a base anterior |
| **aviso** | quebra de conteúdo: categoria nova, valor fora da faixa, referência órfã | publica, registra no manifesto e fica visível no painel |

O raciocínio: dado estranho em uma linha não pode derrubar o painel inteiro,
mas dado com a estrutura quebrada não pode entrar calado. Para revisão de
dados, `make validar` com `--estrito` trata todo aviso como erro.

## O histórico

A planilha é sempre a foto de hoje. Para o painel conseguir mostrar evolução, o
pipeline grava a cada execução um resumo em `data/published/historico.csv`
(formato longo: uma linha por dia × dataset × agrupamento × categoria).

Reexecutar no mesmo dia substitui as linhas daquele dia, não duplica.

Os agrupamentos ficam em `historico.agrupar_por`, no contrato. Hoje:
`status_credenciamento`, `estado`, `representa`.

## O manifesto

`data/published/manifest.json` é o contrato de saída. O painel lê dele:

- quando a base foi atualizada e de qual arquivo (com hash SHA-256);
- quantas linhas tem cada tabela;
- o resultado da validação, com a lista de problemas;
- quais colunas foram retidas por sigilo;
- percentual de preenchimento de cada coluna.

Com isso, o painel consegue mostrar o estado da base **sem abrir os dados**.

## Formatos publicados

- **CSV** — abre em qualquer lugar, serve para download e conferência.
- **Parquet** — tipado e compacto, para análise (Python, R, Power BI).
- **JSON** — o que o painel consome no navegador.

## Limites conhecidos deste piloto

- Tudo roda em memória, com pandas. Serve confortavelmente para dezenas de
  milhares de linhas; acima disso, revisar.
- O JSON publicado carrega a tabela inteira. Passando de ~5 MB por arquivo,
  usar `publicacao.limite_linhas_json` ou publicar agregados em vez de linhas.
- Uma planilha por dia, escolhida pelo nome. Múltiplas fontes por dia exigiriam
  mudar `fonte.selecao` para `todos` e definir como combiná-las.
