# Rotina de atualização

Como subir a planilha do dia e o que fazer quando algo dá errado.

## O caminho curto (sem instalar nada)

1. Abra o repositório no GitHub, entre em `data/raw/`.
2. **Add file → Upload files**, arraste o `.xlsm`.
3. Nomeie no formato `AAAA-MM-DD_redes_bahia.xlsm`.
4. Commit.
5. Na aba **Actions**, acompanhe o fluxo **Atualizar base**.
   - ✅ verde: base publicada e commitada de volta. Fim.
   - ❌ vermelho: nada foi publicado. Abra o artefato `relatorio-validacao`
     e siga a seção "Quando dá errado" abaixo.

## O caminho completo (na sua máquina)

```bash
make instalar          # só na primeira vez
cp ~/planilhas/edital.xlsm data/raw/2026-08-01_redes_bahia.xlsm
make validar           # confere sem publicar
make dados             # valida e publica
git add data/ docs/03-dicionario-de-dados.md
git commit -m "dados: base de 2026-08-01"
git push
```

Sem a planilha real em mãos, `make exemplo` gera uma sintética para testar o
caminho todo.

## Regras do arquivo

- Um arquivo por dia. **Nunca sobrescrever** o de ontem.
- A data no nome define qual é o mais recente. Data errada, base errada.
- Extensão `.xlsm` (é o que `fonte.padrao_arquivo` procura). Para `.xlsx`,
  ajustar o contrato.
- A planilha não pode estar protegida por senha.

## Quando dá errado

O relatório fica em `reports/validacao.md` (ou no artefato do Actions).

### `coluna_ausente` — "a coluna X não foi encontrada"

Alguém renomeou, moveu ou apagou uma coluna na planilha.

- Renomeada por engano → desfazer na planilha e subir de novo.
- Renomeada de propósito → atualizar `origem` da coluna em `config/fontes.yml`.
- Coluna nova → rodar `make perfil`, ver a sugestão em
  `reports/rascunho_fontes.yml` e declarar a coluna no contrato.

### `chave_duplicada` — "linhas repetidas"

Duas linhas com o mesmo identificador. O relatório mostra quais. Normalmente é
linha colada duas vezes ou inscrição registrada em duplicidade. Corrigir na
planilha: com chave duplicada, qualquer contagem do painel fica errada.

### `obrigatorio_vazio` — "coluna obrigatória com valor vazio"

Célula em branco em coluna que o painel precisa. O relatório identifica as
linhas pelo `id_inscricao`.

Se a coluna legitimamente pode ficar vazia (por exemplo, nota antes da
avaliação), o certo é tirar `obrigatorio: true` dela no contrato, não preencher
com valor inventado.

### `valor_nao_previsto` — aviso, não bloqueia

Apareceu uma categoria que não está na lista do contrato (status novo, eixo
novo, ou só uma diferença de grafia: "Em Análise" vs "Em análise").

- Grafia diferente → padronizar na planilha.
- Categoria nova de verdade → acrescentar em `valores` no contrato.

Enquanto não for resolvido, o painel mostra as duas grafias como coisas
diferentes.

### `referencia_orfa` — aviso, não bloqueia

Valor que não existe na tabela de apoio. Um município escrito diferente do que
está na aba `Municipios` some do mapa. Padronizar a grafia.

### `conversao_invalida` — aviso, não bloqueia

Uma célula não pôde ser lida como o tipo declarado e virou vazio. Quase sempre
é texto em coluna numérica ("a combinar", "-", "n/a") ou data em formato
inesperado.

### `coluna_nao_declarada` — aviso, não bloqueia

A planilha tem colunas que o contrato não conhece, e elas ficaram de fora da
base. Se são necessárias, declarar em `config/fontes.yml`.

## Quando a planilha muda de estrutura

```bash
make perfil
```

Isso gera:

- `reports/perfil_<arquivo>.md` — o que existe hoje em cada aba: colunas,
  tipos, preenchimento, exemplos, e um 🔒 nas colunas que parecem ser dado
  pessoal;
- `reports/rascunho_fontes.yml` — proposta de contrato para comparar com o
  atual.

O rascunho **não** substitui `config/fontes.yml`. Quem decide o que é
obrigatório, sigiloso e qual é a chave é uma pessoa.

Depois de ajustar o contrato: `make validar`, e só então `make dados`.

## Publicar mesmo com erro

`make dados` para na primeira quebra de estrutura. Para publicar assim mesmo:

```bash
python -m pipeline dados --forcar
```

Use com parcimônia: o painel vai mostrar dado que o próprio pipeline classificou
como quebrado. O manifesto registra o status, então fica rastreável.

## Refazer uma base antiga

Toda planilha fica em `data/raw/`. Para reconstruir a base de um dia anterior:

```bash
git checkout <commit-daquele-dia> -- data/raw/
python -m pipeline dados --data 2026-07-15
```
