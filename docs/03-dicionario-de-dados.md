# Dicionário de dados

> **Arquivo gerado automaticamente — não edite à mão.**
> Fonte: `config/fontes.yml`. Para atualizar: `make dicionario`.
> Última geração: 2026-07-30 · versão do contrato: 2

## Como ler

- **Coluna** — nome técnico, usado nos arquivos publicados e no painel.
- **Origem** — cabeçalho correspondente na planilha de origem.
- **Tipo** — `texto`, `categoria`, `inteiro`, `decimal`, `data`, `booleano`.
- **Obr.** — obrigatória: se vier vazia, a publicação é bloqueada.
- **Sigilo** — dado pessoal/identificação: fica em `data/processed/` e **não** é publicado.
- **Preench.** — percentual preenchido na última execução do pipeline.

## `credenciamento`

Uma linha por organização que respondeu o formulário de credenciamento. Grão: resposta ao formulário. É o funil de elegibilidade do edital — cada coluna `criterio_*` é um requisito respondido pela própria organização, e o `status_credenciamento` é o resultado da checagem automática desses requisitos.

- Aba na planilha: `Credenciamento Redes Bahia` (cabeçalho na linha 1)
- Grão / chave: `id`
- Linhas na última execução: **13**

| Coluna | Origem | Tipo | Obr. | Sigilo | Preench. | Descrição |
|---|---|---|:-:|:-:|---:|---|
| `id` | ID | texto | sim | — | 100% | Identificador da resposta no sistema de formulários. |
| `edital` | Edital | texto | — | — | 0% | Edital ao qual a resposta se refere. Veio inteiramente vazia na remessa de 30/07/2026 — declarada aqui para não sumir do painel quando começar a ser preenchida. |
| `formulario` | Formulário | categoria | — | — | 100% | Nome do formulário de origem. Hoje há só um. |
| `data_resposta` | Data da Resposta | data | sim | — | 100% | Data de envio da resposta. Vem como texto no formato "29/07/2026 às 12:16"; o pipeline converte para data. |
| `organizacao` | Respondente | texto | sim | — | 100% | Nome da organização ou coletivo respondente. |
| `estado` | Estado do respondente | categoria | sim | — | 100% | Estado declarado pela organização. |
| `respondente_nome` | Usuário que respondeu | texto | — | 🔒 | 100% | Nome da pessoa física que preencheu o formulário. Dado pessoal — não publicado. |
| `respondente_email` | E-mail do usuário | texto | — | 🔒 | 100% | E-mail da pessoa que preencheu. Dado pessoal — não publicado. |
| `status_credenciamento` | Status do credenciamento | categoria | sim | — | 100% | Resultado da checagem automática dos critérios. |
| `representa` | Eu represento: | categoria | sim | — | 100% | Natureza jurídica declarada pela respondente. |
| `criterio_estatuto_registrado` | Sua organização social possui a ata de Constituição e Estatuto Social registrada em cartório? | booleano | — | — | 100% | Ata de constituição e estatuto registrados em cartório. |
| `criterio_regularidade_credito` | Sua organização social está regularizada nos órgãos fiscalizadores de crédito, tais como: Serasa, SPC, Receita Federal, etc? | booleano | — | — | 100% | Regularidade em Serasa, SPC, Receita Federal e afins. |
| `criterio_dois_representantes` | Seu coletivo tem, no mínimo, dois representantes? | categoria | — | — | 100% | Coletivo com ao menos dois representantes. Não é Sim/Não: organizações formais respondem "Não se aplica". |
| `criterio_sede_bahia` | Sua organização tem sede no estado da Bahia? | booleano | — | — | 100% | Sede no estado da Bahia. |
| `criterio_atuacao_apenas_bahia` | Sua organização ou coletivo atua somente no mesmo estado onde está sediada (Bahia)? | booleano | — | — | 100% | Atuação restrita ao estado da sede. |
| `criterio_municipios_ate_200mil` | A sua organização ou coletivo atua em municípios baianos de, no máximo, 200 mil habitantes? | booleano | — | — | 100% | Atuação em municípios de até 200 mil habitantes. |
| `criterio_em_atividade` | Sua organização ou coletivo está em atividade e beneficia diretamente pessoas? | booleano | — | — | 100% | Em atividade, com beneficiários diretos. |
| `criterio_receita_acima_500mil` | Sua organização ou coletivo teve uma receita anual de mais de 500 mil reais no ano de 2025? | booleano | — | — | 100% | Receita anual acima de R$ 500 mil em 2025. Atenção ao sentido: "Sim" aqui é critério de EXCLUSÃO, não de aprovação. |
| `criterio_atuacao_minima_3_anos` | A sua organização ou coletivo, desenvolve comprovadamente atividades no território há, no mínimo, 3 anos? | booleano | — | — | 100% | Pelo menos três anos de atuação comprovada no território. |
| `criterio_vinculo_partidario` | Sua organização ou coletivo possui algum vínculo com partidos políticos em todo o território nacional ou seus responsáveis exercem cargos políticos? | booleano | — | — | 100% | Vínculo partidário ou cargo político. "Sim" é critério de EXCLUSÃO. |
| `criterio_fins_religiosos` | Sua organização social ou coletivo tem fins religiosos? | booleano | — | — | 100% | Fins religiosos. "Sim" é critério de EXCLUSÃO. |
| `ciencia_comprovacao_receita` | Declaro que estou ciente de que serão pedidas comprovações da receita anual. | categoria | — | — | 100% | Ciência de que a receita declarada será comprovada. |

**Regras de validação**

- **mínimo de 1 linha(s)** — abaixo disso bloqueia (erro).
- **unicidade** em (id) — duplicata bloqueia (erro).
- **valores previstos** em `status_credenciamento`: `Aprovado automaticamente`, `Não aprovado` — fora da lista gera aviso.
- **valores previstos** em `representa`: `Associação sem fins lucrativos`, `Coletivo`, `Nenhuma das opções` — fora da lista gera aviso.
- **valores previstos** em `criterio_dois_representantes`: `Sim`, `Não`, `Não se aplica, pois somos uma organização social (ONG, OSC)` — fora da lista gera aviso.

## Colunas não publicadas (LGPD)

Estas colunas existem na base interna e são removidas de `data/published/`:

- `credenciamento.respondente_nome`
- `credenciamento.respondente_email`

