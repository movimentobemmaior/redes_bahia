# Governança e LGPD

> Este documento descreve as decisões técnicas tomadas e o que ainda precisa de
> validação jurídica. Não substitui parecer do jurídico.

> 🔴 **PENDÊNCIA BLOQUEANTE — o repositório está público.**
>
> Verificado em 2026-07-30. Nada vazou: `data/raw/` ainda só tem um README.
> Mas a rotina descrita neste projeto coloca as planilhas originais — com CNPJ
> e e-mail — dentro de `data/raw/`, versionadas. **Em repositório público, a
> primeira planilha subida é uma publicação de dados pessoais**, e o histórico
> do git a mantém acessível mesmo depois de apagada.
>
> **Não suba nenhum `.xlsm` até resolver isso.** Ver "Como destravar" abaixo.

## O que está em jogo

A planilha do edital contém dados que identificam organizações e pessoas: CNPJ,
e-mail de contato, e possivelmente nome de responsável e telefone. A partir do
momento em que esse arquivo entra em um repositório, ele passa a ter cópia,
histórico e (dependendo da configuração) alcance.

## Como destravar

O projeto foi desenhado assumindo repositório privado. Como ele está público,
uma destas três escolhas precisa ser feita **antes da primeira planilha**:

| Opção | O que fazer | O que se ganha e o que se perde |
|---|---|---|
| **A. Tornar o repositório privado** | Settings → General → Danger Zone → Change visibility | Nada muda no projeto; é a opção que preserva o desenho original (planilha versionada, publicação refazível). Perde-se a vitrine pública do código. |
| **B. Manter público e tirar os dados do git** | `data/raw/` e `data/processed/` passam a viver fora do repositório (Drive, S3, storage interno); o pipeline lê de lá | Código público, dado fora. Perde-se a versão em conjunto entre dado e código, que é o principal benefício do [ADR 0001](adr/0001-base-estatica-versionada.md) — refazer uma publicação antiga deixa de ser automático. |
| **C. Manter público e não guardar identificação** | Remover CNPJ e e-mail já na origem, antes de a planilha entrar em `data/raw/` | Simples, mas perde-se a capacidade de desduplicar organização por CNPJ (indicador A2) e de conferir dado com a fonte. |

**A é a recomendação**, por ser a única que não desmonta nada do que já está
construído. B exige reescrever o ADR 0001 e a camada de leitura. C exige um
passo manual diário, que é justamente o tipo de coisa que se esquece.

Enquanto a decisão não sai, o repositório pode ficar como está: sem `.xlsm` em
`data/raw/`, não há dado pessoal exposto.

## Decisões em vigor

### 1. `data/raw/` guarda as planilhas originais

Isso é proposital: é o que permite refazer qualquer publicação passada. E é
justamente o que **exige repositório privado** (ver a pendência no topo).

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

### 3. Só `data/published/` alimenta o painel

O painel não lê `data/raw/` nem `data/processed/`. Se um dia o painel for
hospedado, é essa pasta — e só ela — que sai.

### 4. Nome de organização é publicado

`organizacao` não está marcada como sigilosa: identificar quem se inscreveu em
edital de financiamento é, em geral, informação de interesse público, e sem ela
o painel perde sentido.

**Ponto para validação jurídica**, especialmente se o painel for público.

## O que ainda precisa de decisão

| Questão | Impacto |
|---|---|
| O painel será público, restrito à equipe, ou restrito ao comitê? | define o que pode ser publicado |
| Nome de organização pode aparecer em painel público? | ver acima |
| Notas por avaliador podem ser publicadas? | avaliação identificável de terceiros |
| Por quanto tempo guardar as planilhas em `data/raw/`? | hoje: indefinidamente |
| Quem pode dar acesso ao repositório? | hoje: sem processo escrito |
| O edital coletou consentimento para divulgação dos dados? | base legal do tratamento |

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
