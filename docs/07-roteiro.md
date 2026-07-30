# Roteiro

## Onde estamos

**Fase 1 — Base estática (esta entrega).** A planilha do dia entra, vira base
validada, versionada e documentada. O painel ainda não existe; o que existe é
o chão em que ele vai ser construído.

Entregue:

- contrato de dados declarativo (`config/fontes.yml`);
- pipeline de leitura, padronização, validação e publicação;
- separação entre base interna e base publicada, com retenção de dado sigiloso;
- histórico diário, que permite série temporal a partir de fotos diárias;
- manifesto com procedência e resultado da validação;
- dicionário de dados gerado a partir do contrato;
- ferramenta de perfilamento para quando a planilha mudar;
- automação: subiu o `.xlsx`, a base se atualiza sozinha;
- tokens de design e regras visuais definidos e verificados;
- página de estado da base (`dashboard/`);
- testes cobrindo o caminho completo.

## Fase 2 — Ajuste ao dado real (em andamento)

A primeira planilha real chegou em 30/07/2026: o formulário de credenciamento,
com 13 respostas. Feito desde então:

- ✅ `make perfil` na planilha real;
- ✅ `config/fontes.yml` reescrito do zero (versão 2) — o contrato provisório
  supunha inscrições, avaliações e municípios; a base real é o credenciamento,
  uma aba só, 22 colunas;
- ✅ dois defeitos do pipeline corrigidos, ambos revelados pelo dado real:
  coluna com nome e sem dado era tratada como ausente (bloquearia a publicação
  todo dia por causa de `Edital`), e data no formato "29/07/2026 às 12:16" não
  era reconhecida;
- ✅ catálogo de indicadores reescrito para o que existe ([04](04-indicadores.md));
- ✅ gerador de exemplo e testes realinhados; pipeline roda limpo no dado real.

Falta:

1. Confirmar com a coordenação as pendências do catálogo de indicadores —
   principalmente o **sentido de exclusão** dos três critérios invertidos.
2. Rodar com o dado diário por alguns dias e ajustar as regras que gerarem
   ruído.
3. Decidir se a etapa de inscrição (propostas) virá em outra planilha; se sim,
   ela é um segundo dataset, com contrato próprio.

**Critério para sair da fase 2:** uma semana de execuções diárias sem erro de
estrutura, e o catálogo de indicadores confirmado pela coordenação.

## Fase 3 — Painel (primeira versão no ar)

- ✅ Tela única com funil de elegibilidade, distribuições, evolução e tabela
  completa, sobre `data/published/`.
- ✅ Filtros de estado, resultado e natureza jurídica.
- ✅ Bloco de qualidade da base sempre visível (D1–D3 do catálogo).
- ✅ Gráficos em SVG próprio, seguindo [05](05-identidade-visual.md), sem
  dependência externa.
- ✅ Publicação: GitHub Pages
  ([ADR 0005](adr/0005-painel-publico-no-github-pages.md)).

Fica para as próximas rodadas:

1. Mapa por território — depende de uma coluna de município, que o formulário
   de credenciamento não coleta.
2. Comparação entre dias usando `historico.csv` (hoje a evolução vem da data de
   resposta, não do histórico de execuções).
3. Telas da etapa de inscrição, quando essa base existir.

## Fase 4 — Além do piloto

Coisas que o piloto deliberadamente não resolve, com o gatilho de quando passam
a valer a pena:

| Item | Quando passa a valer a pena |
|---|---|
| Banco de dados (DuckDB/Postgres) no lugar de arquivos | quando o JSON publicado passar de ~5 MB ou a leitura ficar lenta |
| Ingestão direta do sistema de inscrição, sem planilha | quando existir API |
| Mais de uma fonte por dia | quando outra base (execução, prestação de contas) entrar |
| Alerta automático quando a validação falha | quando o painel virar rotina de decisão |
| Comparação entre editais | a partir da segunda edição |
| Camada semântica (dbt ou equivalente) | quando os indicadores começarem a divergir entre telas |

## Riscos conhecidos

| Risco | Efeito | Como está tratado |
|---|---|---|
| A planilha muda de formato sem aviso | pipeline para | erro claro apontando a coluna + `make perfil` para diagnosticar |
| Grafia inconsistente (município, status) | contagem errada, buraco no mapa | vira aviso na validação, com os valores listados |
| Ninguém sobe a planilha por vários dias | painel desatualizado sem parecer | data da última atualização em destaque na tela |
| Dado sigiloso vazar para a camada publicada | incidente de LGPD | remoção automática + teste que falha se acontecer |
| Repositório voltar a ser público com planilha em `data/raw/` | publicação de dado pessoal, irreversível pelo histórico do git | repositório privado desde 2026-07-30; a condição está registrada em [governança](06-governanca-e-lgpd.md) |
| Dado de identificação chegar ao site público | exposição irreversível: o site é indexável | montagem por lista de permissão + trava com testes de vazamento, rodando no CI e antes de cada publicação |
| Coluna nova entrar no contrato sem marcação de sigilo | vira dado público sem ninguém decidir isso | revisão do contrato em pull request; a trava barra o marcado, não adivinha o que falta marcar |
| Chave duplicada | todo total do painel fica errado | erro que bloqueia a publicação |
| Critério com sentido invertido lido ao contrário | gráfico exatamente oposto à realidade | sentido registrado na descrição de cada coluna e destacado em [04](04-indicadores.md) B2 |
| Base pequena (13 respostas) tratada como estatística | percentual instável passando por precisão | painel mostra número absoluto; percentual só no tooltip |
| Status automático não explicado pelos critérios | decisão sem motivo rastreável | painel conta e destaca as não aprovadas sem requisito não atendido |
