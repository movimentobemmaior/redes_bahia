# `data/raw/` — as planilhas de cada etapa

O edital tem cinco etapas, e cada uma tem a sua pasta. **É a única parte do
repositório em que se mexe na rotina.**

| Pasta | Etapa | O que entra |
|---|---|---|
| `1-divulgacao/` | Divulgação | dados da comunicação: alcance, canais, origem |
| `2-cadastramento/` | Cadastramento | respostas do formulário de credenciamento |
| `3-triagem/` | Triagem | propostas submetidas e conferência documental |
| `4-selecao/` | Seleção | avaliação de mérito: notas, critérios, avaliadores |
| `5-resultado/` | Resultado | selecionadas, valores aprovados, carteira final |

Cada pasta tem um README com o que se espera dela.

## Regras

- Um arquivo por dia, por etapa. **Nunca sobrescrever** o de ontem.
- Nome no formato `AAAA-MM-DD_<etapa>.xlsx`. A data no nome define qual é o mais
  recente; data errada, base errada.
- Etapa sem planilha não é problema: o pipeline processa as que existem e o
  painel mostra as demais como "ainda sem dados".
- A planilha não pode estar protegida por senha.

## Enquanto o repositório for público

As planilhas destas pastas estão **fora do git** (ver `.gitignore`). O desenho
do projeto as versiona — é o que torna qualquer publicação refazível
([ADR 0001](../../docs/adr/0001-base-estatica-versionada.md)) —, mas com o
repositório público isso publicaria nome e e-mail de quem respondeu, e a
decisão ficou em aberto.

Na prática: a planilha fica na sua máquina, `make dados` a processa
normalmente, e o que vai para o repositório é `data/published/`, sem dado de
identificação. Para voltar ao desenho original, apague as duas últimas linhas
do bloco correspondente no `.gitignore`.

## Atenção — LGPD

Os arquivos destas pastas contêm dados de identificação (nome e e-mail de quem
respondeu). As colunas marcadas como `sensivel: true` no contrato nunca chegam a
`data/published/`, mas isso protege a camada publicada, **não** estas pastas:
aqui o arquivo fica como veio. Ver `docs/06-governanca-e-lgpd.md`.
