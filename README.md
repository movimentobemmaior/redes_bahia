# Painel Redes Bahia

Monitoramento do Edital Redes Bahia — Movimento Bem Maior.

Todo dia uma planilha `.xlsm` entra em `data/raw/`. Um comando a transforma em
base validada, documentada e versionada, sobre a qual o painel é construído.

> **Piloto.** As escolhas aqui priorizam funcionar já e ser fácil de refazer.
> O que foi deliberadamente deixado de fora, e o gatilho para reconsiderar cada
> item, está em [`docs/07-roteiro.md`](docs/07-roteiro.md).

> **Repositório privado, e precisa continuar sendo:** `data/raw/` versiona as
> planilhas originais, com CNPJ e e-mail. O painel é restrito ao comitê
> ([ADR 0004](docs/adr/0004-painel-restrito-ao-comite.md)) — e repositório
> privado **não** torna um site privado, ver
> [publicação do painel](docs/08-publicacao-do-painel.md).

---

## A rotina do dia

```bash
# 1. coloque a planilha em data/raw/ com a data no nome
cp planilha.xlsm data/raw/2026-08-01_redes_bahia.xlsm

# 2. valide e publique
make dados
```

Ou, sem instalar nada: suba o arquivo pelo site do GitHub, em `data/raw/`.
O fluxo **Atualizar base** roda sozinho e devolve a base pronta.

Detalhes e o que fazer quando dá errado:
[`docs/02-rotina-de-atualizacao.md`](docs/02-rotina-de-atualizacao.md).

## Como o dado anda

```
data/raw/*.xlsm ──▶ leitura ──▶ padronização ──▶ validação ──▶ publicação
                                                     │
                                            erro? nada é publicado;
                                       o painel segue com a base de ontem
                                                     │
                              data/processed/  base completa (uso interno)
                              data/published/  base do painel (sem dado sigiloso)
```

A estrutura esperada da planilha vive em **um arquivo declarativo**,
[`config/fontes.yml`](config/fontes.yml). Dele saem a leitura, a validação, o
dicionário de dados e os metadados publicados. Adaptar o pipeline a uma
planilha nova é editar esse YAML, não o código.

> ⚠️ O contrato atual foi escrito **antes do primeiro `.xlsm` real**. Quando o
> arquivo verdadeiro chegar, rode `make perfil`: ele inspeciona a planilha e
> propõe um contrato para comparar com o atual.

## Estrutura do repositório

```
config/fontes.yml     contrato de dados: o que a planilha tem e o que precisa valer
pipeline/             leitura, padronização, validação e publicação
  ingest.py             acha e abre o .xlsm
  transform.py          limpa e converte tipos
  validate.py           aplica o contrato
  publish.py            grava as bases + manifesto + histórico
  profiling.py          inspeciona planilha desconhecida e propõe contrato
  dicionario.py         gera o dicionário de dados
data/
  raw/                  planilha de cada dia, intocada  ← você mexe aqui
  processed/            base completa (csv + parquet), inclui dado sigiloso
  published/            base do painel + manifest.json + historico.csv
design/tokens/        cores, tipografia e espaçamentos do painel
dashboard/            página de estado da base (o painel em si vem na fase 3)
docs/                 documentação, dicionário de dados e decisões (ADR)
tests/                testes, incluindo o caminho completo de ponta a ponta
scripts/              utilitários: planilha de exemplo, montagem e trava do site
```

## Comandos

| Comando | O que faz |
|---|---|
| `make dados` | **rotina diária**: valida a planilha e publica a base |
| `make validar` | confere sem publicar |
| `make perfil` | inspeciona o `.xlsm` e propõe um contrato de dados |
| `make exemplo` | gera uma planilha sintética para testar sem o arquivo real |
| `make dicionario` | regera o dicionário de dados |
| `make painel` | abre a página de estado da base em `localhost:8000` |
| `make site` | monta o pacote do painel para hospedagem e roda a trava de sigilo |
| `make teste` / `make lint` | testes e estilo |
| `make instalar` | instala as dependências |

`make` sozinho lista tudo.

## Documentação

| | |
|---|---|
| [Arquitetura de dados](docs/01-arquitetura-de-dados.md) | como o dado anda e por quê |
| [Rotina de atualização](docs/02-rotina-de-atualizacao.md) | o passo a passo do dia, e o que fazer quando falha |
| [Dicionário de dados](docs/03-dicionario-de-dados.md) | toda coluna, gerado a partir do contrato |
| [Indicadores](docs/04-indicadores.md) | o que o painel vai medir (proposta a validar) |
| [Identidade visual](docs/05-identidade-visual.md) | cor, tipografia e regras de gráfico |
| [Governança e LGPD](docs/06-governanca-e-lgpd.md) | o que é sigiloso e o que ainda precisa de decisão |
| [Roteiro](docs/07-roteiro.md) | fases, riscos e o que ficou fora do piloto |
| [Publicação do painel](docs/08-publicacao-do-painel.md) | como o painel chega ao comitê sem virar público |
| [Decisões (ADR)](docs/adr/) | por que as coisas são como são |

## Duas regras que o projeto não abre mão

**Erro bloqueia, aviso publica.** Quebra de estrutura (coluna que sumiu, chave
duplicada) impede a publicação: o painel continua com a base da última execução
válida. Quebra de conteúdo (categoria nova, valor fora da faixa) publica, mas
fica registrada no manifesto e visível na tela. O porquê está no
[ADR 0003](docs/adr/0003-erro-bloqueia-aviso-publica.md).

**Dado sigiloso não sai.** Coluna marcada como `sensivel` no contrato fica em
`data/processed/` e nunca chega a `data/published/`. Existe teste que falha se
isso for violado. Isso protege a camada publicada — `data/raw/` guarda as
planilhas como vieram, e é por isso que o repositório é privado (ver
[governança](docs/06-governanca-e-lgpd.md)). O pacote enviado para hospedagem
passa ainda por uma segunda trava, `make site`.

## Instalação (desenvolvimento)

Python 3.11 ou superior.

```bash
git clone <url-do-repositorio>
cd redes_bahia
make instalar
make exemplo && make dados   # roda o caminho completo com dado sintético
make painel                  # http://localhost:8000/dashboard/
```
