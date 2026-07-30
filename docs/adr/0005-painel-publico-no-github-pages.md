# ADR 0005 — Painel público no GitHub Pages

- **Data:** 2026-07-30
- **Situação:** vigente
- **Substitui:** [ADR 0004 — Painel restrito ao comitê](0004-painel-restrito-ao-comite.md)

## Contexto

O ADR 0004, do mesmo dia, decidiu que o painel seria restrito ao comitê. Ao
implementar a hospedagem, uma restrição técnica apareceu:

`movimentobemmaior` é uma **conta pessoal**, não uma organização. Nesse tipo de
conta, o GitHub Pages não tem controle de acesso — ele existe apenas no GitHub
Enterprise Cloud, com organização. Repositório privado protege os arquivos; o
site gerado a partir dele continua aberto a quem tiver o endereço.

Colocadas as opções (painel agregado no Pages, painel completo público, ou
Cloudflare Access com restrição de verdade), a coordenação optou pelo painel
completo no GitHub Pages, ciente de que ele é público.

## Decisão

O painel é **público**, hospedado no GitHub Pages, publicando
`data/published/` na íntegra.

Fica visível para qualquer pessoa com o endereço:

- nome das organizações proponentes;
- município e território de identidade;
- valor solicitado por proposta;
- status e etapa no processo, **inclusive de propostas ainda em análise**;
- nota final e notas por avaliador e critério.

Continua fora, removido automaticamente na publicação e conferido por trava:
CNPJ, e-mail de contato, e todo o conteúdo de `data/raw/` e `data/processed/`.

## Consequências

**A favor**

- Transparência do edital sem nenhuma barreira de acesso: o comitê, as
  organizações inscritas e qualquer interessado veem a mesma coisa.
- Nenhuma infraestrutura nova para operar. Publica junto com o pipeline.
- Sem custo de plataforma além do plano do GitHub.

**Contra — assumidos conscientemente**

- Status de proposta **em análise** fica público antes da decisão final. Uma
  organização aparece como "Inabilitada" para qualquer pessoa antes mesmo de
  ser comunicada.
- Notas por avaliador (indicador C2 do [catálogo](../04-indicadores.md)) ficam
  públicas, o que é avaliação identificável de terceiros.
- O site é indexável por buscadores. Sair do ar depois não desfaz o que foi
  copiado ou indexado.
- A base legal do tratamento não foi verificada: não se sabe se o edital
  coletou consentimento para divulgação. **Ponto aberto para o jurídico** —
  ver [governança](../06-governanca-e-lgpd.md).

**Mitigação que permanece**

A separação entre camada interna e camada publicada não muda. A trava
(`scripts/checar_publicacao.py`) continua sendo o que impede CNPJ e e-mail de
saírem, e passa a ser a peça mais crítica do projeto, já que o destino agora é
a web aberta.

## Alternativas descartadas

- **Painel agregado no Pages** — publicar só totais por território, funil e
  distribuição de valores, sem linha por proposta. Protegeria as organizações
  mantendo o link público, mas exigia uma camada de agregação no pipeline e
  deixava o comitê sem o detalhe no painel.
- **Cloudflare Pages + Access** — única forma de ter link restrito de verdade
  com o painel completo. Descartada por exigir domínio no Cloudflare e mais uma
  peça para operar.
- **Manter o ADR 0004 sem hospedagem** — deixaria o painel sem link, que era o
  objetivo do pedido.

## Quando revisar

- Se o jurídico apontar que falta base legal para a divulgação.
- Se alguma organização inscrita questionar a exposição do seu status.
- Antes da segunda edição do edital: vale decidir se o padrão é publicar
  durante a análise ou só depois do resultado.
