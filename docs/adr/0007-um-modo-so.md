# ADR 0007 — Um modo só, o claro

- **Data:** 2026-07-30
- **Situação:** aceita

## Contexto

O painel nasceu com dois modos: claro e escuro, com botão para alternar e
respeito à preferência do sistema (`prefers-color-scheme`). Cada token de cor
existia em duas versões, e cada regra de cor de componente precisava da sua
contraparte escura.

A coordenação pediu para ficar só o claro.

Havia razão técnica na mesma direção. A verificação de daltonismo da paleta de
séries passava em todos os pares sobre fundo branco, mas sobre o fundo escuro o
limite caía para **três séries** em gráficos que comparam todos os pares — roxo
e azul ficavam próximos demais. O segundo modo custava uma cor de série.

## Decisão

O painel tem um modo, o claro. Saem:

- o botão de alternar tema e o `data-tema` no `<html>`;
- `configurarTema()` e a preferência guardada no navegador;
- os blocos `@media (prefers-color-scheme: dark)` e `:root[data-tema="escuro"]`
  em `design/tokens/tokens.css` e `dashboard/assets/painel.css`;
- o conjunto escuro de hexes em `design/tokens/tokens.json`.

Fica `color-scheme: light` em `:root`. Sem ele, um navegador em tema escuro
desenharia `select` e `input` no esquema do sistema — campo preto no meio de
uma página branca. É a única linha do arquivo que ainda existe por causa do
modo escuro, e ela existe para impedi-lo.

## Consequências

**Menos superfície.** Uma cor por token, uma regra por componente. Trocar um hex
passa a exigir uma verificação, não duas.

**As quatro séries valem sempre.** O limite de três em gráficos de comparação
total era do modo escuro; sem ele, a paleta inteira está liberada.

**Quem prefere tela escura perde a opção.** É o custo aceito. Vale menos aqui do
que valeria num aplicativo de uso contínuo: o painel é consultado por minutos,
em reunião, quase sempre em ambiente claro.

**A placa branca dos logos continua existindo**, agora só na tela de entrada,
que é roxa. Os logos dos parceiros vêm em versão para fundo claro e não se
inverte nem se dessatura marca de terceiro — isso não era uma regra do modo
escuro, era uma regra de marca.

## Alternativas consideradas

**Manter os dois modos e cortar uma série no escuro.** Era o estado anterior, e
o problema é que a restrição não aparece em lugar nenhum na hora de escrever o
gráfico: quem usa a quarta série no claro não descobre que ela quebrou no
escuro.

**Manter o escuro e refazer a paleta para caber quatro séries nele.** Os hues
vêm da coalizão; não há liberdade para movê-los o bastante.

## Quando revisar

Se o painel passar a ser usado em plantão ou em tela por tempo longo, ou se
alguém do comitê pedir por acessibilidade — sensibilidade à luz é razão
legítima e muda o cálculo.
