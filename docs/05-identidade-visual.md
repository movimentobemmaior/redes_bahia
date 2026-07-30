# Identidade visual

Referência única para telas e gráficos do painel. Os valores vivem em
`design/tokens/tokens.css` (para o navegador) e `design/tokens/tokens.json`
(para código que gera gráfico). **Nenhum componente escreve cor ou tamanho de
fonte na mão.**

## Princípio

O painel é instrumento de acompanhamento de política pública, não peça de
comunicação. Prioridade: legibilidade, honestidade do número, acessibilidade.
Ornamento que não ajuda a ler sai.

## Tipografia

Uma família só, a sans do sistema operacional:

```
system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", sans-serif
```

Sem fonte de display, sem serifada, sem fonte carregada de servidor externo.
Duas razões: o painel abre igual em qualquer máquina da equipe, e não depende
de rede para renderizar. Se um dia houver tipografia institucional definida,
substituir apenas `--fonte-ui` — nada mais muda.

### Escala

| Token | Tamanho | Uso |
|---|---|---|
| `--texto-hero` | 44px | número de destaque (um por bloco, no máximo) |
| `--texto-2xl` | 32px | título da página |
| `--texto-xl` | 24px | título de seção |
| `--texto-lg` | 20px | título de cartão |
| `--texto-md` | 16px | texto corrente |
| `--texto-sm` | 14px | rótulo, legenda, célula de tabela |
| `--texto-xs` | 12px | metadado, nota de rodapé |

Três pesos: 400 (corrente), 500 (rótulo destacado), 650 (título e número
grande). Nada de 300 — some em tela clara.

Entrelinha: 1.5 no texto corrente, 1.2 em título e número grande.

### Números

Número grande solto (destaque, cartão) usa a figura proporcional padrão.
`font-variant-numeric: tabular-nums` fica reservado para **coluna que precisa
alinhar na vertical**: linha de tabela e marcação de eixo. Usar tabular em todo
lugar deixa o texto corrente com buraco entre os dígitos.

Formato brasileiro em toda parte: `1.234,56`, `R$ 1.234,56`, `12,5%`,
datas em `dd/mm/aaaa` na tela (`AAAA-MM-DD` nos arquivos).

## Cor

### Séries categóricas

Oito posições, **em ordem fixa**. Uma série recebe a cor pela sua identidade,
nunca pela sua posição no ranking: se um filtro muda quantas séries aparecem,
as que sobraram mantêm a cor que tinham.

| Slot | Cor | Claro | Escuro |
|---|---|---|---|
| 1 | azul | `#2a78d6` | `#3987e5` |
| 2 | laranja | `#eb6834` | `#d95926` |
| 3 | verde-água | `#1baf7a` | `#199e70` |
| 4 | amarelo | `#eda100` | `#c98500` |
| 5 | magenta | `#e87ba4` | `#d55181` |
| 6 | verde | `#008300` | `#008300` |
| 7 | violeta | `#4a3aa7` | `#9085e9` |
| 8 | vermelho | `#e34948` | `#e66767` |

A ordem não é estética: ela é o que garante que cores **vizinhas** continuem
distinguíveis para quem tem daltonismo. Reordenar quebra isso.

Paleta verificada nos dois modos (protanopia, deuteranopia, tritanopia,
contraste com a superfície):

- claro: pior par vizinho ΔE 9.1 em CVD, 19.6 em visão normal — passa;
- escuro: pior par vizinho ΔE 8.4 em CVD, 19.3 em visão normal — passa.

No modo claro, verde-água, amarelo e magenta ficam abaixo de 3:1 de contraste
com o fundo. Onde essas cores forem usadas, o gráfico precisa trazer **rótulo
visível ou tabela de dados** — a cor não pode ser a única pista.

**Nona série não existe.** Ao chegar em nove categorias: agrupar em "Outros",
quebrar em pequenos múltiplos, ou trocar de recorte. Cor gerada por algoritmo
está fora.

Em gráficos com todos contra todos (dispersão, bolhas, mapa coroplético,
pequenos múltiplos), o limite cai para **três séries** — acima disso os pares
não vizinhos deixam de ser distinguíveis com segurança.

### Magnitude (rampa sequencial)

Um tom só, do claro ao escuro (`--seq-100` a `--seq-700`). Mapa da Bahia,
mapa de calor, intensidade. Nunca arco-íris.

Em escala **ordinal** (etapas do funil, faixas), o passo mais claro no modo
claro é o `--seq-250`: abaixo disso a forma some no fundo.

### Variação com sinal (divergente)

Azul ↔ vermelho, com cinza no meio. O ponto neutro é cinza porque precisa ler
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

- Largura máxima do conteúdo: 1200px.
- Espaçamento na escala de 4px (`--e-1` a `--e-12`).
- Cantos: 4px em elementos pequenos, 8px em cartões, 12px em blocos grandes.
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
   vizinhos).
2. Reordenar os slots é mudança de acessibilidade, não de gosto.
3. Mudar `tokens.css` sem mudar `tokens.json` (ou o contrário) deixa gráfico e
   tela com cores diferentes.
