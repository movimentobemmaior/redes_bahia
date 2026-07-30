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
- Automação: subir um `.xlsm` em `data/raw/` dispara validação e publicação.
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

### Pendente

- Substituir o contrato provisório pelo contrato do `.xlsm` real (fase 2).
- Fechar o catálogo de indicadores com a coordenação.
- Decidir se o painel será público ou restrito.
