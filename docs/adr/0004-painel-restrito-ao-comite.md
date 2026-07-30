# ADR 0004 — Painel restrito ao comitê

- **Data:** 2026-07-30
- **Situação:** **substituído** por
  [ADR 0005 — Painel público no GitHub Pages](0005-painel-publico-no-github-pages.md),
  na mesma data. Mantido no repositório porque o raciocínio sobre o que a
  audiência muda continua válido, e porque a alternativa restrita segue
  disponível caso a decisão seja revista.

## Contexto

A pergunta "o painel será público, restrito à equipe, ou restrito ao comitê?"
estava aberta desde o início ([governança](../06-governanca-e-lgpd.md)), e ela
determina o que pode aparecer na tela.

O painel mostra nome das organizações proponentes, valores solicitados, status
no processo e notas de avaliação. Cada um desses itens tem uma leitura
diferente conforme a audiência: para o comitê é insumo de decisão; em praça
pública, o status de uma proposta antes da decisão final expõe organizações a
um julgamento que o edital ainda não fez.

O repositório passou a ser privado nesta mesma data, resolvendo a exposição das
planilhas originais.

## Decisão

O painel é **restrito ao comitê**.

Consequências técnicas imediatas:

- a hospedagem precisa ter controle de acesso — repositório privado **não**
  torna um site privado (ver [publicação](../08-publicacao-do-painel.md));
- o pacote do painel é montado por lista de permissão e conferido por uma trava
  antes de sair, de modo que a decisão de audiência e a decisão de sigilo
  fiquem independentes: mesmo que o painel um dia se torne público, nenhum dado
  de identificação vai junto.

## Consequências

**A favor**

- Não há decisão de exposição tomada por omissão: enquanto não houver
  hospedagem com controle de acesso, não há link.
- O catálogo de indicadores fica livre para incluir itens sensíveis ao processo
  — como a dispersão entre avaliadores (C2), que em painel público seria
  temerária.

**Contra**

- Exige infraestrutura que o piloto não tinha previsto (a opção recomendada é
  Cloudflare Access, gratuita até 50 pessoas, mas é mais uma peça a operar).
- Perde-se o valor de transparência pública que um painel de edital poderia
  ter. Nada impede uma versão pública futura, com recorte próprio — mas ela
  seria outra decisão, com outro ADR.

## Alternativas descartadas

- **Painel público** — foi considerada e descartada nesta data. Expõe status e
  notas de propostas ainda em análise.
- **URL pública não divulgada** — não é controle de acesso. Um link
  encaminhado, ou indexado, torna o painel aberto sem que ninguém perceba.
- **Sem painel, só relatório em PDF** — resolve o acesso, mas descarta a
  atualização diária, que é a razão de ser do projeto.

## Quando revisar

- Se o edital chegar ao resultado final e a coordenação decidir publicar os
  selecionados: aí cabe uma versão pública, com recorte próprio e ADR próprio.
- Se o comitê crescer além do que a opção de hospedagem escolhida comporta.
