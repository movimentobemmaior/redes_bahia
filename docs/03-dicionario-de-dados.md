# Dicionário de dados

> **Arquivo gerado automaticamente — não edite à mão.**
> Fonte: `config/fontes.yml`. Para atualizar: `make dicionario`.
> Última geração: 2026-07-30 · versão do contrato: 1

## Como ler

- **Coluna** — nome técnico, usado nos arquivos publicados e no painel.
- **Origem** — cabeçalho correspondente na planilha `.xlsm`.
- **Tipo** — `texto`, `categoria`, `inteiro`, `decimal`, `data`, `booleano`.
- **Obr.** — obrigatória: se vier vazia, a publicação é bloqueada.
- **Sigilo** — dado pessoal/identificação: fica em `data/processed/` e **não** é publicado.
- **Preench.** — percentual preenchido na última execução do pipeline.

## `avaliacoes`

Uma linha por nota atribuída. Grão: inscrição × avaliador × critério. Permite ver dispersão entre avaliadores e desempenho por critério.

- Aba na planilha: `Avaliacoes` (cabeçalho na linha 1)
- Grão / chave: `id_inscricao`, `avaliador`, `criterio`

| Coluna | Origem | Tipo | Obr. | Sigilo | Preench. | Descrição |
|---|---|---|:-:|:-:|---:|---|
| `avaliador` | Avaliador | categoria | sim | — | — | Identificação do avaliador (código ou nome). |
| `criterio` | Critério | categoria | sim | — | — | Critério avaliado, conforme edital. |
| `data_avaliacao` | Data da Avaliação | data | — | — | — | Data em que a nota foi registrada. |
| `id_inscricao` | ID Inscrição | texto | sim | — | — | Chave estrangeira para inscricoes.id_inscricao. |
| `nota` | Nota | decimal | sim | — | — | Nota do critério (0 a 10). |

**Regras de validação**

- **unicidade** em (id_inscricao, avaliador, criterio) — duplicata bloqueia (erro).
- **faixa** de `nota`: mín. 0, máx. 10 — fora da faixa gera aviso.
- **referência**: `id_inscricao` deve existir em `inscricoes.id_inscricao` — órfão gera aviso.

## `inscricoes`

Uma linha por proposta inscrita no edital. Grão: inscrição. Base para todos os indicadores de funil, território e valores.

- Aba na planilha: `Inscricoes` (cabeçalho na linha 1)
- Grão / chave: `id_inscricao`

| Coluna | Origem | Tipo | Obr. | Sigilo | Preench. | Descrição |
|---|---|---|:-:|:-:|---:|---|
| `cnpj` | CNPJ | texto | — | 🔒 | — | CNPJ da proponente. Dado de identificação — não publicado. |
| `data_inscricao` | Data de Inscrição | data | sim | — | — | Data de envio da proposta. |
| `eixo` | Eixo | categoria | — | — | — | Eixo temático da proposta. |
| `email_contato` | E-mail de Contato | texto | — | 🔒 | — | Contato da proponente. Dado pessoal — não publicado. |
| `etapa` | Etapa | categoria | — | — | — | Etapa do processo em que a proposta se encontra. |
| `id_inscricao` | ID Inscrição | texto | sim | — | — | Identificador único da proposta no sistema de inscrição. |
| `municipio` | Município | categoria | sim | — | — | Município-sede da organização. |
| `nota_final` | Nota Final | decimal | — | — | — | Nota consolidada da avaliação (0 a 10). Vazia até ser avaliada. |
| `organizacao` | Organização | texto | sim | — | — | Nome da organização proponente. |
| `status` | Status | categoria | sim | — | — | Situação atual da proposta. |
| `territorio_identidade` | Território de Identidade | categoria | sim | — | — | Um dos 27 Territórios de Identidade da Bahia. |
| `valor_solicitado` | Valor Solicitado | decimal | — | — | — | Valor pleiteado em reais. |

**Regras de validação**

- **mínimo de 1 linha(s)** — abaixo disso bloqueia (erro).
- **unicidade** em (id_inscricao) — duplicata bloqueia (erro).
- **valores previstos** em `status`: `Inscrita`, `Em análise`, `Habilitada`, `Inabilitada`, `Selecionada`, `Não selecionada`, `Desistente` — fora da lista gera aviso.
- **faixa** de `nota_final`: mín. 0, máx. 10 — fora da faixa gera aviso.
- **faixa** de `valor_solicitado`: mín. 0, máx. — — fora da faixa gera aviso.
- **referência**: `municipio` deve existir em `municipios.municipio` — órfão gera aviso.

## `municipios`

Tabela de apoio (dimensão). Grão: município. Usada para mapas, cobertura territorial e cálculos por habitante.

- Aba na planilha: `Municipios` (cabeçalho na linha 1)
- Grão / chave: `municipio`

| Coluna | Origem | Tipo | Obr. | Sigilo | Preench. | Descrição |
|---|---|---|:-:|:-:|---:|---|
| `codigo_ibge` | Código IBGE | texto | — | — | — | Código IBGE de 7 dígitos — chave para bases externas e mapas. |
| `municipio` | Município | texto | sim | — | — | Nome do município. |
| `populacao` | População | inteiro | — | — | — | População estimada (fonte IBGE). |
| `territorio_identidade` | Território de Identidade | categoria | sim | — | — | Território de Identidade ao qual o município pertence. |

**Regras de validação**

- **unicidade** em (municipio) — duplicata bloqueia (erro).

## Colunas não publicadas (LGPD)

Estas colunas existem na base interna e são removidas de `data/published/`:

- `inscricoes.cnpj`
- `inscricoes.email_contato`

