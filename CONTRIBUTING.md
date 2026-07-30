# Como contribuir

## Antes de qualquer coisa

```bash
make instalar
make exemplo && make dados   # confirma que o caminho completo funciona
make teste
```

## Os dois tipos de mudança

### Mudou a planilha

Quase sempre a resposta é **editar `config/fontes.yml`**, não o código.

1. `make perfil` — vê o que a planilha tem hoje e propõe um contrato.
2. Ajusta `config/fontes.yml` comparando com `reports/rascunho_fontes.yml`.
3. `make validar` — confere sem publicar.
4. `make dados` — publica (isso regera o dicionário de dados).
5. Commit incluindo `docs/03-dicionario-de-dados.md`.

Se a mudança não couber no vocabulário do contrato, aí sim é código — e vale
avaliar se o vocabulário deveria crescer.

### Mudou o código

- Cada módulo do `pipeline/` tem uma responsabilidade só. Lógica de limpeza vai
  em `transform.py`, regra de negócio em `validate.py`, formato de saída em
  `publish.py`. Quando estiver difícil escolher onde colocar, provavelmente a
  responsabilidade está errada.
- Nome de função, variável e coluna em português, sem acento.
- Comentário explica **por que**, não o que o código faz. O comentário mais
  valioso do projeto é o que registra a decisão contraintuitiva (por que
  `2.000` vira 2000, por que a paleta tem uma ordem fixa).
- Toda correção de bug vem com um teste que falha antes da correção.

## Testes

```bash
make teste
```

O que precisa continuar coberto:

- **`test_e2e.py`** — planilha entra, base sai. Se isso quebra, o piloto quebra.
- **`test_publish.py::test_coluna_sensivel_nao_sai_para_o_painel`** — LGPD.
  Nunca desabilite.
- **`test_validate.py`** — a fronteira entre erro e aviso. Mudar essa fronteira
  é decisão de produto e pede um ADR.

## Estilo

```bash
make formatar   # arruma
make lint       # confere
```

Linha de até 100 caracteres, `ruff` decide o resto.

## Decisões

Mudança que altera o rumo do projeto (trocar o formato da base, mudar o que
bloqueia publicação, mudar a paleta) vira um ADR em `docs/adr/`, seguindo o
formato dos existentes: contexto, decisão, consequências, alternativas
descartadas, quando revisar.

## Antes de abrir o pull request

- [ ] `make lint` e `make teste` passam
- [ ] `make dados` roda de ponta a ponta
- [ ] documentação afetada atualizada (o dicionário é gerado, não editado)
- [ ] nenhuma coluna sigilosa nova sem `sensivel: true`
- [ ] decisão relevante registrada em ADR

## O que não entra no repositório

- Senha, token ou chave de qualquer tipo.
- Dado pessoal fora de `data/raw/` e `data/processed/`.
- Arquivo gerado que não seja base publicada (relatórios em `reports/` são
  locais e ignorados pelo git).
