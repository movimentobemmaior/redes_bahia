# Etapa — Seleção

Coloque aqui o `.xlsx` com avaliação de mérito.

Espera-se: notas por critério, avaliadores e a dispersão entre eles.

## Como subir

1. Renomeie o arquivo com a data de referência:

   ```
   AAAA-MM-DD_selecao.xlsx
   ```

2. Coloque nesta pasta e faça o commit.
3. `make dados` (ou o fluxo **Atualizar base**) regenera a base publicada.

**Nunca sobrescreva** o arquivo de um dia anterior: cada dia é um arquivo novo,
e é o histórico da pasta que permite refazer qualquer publicação passada.

## Primeira vez desta etapa

Se ainda não há contrato de dados para ela, o pipeline ignora a pasta e o painel
mostra a etapa como "ainda sem dados". Para ativar:

```bash
make perfil                      # lê a planilha e propõe a estrutura
```

Compare `reports/rascunho_fontes.yml` com `config/fontes.yml`, declare o dataset
e aponte `dataset:` na etapa correspondente do bloco `etapas:`.
