# Identidade visual

Referência única para telas e gráficos do painel. Os valores vivem em
`design/tokens/tokens.css` (para o navegador) e `design/tokens/tokens.json`
(para código que gera gráfico). **Nenhum componente escreve cor ou tamanho de
fonte na mão.**

Tudo aqui foi derivado do regulamento do edital
(`docs/Edital-RedesBahia.pdf`): o roxo institucional, a tipografia e os tons
pálidos dos blocos de conteúdo saíram de amostragem direta das páginas.

## Princípio

O painel é instrumento de acompanhamento, não peça de comunicação. Ele veste a
identidade do edital para que quem abre reconheça de onde vem, mas a prioridade
segue sendo legibilidade, honestidade do número e acessibilidade. Ornamento que
não ajuda a ler sai.

## Tipografia

**Raleway**, a mesma do regulamento, hospedada no próprio repositório
(`dashboard/assets/fontes/`, licença SIL OFL).

```
"Raleway", system-ui, -apple-system, "Segoe UI", sans-serif
```

Servida localmente e não de CDN, por duas razões: o painel abre sem depender de
rede de terceiros, e a fonte não muda debaixo dos pés numa atualização do
provedor. São dois arquivos woff2 (latin e latin-ext, ~78 KB no total), com a
sans do sistema como reserva enquanto carregam.

### Escala

| Token | Tamanho | Uso |
|---|---|---|
| `--texto-hero` | 52px | número de destaque (um por bloco, no máximo) |
| `--texto-3xl` | 40px | título da página, valor de indicador |
| `--texto-2xl` | 30px | título de etapa |
| `--texto-xl` | 22px | título de bloco |
| `--texto-md` | 16px | texto corrente |
| `--texto-sm` | 14px | descrição, legenda, célula de tabela |
| `--texto-xs` | 12px | rótulo institucional, metadado |

Quatro pesos: 400 (corrente), 500 (rótulo destacado), 600 (título), 700 (número
grande e título da página). Nada de 300 — some em tela clara.

Entrelinha: 1.6 no texto corrente, 1.15 em título e número grande.

**Rótulo institucional** (`ETAPA 2`, `PARCERIA TÉCNICA`, `ÚLTIMA ATUALIZAÇÃO`)
segue o padrão do regulamento: caixa alta, 12px, peso 600 e entreletra de
0.12em. É o recurso que dá à tela o ar do documento sem precisar de ornamento.

### Números

Número grande solto (destaque, cartão) usa a figura proporcional padrão.
`font-variant-numeric: tabular-nums` fica reservado para **coluna que precisa
alinhar na vertical**: linha de tabela e marcação de eixo. Usar tabular em todo
lugar deixa o texto corrente com buraco entre os dígitos.

Formato brasileiro em toda parte: `1.234,56`, `R$ 1.234,56`, `12,5%`,
datas em `dd/mm/aaaa` na tela (`AAAA-MM-DD` nos arquivos).

## Cor

### Marca

O roxo institucional, amostrado da capa do regulamento:

| Token | Hex | Onde |
|---|---|---|
| `--roxo-900` | `#3e2166` | base do gradiente do cabeçalho |
| `--roxo-800` | `#4f2d71` | títulos de seção no regulamento |
| `--roxo-600` | `#6b489b` | topo do gradiente, série 1 |
| `--roxo-050` | `#faf6fd` | fundo dos blocos, como no edital |

O cabeçalho do painel usa o mesmo gradiente da capa (135°, do `--roxo-600` ao
`--roxo-900`), com a marca do Movimento Bem Maior em branco.

### Séries categóricas

Quatro posições, **em ordem fixa**, com os hues da coalizão. Uma série recebe a
cor pela sua identidade, nunca pela sua posição no ranking: se um filtro muda
quantas séries aparecem, as que sobraram mantêm a cor que tinham.

| Slot | Cor | Claro | Escuro | Origem |
|---|---|---|---|---|
| 1 | roxo | `#6b489b` | `#8f6fbe` | marca do edital |
| 2 | laranja | `#e2711d` | `#d4701f` | Phomenta, Lina Galvani, phi |
| 3 | verde | `#0f8a5f` | `#1d9463` | Instituto Lina Galvani |
| 4 | azul | `#4a7fd4` | `#5a8fdb` | marca Redes Bahia |

A ordem não é estética: ela é o que garante que cores **vizinhas** continuem
distinguíveis para quem tem daltonismo. Reordenar quebra isso.

Paleta verificada com `scripts/validate_palette.js` nos dois modos
(protanopia, deuteranopia, tritanopia, faixa de luminosidade, chroma e
contraste com a superfície):

- **claro** (superfície `#ffffff`): passa em todos os pares. Pior par vizinho
  ΔE 17.8 em CVD e 20.1 em visão normal; pior par entre todos, 15.5.
