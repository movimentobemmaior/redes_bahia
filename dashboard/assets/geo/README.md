# `geo/` — malhas do mapa

Contorno e população dos municípios baianos, usados pelo mapa do painel
(`assets/mapa.js`).

| Arquivo | Feições | Propriedades | Casa por |
|---|---|---|---|
| `bahia-municipios.json` | 417 municípios | `chave`, `nome`, `populacao` | código IBGE (`2927408`) ou nome |

**Por que só a Bahia.** Houve também uma malha dos 27 estados, para colorir de
onde vinham as respostas. Saiu: o formulário pergunta a UF, as respostas se
concentram em duas ou três, e para duas ou três linhas uma tabela diz mais que
um mapa do Brasil com 24 estados vazios. O mapa ficou onde há território para
mostrar — o municipal, que é onde mora o critério do edital.

## Quem escolhe

O contrato, em `config/fontes.yml`:

```yaml
geografia:
  coluna: estado        # a coluna da planilha que carrega o lugar
  nivel: estado         # o que essa coluna significa: estado | municipio
  destaque: BA
  territorio:           # o recorte em que o edital pode atuar
    malha: municipio
    limite_populacao: 200000
    rotulo: municípios de até 200 mil habitantes
```

Hoje o mapa desenha o **território**: quais municípios baianos cabem no recorte
de até 200 mil habitantes, coloridos pela própria população. Quando a planilha
passar a trazer o município de cada organização, mude `coluna` e `nivel` — o
mesmo bloco passa a colorir por contagem de respostas, sem mudança de código.

`tests/test_mapa.py` falha se o contrato pedir uma malha que não existe, se
algum município vier sem população, ou se o limite deixar todos (ou nenhum)
dentro do recorte — os três casos em que o mapa some ou mente em silêncio.

## De onde vêm

| Dado | Origem | Licença |
|---|---|---|
| contorno dos municípios | [tbrugz/geodata-br](https://github.com/tbrugz/geodata-br), a partir do IBGE | CC0 1.0 |
| população estimada (2021) | [wcota/covid19br](https://github.com/wcota/covid19br), a partir do IBGE | CC BY 4.0 |

O crédito viaja dentro do próprio arquivo, nos campos `credito` e
`credito_populacao`.

## Como refazer

```bash
make malhas      # = python scripts/gerar_malhas.py
```

O script baixa as fontes, simplifica o contorno (Douglas–Peucker), arredonda a
coordenada para 4 casas, junta a população por código IBGE e descarta o resto.
Precisa de rede; por isso o resultado é versionado e o dia a dia não roda nada
disso. Se algum município ficar sem população, o script falha em vez de gerar o
arquivo — sem o número, o painel classificaria o município como "fora do
recorte", dizendo o oposto do que se quer dizer.

**Não edite este arquivo à mão.** Se o contorno precisar de mais ou menos
detalhe, mude a tolerância no script e rode de novo, para que o arquivo continue
reproduzível a partir da fonte.
