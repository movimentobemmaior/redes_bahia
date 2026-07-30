# ADR 0001 — Base estática versionada em git, a partir do `.xlsm`

- **Data:** 2026-07-30
- **Situação:** vigente

## Contexto

O dado do edital vive em uma planilha `.xlsm` mantida à mão. Não há API. A
atualização é diária e feita por uma pessoa da equipe, não por um sistema. O
objetivo imediato é um piloto que funcione, não uma plataforma.

## Decisão

A base do painel são **arquivos versionados no repositório**, gerados a partir
da planilha do dia por um comando. Sem banco de dados, sem servidor.

- `data/raw/` guarda cada planilha diária, intocada e versionada.
- `data/processed/` e `data/published/` são gerados e também versionados.
- O painel lê arquivos estáticos, sem back-end.

## Consequências

**A favor**

- Qualquer publicação pode ser refeita: a planilha daquele dia e o código
  daquele dia estão ambos no histórico.
- `git diff` mostra o que mudou entre duas execuções.
- Não há infraestrutura para manter, pagar ou proteger.
- O painel pode ser hospedado como site estático.

**Contra**

- Planilhas versionadas fazem o repositório crescer (~30 KB/dia; ~11 MB/ano —
  aceitável).
- Arquivo binário não tem diff legível.
- Obriga o repositório a ser privado, porque `data/raw/` contém dado de
  identificação.
- Não escala para milhões de linhas.

## Alternativas descartadas

- **Banco de dados gerenciado** — resolve escala que este projeto não tem, e
  cria custo e operação em um piloto.
- **Só a planilha, lida direto pelo painel** — sem validação, sem histórico,
  sem procedência; quebra na primeira coluna renomeada.
- **Planilha fora do repositório (Drive/S3)** — perde a versão em conjunto entre
  dado e código, que é o principal benefício desta decisão.

## Quando revisar

- O repositório passar de ~500 MB.
- O JSON publicado passar de ~5 MB por arquivo.
- Surgir uma API no sistema de inscrição.
- O painel precisar ser público (aí `data/raw/` tem que sair do repositório).
