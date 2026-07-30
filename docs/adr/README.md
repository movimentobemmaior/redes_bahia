# Decisões de arquitetura (ADR)

Registro curto de cada decisão que muda o rumo do projeto: o contexto, a
escolha, o que se abriu mão e quando revisar.

Vale o esforço porque daqui a seis meses ninguém lembra por que a base não é um
banco de dados, e sem o registro a discussão recomeça do zero.

| # | Decisão | Data | Situação |
|---|---|---|---|
| [0001](0001-base-estatica-versionada.md) | Base estática versionada em git, a partir do `.xlsx` | 2026-07-30 | vigente |
| [0002](0002-contrato-declarativo.md) | Contrato de dados declarativo em YAML | 2026-07-30 | vigente |
| [0003](0003-erro-bloqueia-aviso-publica.md) | Erro bloqueia a publicação; aviso publica e registra | 2026-07-30 | vigente |
| [0004](0004-painel-restrito-ao-comite.md) | Painel restrito ao comitê | 2026-07-30 | substituído pelo 0005 |
| [0005](0005-painel-publico-no-github-pages.md) | Painel público no GitHub Pages | 2026-07-30 | vigente |
| [0006](0006-porta-de-entrada-no-painel.md) | Porta de entrada no painel — cortina, não fechadura | 2026-07-30 | vigente |
| [0007](0007-um-modo-so.md) | Um modo só, o claro | 2026-07-30 | vigente |

## Formato

Contexto → Decisão → Consequências → Alternativas descartadas → Quando revisar.
Uma página, no máximo. ADR não se edita depois de vigente: se a decisão muda,
escreve-se outro ADR que substitui o anterior.
