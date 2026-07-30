# Governança e LGPD

> Este documento descreve as decisões técnicas tomadas e o que ainda precisa de
> validação jurídica. Não substitui parecer do jurídico.

> ✅ **Resolvido em 2026-07-30: o repositório foi tornado privado.**
>
> Por um período o repositório esteve público, o que era incompatível com
> `data/raw/` guardar as planilhas originais. Nada vazou — nenhuma planilha
> chegou a ser subida nesse intervalo; `data/raw/` só tinha o README. A
> condição que o projeto pressupõe está atendida.

## O que está em jogo

A planilha do edital contém dados que identificam organizações e pessoas: CNPJ,
e-mail de contato, e possivelmente nome de responsável e telefone. A partir do
momento em que esse arquivo entra em um repositório, ele passa a ter cópia,
histórico e (dependendo da configuração) alcance.

## Decisões em vigor

### 0. O repositório é privado, e precisa continuar sendo

`data/raw/` versiona as planilhas originais, com CNPJ e e-mail. Tornar o
repositório público de novo exigiria, antes, tirar `data/raw/` e
`data/processed/` do git — e do histórico, não só da última versão.

**Repositório privado protege os arquivos, não o painel.** Site gerado a partir
de repositório privado continua público se hospedado sem controle de acesso.
Ver [publicação do painel](08-publicacao-do-painel.md).

### 1. `data/raw/` guarda as planilhas originais

Isso é proposital: é o que permite refazer qualquer publicação passada. E é
justamente o que **exige repositório privado**, mesmo com o painel sendo
público — são camadas diferentes.

Se o repositório for tornado público mais tarde, `data/raw/` e
`data/processed/` precisam sair antes — e sair do histórico do git, não só da
última versão.

### 2. Coluna sigilosa não chega à camada publicada

Toda coluna marcada com `sensivel: true` em `config/fontes.yml` é removida na
publicação. Ela existe em `data/processed/` (uso interno) e nunca em
`data/published/`.

Hoje estão marcadas:

| Coluna | Motivo |
|---|---|
| `inscricoes.cnpj` | identifica a organização de forma inequívoca |
| `inscricoes.email_contato` | dado pessoal de contato |

A lista atualizada fica no [dicionário de dados](03-dicionario-de-dados.md),
seção "Colunas não publicadas".

Existe um teste automatizado que falha se uma coluna sigilosa aparecer na
camada publicada (`tests/test_publish.py`).

### 3. Só `data/published/` alimenta o painel — e ela agora é pública

O painel não lê `data/raw/` nem `data/processed/`. Com o painel publicado no
GitHub Pages ([ADR 0005](adr/0005-painel-publico-no-github-pages.md)), tudo que
está em `data/published/` é **acessível a qualquer pessoa na internet**.

Consequência prática: acrescentar uma coluna ao contrato sem marcá-la como
`sensivel` passou a ser uma decisão de publicação. A trava de `make site` barra
o que está marcado; ela não adivinha o que deveria estar.

### 4. Nome de organização, status e notas são públicos

`organizacao`, `status`, `etapa`, `valor_solicitado`, `nota_final` e a tabela
inteira de `avaliacoes` não estão marcadas como sigilosas, e portanto aparecem
no painel público.

**Ponto aberto para o jurídico**, e o mais relevante deste documento: uma
organização aparece como "Inabilitada" para qualquer pessoa possivelmente antes
de ser comunicada, e as notas por avaliador são avaliação identificável de
terceiros. A decisão de publicar está registrada no
[ADR 0005](adr/0005-painel-publico-no-github-pages.md), com as alternativas que
foram descartadas caso ela precise ser revista.

## O que ainda precisa de decisão

| Questão | Impacto |
|---|---|
| **O edital coletou consentimento para divulgação?** | base legal para o painel público — a pergunta mais urgente da lista |
| Status de proposta em análise pode ser público antes da comunicação à organização? | hoje é |
| Notas por avaliador podem ser públicas? | hoje são; avaliação identificável de terceiros |
| Por quanto tempo guardar as planilhas em `data/raw/`? | hoje: indefinidamente |
| Quem pode dar acesso ao repositório? | hoje: sem processo escrito |

## Se um dado sigiloso vazar para a camada publicada

1. Remover a coluna do arquivo publicado e republicar.
2. Marcar a coluna como `sensivel: true` no contrato.
3. Limpar o histórico do git (`git filter-repo`) — apagar na última versão não
   basta, o commit anterior continua acessível.
4. Se o repositório ou o painel estiveram públicos nesse intervalo, registrar o
   incidente e comunicar a coordenação: pode haver dever de notificação.

## Rastreabilidade

Todo dado publicado tem procedência registrada. `data/published/manifest.json`
guarda o nome do arquivo de origem, o hash SHA-256, a data da execução e a
versão do pipeline. Com isso é possível responder "de onde veio este número"
para qualquer valor do painel.

## Segurança básica

- Nenhuma senha, token ou chave no repositório.
- Acesso ao repositório revisado quando alguém sai da equipe.
- A automação (`.github/workflows/atualizar-base.yml`) usa o token do próprio
  GitHub Actions, com permissão de escrita apenas neste repositório.
