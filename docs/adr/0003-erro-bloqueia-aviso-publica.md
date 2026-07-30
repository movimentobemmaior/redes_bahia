# ADR 0003 — Erro bloqueia a publicação; aviso publica e registra

- **Data:** 2026-07-30
- **Situação:** vigente

## Contexto

Planilha preenchida à mão sempre tem alguma coisa fora do lugar. Duas posturas
extremas falham:

- **validação rígida** — o painel para toda semana por causa de uma célula, e a
  equipe aprende a usar `--forcar` sempre, o que anula a validação;
- **sem validação** — o painel mostra número errado com cara de número certo,
  que é pior do que não mostrar.

## Decisão

Dois níveis de gravidade, com efeitos diferentes.

**Erro — bloqueia a publicação.** Quebra de estrutura, que invalida o painel
inteiro:

- coluna declarada que sumiu da planilha;
- coluna obrigatória com célula vazia;
- chave duplicada;
- aba abaixo do mínimo de linhas.

Nada é publicado, e o painel continua mostrando a base da última execução
válida. Base de ontem, correta, é melhor que base de hoje, quebrada.

**Aviso — publica e registra.** Quebra de conteúdo, localizada:

- categoria fora da lista prevista;
- valor fora da faixa esperada;
- referência que não existe na tabela de apoio;
- célula que não pôde ser convertida para o tipo declarado.

Publica, registra no manifesto e fica visível no painel.

Duas saídas de emergência: `--estrito` promove aviso a erro (para revisão de
dados) e `--forcar` publica mesmo com erro (para exceção consciente, com o
status registrado no manifesto).

## Consequências

**A favor**

- O painel só para quando parar é a atitude correta.
- Problema de conteúdo fica visível em vez de sumir.
- Quem sobe a planilha recebe uma lista acionável, com os valores concretos.

**Contra**

- A fronteira entre "estrutural" e "de conteúdo" é uma escolha, e vai precisar
  de ajuste quando o dado real aparecer.
- Publicar com aviso depende de alguém olhar o aviso. O bloco de qualidade da
  base no painel (E1–E3) existe para isso.

## Alternativas descartadas

- **Só um nível** — cai em um dos dois extremos descritos no contexto.
- **Quarentena da linha problemática** — some com dado sem a pessoa perceber, e
  faz o total do painel não bater com o da planilha.

## Quando revisar

Depois de uma semana de execuções com o dado real: se algum aviso aparecer
todos os dias sem ninguém agir, ou ele vira erro ou a regra está errada.