- **escuro** (superfície `#1b1526`): passa nos pares vizinhos, com ΔE 17.1 em
  CVD e 19.9 em visão normal. **Em gráficos que comparam todos os pares**
  (dispersão, bolhas, coroplético, pequenos múltiplos) o limite no modo escuro
  é de **três séries**: com as quatro, roxo e azul ficam próximos demais.

**Quinta série não existe.** Ao chegar em cinco categorias: agrupar em
"Outros", quebrar em pequenos múltiplos, ou trocar de recorte. Cor gerada por
algoritmo está fora.

A paleta anterior tinha oito slots e não vinha da marca. Foi trocada em
30/07/2026 para a identidade do edital; a checagem foi refeita do zero, e o
número de slots caiu porque os hues da coalizão não cobrem espaço de cor
suficiente para oito categorias seguras. Quatro cobrem o que o painel usa.

### Magnitude (rampa sequencial)

Um tom só, do claro ao escuro (`--seq-100` a `--seq-700`). Mapa da Bahia,
mapa de calor, intensidade. Nunca arco-íris.

Em escala **ordinal** (etapas do funil, faixas), o passo mais claro no modo
claro é o `--seq-250`: abaixo disso a forma some no fundo.

### Variação com sinal (divergente)

Roxo ↔ laranja, com cinza no meio. O ponto neutro é cinza porque precisa ler
como "nada"; uma terceira cor no meio vira uma terceira categoria.

### Status (reservado)

`--status-ok`, `--status-atencao`, `--status-serio`, `--status-critico` são
exclusivos de estado. Nunca viram "a cor da quarta série".

Status **sempre** aparece com ícone e rótulo em texto, nunca só pela cor —
tanto por daltonismo quanto porque um ponto vermelho não diz o que aconteceu.

### Texto

Texto usa tinta (`--tinta-1/2/3`), nunca a cor da série. Quem carrega a
identidade da série é o traço ou o quadradinho ao lado do rótulo. Rótulo
colorido sobre fundo claro é a receita mais comum de painel ilegível.

## Gráficos

- **Marca fina.** Linha de 2px; ponta de barra arredondada em 4px, ancorada na
  linha de base; marcador de no mínimo 8px.
- **2px de respiro** entre preenchimentos vizinhos (segmentos empilhados,
  barras coladas) e anel de 2px na cor da superfície em marca sobreposta.
- **Grade discreta.** Grade e eixo em tom recessivo (`--grade`, `--eixo`); o
  dado é a coisa mais escura da tela.
- **Um eixo.** Nunca dois eixos verticais com escalas diferentes: é a forma mais
  fácil de sugerir uma correlação que não existe. Duas medidas de grandezas
  diferentes viram dois gráficos.
- **Legenda a partir de duas séries.** Com uma série só, o título já nomeia. Com
  até quatro, rotular direto na marca além da legenda.
- **Rótulo seletivo.** Número em todo ponto polui; rotular o primeiro, o último
  e os extremos.
- **Passar o mouse mostra o valor.** Linha e área: mira vertical com tooltip.
  Barra, ponto e célula: tooltip por marca.
- **Tabela sempre acessível.** Todo gráfico tem uma tabela equivalente
  alcançável — pelos arquivos em `data/published/` no mínimo.
- **Modo escuro é escolhido, não invertido.** Os passos escuros da tabela acima
  foram medidos contra o fundo escuro.

### Quando não fazer gráfico

Um número só não vira gráfico: vira número grande com rótulo. Comparação de
duas categorias cabe em uma frase. Gráfico existe para revelar padrão, ordem ou
distribuição.

## Layout

- Largura máxima do conteúdo: 1160px.
- Espaçamento na escala de 4px (`--e-1` a `--e-16`).
- Cantos: 4px em elementos pequenos, 10px em cartões, 16px em blocos grandes —
  o mesmo raio generoso dos blocos do regulamento.
- Cabeçalho em gradiente roxo, conteúdo sobre plano claro, rodapé branco com a
  faixa da coalizão. É a estrutura da capa do edital, na vertical.
- Filtros ficam em uma faixa única acima dos gráficos, nunca espalhados.
- A tela precisa funcionar em 360px de largura: tabela e gráfico largo rolam
  dentro do próprio contêiner, a página nunca rola na horizontal.

## Acessibilidade — mínimo obrigatório

1. Nenhuma informação transmitida só por cor.
2. Contraste de texto de no mínimo 4.5:1.
3. Navegação por teclado em todo filtro e controle.
4. Foco visível.
5. Tabela equivalente para todo gráfico.
6. Respeita `prefers-reduced-motion`.

## Antes de mudar qualquer cor

1. Trocar hex de série exige revalidar a paleta inteira nos dois modos
   (contraste, faixa de luminosidade, separação para daltonismo entre pares
   vizinhos). Os números da última verificação estão registrados acima —
   substitua-os pelos novos.
2. Reordenar os slots é mudança de acessibilidade, não de gosto.
3. Mudar `tokens.css` sem mudar `tokens.json` (ou o contrário) deixa gráfico e
   tela com cores diferentes.
