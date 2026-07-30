---
name: Mudança na planilha
about: A estrutura do .xlsm mudou (coluna, aba, categoria nova)
title: "[planilha] "
labels: contrato
---

## O que mudou na planilha

- [ ] coluna nova
- [ ] coluna renomeada
- [ ] coluna removida
- [ ] aba nova ou renomeada
- [ ] categoria nova em uma coluna existente (status, eixo, etapa...)
- [ ] outro:

## Detalhes

<!-- Nome exato do cabeçalho, aba e o que a coluna significa. -->

## É dado pessoal ou de identificação?

- [ ] sim — precisa entrar como `sensivel: true` e ficar fora da base publicada
- [ ] não

## Entra no painel?

<!-- Se sim, qual indicador ela alimenta? Ver docs/04-indicadores.md -->

## Antes de resolver

Rode `make perfil` na planilha nova e anexe `reports/rascunho_fontes.yml`.
