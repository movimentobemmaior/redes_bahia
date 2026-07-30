# Publicação do painel

Como o painel vai ao ar, e o que nunca vai junto.

## A decisão

O painel é **público**, no GitHub Pages
([ADR 0005](adr/0005-painel-publico-no-github-pages.md)).

Endereço, depois do primeiro deploy:

```
https://movimentobemmaior.github.io/redes_bahia/
```

Há uma tela de usuário e senha antes do painel
([ADR 0006](adr/0006-porta-de-entrada-no-painel.md)), mas ela é **cortina, não
fechadura**: o endereço é público, a conferência roda no navegador e
`data/published/` responde por URL direta sem passar por ela. Ver
[Quem entra](#quem-entra).

**O repositório é público**, e as planilhas de origem ficam fora do git por
causa disso:

| | Onde vive | Quem enxerga |
|---|---|---|
| Planilhas originais (`data/raw/`) | só na máquina de quem roda | ninguém, fora do git |
| Base interna completa (`data/processed/`) | só na máquina de quem roda | ninguém, fora do git |
| Base do painel (`data/published/`) | repositório público **e** site | qualquer pessoa |

O que separa uma coisa da outra não é a configuração do GitHub nem a tela de
entrada — é a montagem do pacote, descrita abaixo, e o `.gitignore`.

## Ligar pela primeira vez

Passo manual, uma vez só:

> **Settings → Pages → Build and deployment → Source: _GitHub Actions_**

Depois disso o fluxo **Publicar painel** cuida do resto, a cada atualização da
base.

⚠️ **Se um dia o repositório voltar a ser privado**, o GitHub Pages passa a
exigir plano pago. A saída é assinar o plano, não abrir o repositório de novo
com as planilhas versionadas: `data/raw/` guarda CNPJ e e-mail. Ver
[governança](06-governanca-e-lgpd.md).

## Como o pacote é montado

```bash
make site
```

Duas etapas, de propósitos diferentes:

1. **`scripts/montar_site.py`** monta `_site/` por **lista de permissão**.
   Nada é copiado por padrão; entram apenas:

   | Origem | Vira |
   |---|---|
   | `dashboard/index.html` | a tela de entrada (usuário e senha) |
   | `dashboard/painel.html` e `dashboard/assets/` | o painel |
   | `design/tokens/` | cores e tipografia |
   | `data/published/` | os dados (já sem colunas de identificação) |

   Uma pasta nova no repositório nunca vira arquivo publicado por descuido —
   precisa ser acrescentada à lista à mão. Arquivos `.md` e planilhas são
   descartados mesmo dentro de pasta permitida.

2. **`scripts/checar_publicacao.py`** confere o resultado contra o contrato de
   dados e falha se encontrar:

   - qualquer planilha (`.xlsm`, `.xlsx`, `.xls`) no pacote;
   - qualquer arquivo vindo de `data/raw/` ou `data/processed/`;
   - qualquer coluna marcada `sensivel: true` nos dados publicados —
     conferido contra a união das colunas sigilosas de **todos** os datasets,
     não só as do dataset de mesmo nome;
   - qualquer arquivo inesperado na camada publicada (uma cópia manual, um
     resto de teste) — arquivo que não é dataset do contrato, histórico ou
     manifesto não passou por nenhuma remoção de sigilo;
   - um manifesto que declare coluna sigilosa como publicada.

A separação é intencional: a montagem escolhe o que entra, a trava confere o
que entrou. A primeira erra por engano de configuração; a segunda, só se o
contrato estiver errado.

**Com o site público, a trava é a peça mais crítica do projeto.** Ela roda no
CI, roda no fluxo de publicação, e tem testes que plantam vazamentos de
propósito (`tests/test_publicacao.py`). Uma trava que nunca foi vista falhando
não é trava.

## Quem entra

O painel abre atrás de uma tela de usuário e senha (`dashboard/index.html`). A
credencial fica com a coordenação do edital; para trocá-la, ver
[ADR 0006](adr/0006-porta-de-entrada-no-painel.md).

**É uma cortina, não uma fechadura**, e a diferença muda o que pode ser
publicado. O painel é página estática: não há servidor conferindo nada, quem
abrir o código-fonte vê como passar, e `data/published/` continua acessível por
URL direta e no repositório público. A porta evita que o link caia em quem não
foi convidado — não protege dado sigiloso.

Por isso a regra de sigilo continua sendo a mesma de sempre: **dado que não
pode vazar não sai de `data/processed/`**, e é `checar_publicacao.py` que cobra
isso. A porta não afrouxa nenhuma linha desta página.

## Depois de publicar

1. Abra o endereço em janela anônima e confira que o painel carrega.
2. Confira que `https://movimentobemmaior.github.io/redes_bahia/data/published/credenciamento.csv`
   **não** tem colunas de nome nem e-mail de pessoa.
3. Confira que `.../data/raw/` e `.../data/processed/` respondem 404.

O passo 2 não é formalidade. É a verificação de que a trava fez o trabalho dela
no ambiente real, e não só no CI.

## Se algo sigiloso for parar no ar

O site é público e indexável — tirar do ar não desfaz o que já foi copiado.
Mesmo assim, na ordem:

1. Corrija a marcação em `config/fontes.yml` e rode `make dados && make site`.
2. Republique (o fluxo roda sozinho no push para `main`).
3. Limpe o histórico do git se o dado também entrou em `data/published/`
   versionado (`git filter-repo`) — apagar na última versão não basta.
4. Registre o incidente e comunique a coordenação: pode haver dever de
   notificação.
