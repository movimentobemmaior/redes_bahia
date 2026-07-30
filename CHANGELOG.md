# Histórico de mudanças

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/).

Mudança de **dado** (planilha do dia) não entra aqui — fica no histórico do git
e em `data/published/historico.csv`. Este arquivo registra mudanças de
**projeto**: contrato, pipeline, regras e documentação.

## [Não publicado]

### Adicionado

- Contrato de dados declarativo (`config/fontes.yml`): abas, colunas, tipos,
  obrigatoriedade, sigilo, chaves e regras de validação.
- Pipeline em quatro camadas: leitura, padronização, validação e publicação.
- Padronização de sujeira típica de planilha: espaço sobrando, número em
  formato brasileiro, data como texto ou série do Excel, `Sim`/`Não`, ID
  numérico que virou `123.0`.
- Validação em dois níveis — erro bloqueia a publicação, aviso publica e fica
  registrado ([ADR 0003](docs/adr/0003-erro-bloqueia-aviso-publica.md)).
- Regras: unicidade, valores previstos, faixa, preenchimento obrigatório,
  mínimo de linhas e referência entre datasets.
- Duas camadas de saída: `data/processed/` (completa) e `data/published/`
  (sem colunas sigilosas), em CSV, Parquet e JSON.
- Manifesto (`data/published/manifest.json`) com procedência, hash da planilha,
  contagens, preenchimento por coluna e resultado da validação.
- Histórico diário (`data/published/historico.csv`), que transforma fotos
  diárias em série temporal.
- Perfilamento (`make perfil`): inspeciona uma planilha desconhecida, gera
  relatório e propõe um contrato.
- Dicionário de dados gerado a partir do contrato.
- Design tokens (`design/tokens/`) com paleta verificada para daltonismo e
  contraste nos modos claro e escuro.
- Página de estado da base em `dashboard/`.
- Automação: subir um `.xlsx` em `data/raw/` dispara validação e publicação.
- Testes cobrindo contrato, padronização, validação, publicação e o caminho
  completo de ponta a ponta.
- Documentação: arquitetura, rotina de atualização, indicadores, identidade
  visual, governança/LGPD, roteiro e três ADRs.

### Publicação do painel

- Decidido: o painel é **público**, no GitHub Pages
  ([ADR 0005](docs/adr/0005-painel-publico-no-github-pages.md), que substitui o
  0004). O repositório segue privado — o que separa uma coisa da outra é a
  montagem do pacote.
- `make site` monta o pacote para hospedagem por **lista de permissão** — só
  entram a página, os tokens de design e `data/published/`.
- Trava de sigilo (`scripts/checar_publicacao.py`) confere o pacote contra o
  contrato antes de qualquer hospedagem: barra planilhas, arquivos da base
  interna, colunas sigilosas e arquivos inesperados na camada publicada.
  Roda no CI e no fluxo **Publicar painel**.
- Documentado por que repositório privado **não** torna um site privado, e as
  opções de hospedagem com controle de acesso
  ([08](docs/08-publicacao-do-painel.md)).

### Corrigido

- Fluxo **Atualizar base** não falha mais quando o contrato muda antes de
  existir qualquer planilha.
- Documentação afirmava que o repositório era privado quando ainda não era.
  Repositório tornado privado em 2026-07-30, sem nenhuma planilha exposta no
  intervalo.

### Ajuste ao dado real (30/07/2026)

Primeira planilha de produção: formulário de credenciamento, 13 respostas.

- `config/fontes.yml` reescrito do zero (**versão 2**). O contrato provisório
  supunha inscrições, avaliações e municípios; a base real é o credenciamento,
  uma aba só com 22 colunas de perguntas do formulário.
- Fonte passa a ser `.xlsx` (era `.xlsm`).
- Colunas sigilosas agora são `respondente_nome` e `respondente_email` — nome
  de pessoa física e e-mail. O nome não foi apontado pelo perfilador
  automático, o que confirma por que o rascunho é revisado por gente.
- Catálogo de indicadores ([04](docs/04-indicadores.md)) reescrito para o que a
  base permite medir, com destaque para os três critérios de sentido invertido,
  em que "Sim" exclui.
- Gerador de exemplo passa a ler os cabeçalhos do próprio contrato, em vez de
  manter uma cópia que diverge.

### Corrigido no pipeline, a partir do dado real

- **Coluna com nome e sem dado era tratada como ausente.** A coluna `Edital`
  veio vazia; no perfil ela sumia em silêncio, e na leitura viraria
  `coluna_ausente` — erro que bloquearia a publicação todos os dias. Agora só
  colunas-fantasma do Excel (sem nome e sem conteúdo) são descartadas.
- **Data no formato "29/07/2026 às 12:16" não era reconhecida** e virava vazio,
  o que apagaria a data de toda a base.

### Pendente

- Confirmar com a coordenação o sentido de exclusão dos critérios invertidos.
- Definir se a etapa de inscrição virá em outra planilha (seria um segundo
  dataset, com contrato próprio).
- Resolver a exposição do repositório: ele está público e `data/raw/` é o lugar
  das planilhas originais. Ver [governança](docs/06-governanca-e-lgpd.md).
