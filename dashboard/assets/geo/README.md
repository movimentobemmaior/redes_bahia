# `geo/` — malhas do mapa

Contornos usados pelo mapa coroplético do painel (`assets/mapa.js`).

| Arquivo | Feições | Casa por | Usado quando |
|---|---|---|---|
| `brasil-estados.json` | 27 unidades da federação | sigla (`BA`) ou nome (`Bahia`) | `geografia.nivel: estado` |
| `bahia-municipios.json` | 417 municípios baianos | código IBGE (`2927408`) ou nome | `geografia.nivel: municipio` |

Quem escolhe é o contrato, em `config/fontes.yml`:

```yaml
geografia:
  coluna: estado      # a coluna da planilha que carrega o lugar
  nivel: estado       # estado | municipio
  destaque: BA        # unidade contornada como território do edital
```

Hoje o formulário de credenciamento só pergunta o estado. Quando a planilha
passar a trazer o município, troque `coluna` e `nivel` — a malha municipal já
está aqui e o painel passa a desenhá-la sem mudança de código. O teste
`tests/test_mapa.py` falha se o contrato pedir um nível sem malha
correspondente, para que a troca não resulte num mapa que some em silêncio.

## De onde vêm

As duas derivam da malha municipal do [IBGE](https://www.ibge.gov.br/), por
intermédio de repositórios públicos:

| Arquivo | Origem | Licença |
|---|---|---|
| `brasil-estados.json` | [luizpedone/municipal-brazilian-geodata](https://github.com/luizpedone/municipal-brazilian-geodata) | MIT |
| `bahia-municipios.json` | [tbrugz/geodata-br](https://github.com/tbrugz/geodata-br) | CC0 1.0 |

## Como refazer

```bash
python scripts/gerar_malhas.py
```

O script baixa as fontes, simplifica o contorno (Douglas–Peucker), arredonda a
coordenada para 4 casas e descarta tudo que não é geometria ou nome. Precisa de
rede; por isso o resultado é versionado e o dia a dia não roda nada disso.

**Não edite estes arquivos à mão.** Se o contorno precisar de mais ou menos
detalhe, mude a tolerância no script e rode de novo — assim o arquivo continua
sendo reproduzível a partir da fonte.
