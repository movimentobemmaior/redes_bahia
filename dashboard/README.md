# `dashboard/` — a camada visual

O painel do Edital Redes Bahia: o funil das cinco etapas, da divulgação ao
resultado.

```bash
make painel   # http://localhost:8000/dashboard/
```

Abrir o `index.html` direto pelo arquivo não funciona: o navegador bloqueia a
leitura dos dados. Tem que ser por servidor.

## O que a tela mostra

Primeiro a visão geral, depois o detalhe de cada etapa. Quem abre para decidir
lê o topo; quem abre para investigar desce.

| Bloco | Responde |
|---|---|
| Estado da base | posso confiar no que estou vendo? |
| **Funil das cinco etapas** | **onde o edital está e quanto passou de uma etapa para a outra** |
| Números gerais | quantas se credenciaram, quantas passaram |
| Resultado do credenciamento | a proporção, de uma olhada |
| **Requisitos não atendidos** | **qual exigência está barrando quem** |
| Origem por estado | quem respondeu de fora da Bahia |
| Natureza jurídica | quem não se encaixa no desenho do edital |
| Respostas por dia | o formulário ainda está recebendo? |
| Organizações | a tabela completa, com o motivo linha a linha |
| Qualidade da base | preenchimento, sigilo e problemas da validação |

Filtros de estado, resultado e natureza jurídica recalculam tudo.

As etapas sem planilha aparecem assim mesmo, marcadas como "ainda sem dados" e
com a pasta em que o arquivo deve ser solto. Esconder etapa vazia daria a
impressão de que o edital termina onde os dados terminam.

## A regra de negócio não está aqui

Qual resposta torna uma organização inelegível vem do **contrato**
(`exclui_quando` em `config/fontes.yml`), atravessa o pipeline e chega ao painel
pelo `manifest.json`.

Isso não é cerimônia: **três critérios do edital têm sentido invertido** — em
receita acima de R$ 500 mil, vínculo partidário e fins religiosos, é o "Sim"
que exclui. Codificar isso no JavaScript seria a forma mais fácil de publicar
um gráfico exatamente ao contrário da realidade, e sem ninguém perceber. Há
teste que falha se a marcação mudar (`tests/test_publish.py`).

## Como funciona

- Lê **apenas** `data/published/`: o manifesto e `credenciamento.json`. Nunca
  `data/raw/` ou `data/processed/`.
- HTML, CSS e JavaScript puros, sem build e sem dependência externa. Os
  gráficos são SVG escrito à mão em `assets/graficos.js` — são três formas, e
  escrevê-las custa menos que carregar uma biblioteca para usar 5% dela.
- Cor, tipografia e espaçamento vêm de `design/tokens/tokens.css`, derivados do
  regulamento do edital. Nenhum valor escrito na mão.
- Tipografia Raleway e logos da coalizão ficam em `assets/fontes/` e
  `assets/marca/`, servidos do próprio repositório: o painel não depende de CDN
  nem de rede de terceiros para renderizar com a identidade certa.

## Regras que valem para qualquer gráfico novo

Detalhadas em [`docs/05-identidade-visual.md`](../docs/05-identidade-visual.md):

- um eixo só (nunca dois eixos verticais com escalas diferentes);
- cor segue a identidade da série, nunca a sua posição no ranking;
- nada comunicado só por cor — sempre rótulo, ícone ou tabela junto;
- rótulo longo é cortado com reticência e mantido inteiro no `<title>`, nunca
  deixado vazar pela borda;
- gráfico mede a largura real do contêiner, para o texto não encolher junto;
- toda tela funciona em 360px, sem rolagem horizontal da página.
