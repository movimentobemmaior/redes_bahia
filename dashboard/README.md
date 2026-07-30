# `dashboard/` — a camada visual

## O que existe hoje

Uma página: **estado da base de dados**. Ela mostra quando a base foi
atualizada, de qual planilha veio, quantas linhas tem cada tabela, o resultado
da validação e os arquivos publicados.

Não é o painel de indicadores — é o que responde "posso confiar no que estou
vendo?", que precisa existir antes de qualquer gráfico.

```bash
make painel   # http://localhost:8000/dashboard/
```

Abrir o `index.html` direto pelo arquivo não funciona: o navegador bloqueia a
leitura do manifesto. Tem que ser por servidor.

## Como funciona

- Lê **apenas** `data/published/manifest.json`. Nunca os dados em si, nunca
  `data/raw/` ou `data/processed/`.
- HTML, CSS e JavaScript puros, sem build e sem dependência externa. Para um
  piloto que precisa abrir em qualquer máquina, isso vale mais que qualquer
  framework.
- Cor, tipografia e espaçamento vêm de `design/tokens/tokens.css`. Nenhum valor
  escrito na mão.

## O que vem depois (fase 3)

Telas de visão geral, território, funil e avaliação, com os indicadores de
[`docs/04-indicadores.md`](../docs/04-indicadores.md) e as regras de
[`docs/05-identidade-visual.md`](../docs/05-identidade-visual.md).

Regras que valem desde já para qualquer gráfico novo:

- um eixo só (nunca dois eixos verticais com escalas diferentes);
- cor segue a identidade da série, nunca a sua posição no ranking;
- nada comunicado só por cor — sempre rótulo, ícone ou tabela junto;
- toda tela funciona em 360px de largura, sem rolagem horizontal da página.
