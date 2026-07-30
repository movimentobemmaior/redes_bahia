# ADR 0002 — Contrato de dados declarativo em YAML

- **Data:** 2026-07-30
- **Situação:** vigente

## Contexto

A planilha muda: coluna renomeada, aba nova, categoria nova. Se a estrutura
esperada estiver espalhada pelo código Python, cada mudança dessas vira tarefa
de programação, e a documentação desatualiza em silêncio.

Além disso, o contrato foi escrito **antes** de o `.xlsm` real existir. Ele
precisa ser fácil de reescrever inteiro.

## Decisão

Toda a estrutura esperada fica em um arquivo declarativo, `config/fontes.yml`:
abas, colunas, tipos, obrigatoriedade, sigilo, chaves e regras de validação.

Desse arquivo saem quatro coisas: a leitura da planilha, a validação, o
dicionário de dados e os metadados publicados.

Complementos:

- `pipeline/config.py` valida o próprio contrato e falha com mensagem que
  aponta a chave problemática;
- `make perfil` inspeciona uma planilha desconhecida e **propõe** um contrato,
  sem sobrescrever o vigente.

## Consequências

**A favor**

- Adaptar a uma planilha nova é editar YAML, não Python.
- O dicionário de dados não pode desatualizar: ele é gerado.
- Quem conhece o edital consegue ler e revisar o contrato sem saber programar.
- O contrato é revisável em pull request, com histórico de mudanças.

**Contra**

- Uma regra realmente incomum não cabe no vocabulário declarativo e exige
  código novo.
- YAML é sensível a indentação e silencioso quando erra — mitigado pela
  validação do próprio contrato e por um teste que carrega o arquivo real.

## Alternativas descartadas

- **Schema no código (pandera, pydantic)** — mais expressivo, mas fecha a porta
  para quem não programa, e é justamente quem conhece o edital.
- **Inferir o schema da planilha** — silencioso demais: coluna sumindo passaria
  a ser normal, que é exatamente o que se quer detectar. A inferência entrou
  como ferramenta de apoio (`make perfil`), não como comportamento automático.
- **Sem contrato, validando na mão** — não sobrevive à rotina diária.

## Quando revisar

- Se as regras necessárias deixarem de caber no vocabulário declarativo.
- Se surgirem várias fontes com estruturas muito diferentes.
