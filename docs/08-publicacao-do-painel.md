# Publicação do painel

Como o painel vai ao ar, e o que nunca vai junto.

## A decisão

O painel é **público**, no GitHub Pages
([ADR 0005](adr/0005-painel-publico-no-github-pages.md)).

Endereço, depois do primeiro deploy:

```
https://movimentobemmaior.github.io/redes_bahia/
```

Não há login. Qualquer pessoa com o endereço vê nome das organizações,
município, território, valor solicitado, status, etapa e notas — inclusive de
propostas ainda em análise. Isso foi decidido conscientemente; as consequências
estão listadas no ADR.

**O repositório continua privado.** As duas coisas convivem de propósito:

| | Onde vive | Quem enxerga |
|---|---|---|
| Planilhas originais (`data/raw/`) | repositório privado | quem tem acesso ao repositório |
| Base interna completa (`data/processed/`) | repositório privado | quem tem acesso ao repositório |
| Base do painel (`data/published/`) | repositório privado **e** site público | qualquer pessoa |

O que separa uma coisa da outra não é a configuração do GitHub — é a montagem
do pacote, descrita abaixo.

## Ligar pela primeira vez

Passo manual, uma vez só:

> **Settings → Pages → Build and deployment → Source: _GitHub Actions_**

Depois disso o fluxo **Publicar painel** cuida do resto, a cada atualização da
base.

⚠️ **GitHub Pages em repositório privado exige plano pago.** Se o fluxo falhar
por isso, a saída é assinar o plano — **não** tornar o repositório público.
`data/raw/` guarda as planilhas com CNPJ e e-mail; abrir o repositório
publicaria isso, o que é um problema de outra ordem. Ver
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
   | `dashboard/index.html` e `dashboard/assets/` | a página |
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

## Depois de publicar

1. Abra o endereço em janela anônima e confira que o painel carrega.
2. Confira que `https://movimentobemmaior.github.io/redes_bahia/data/published/inscricoes.csv`
   **não** tem colunas de CNPJ nem e-mail.
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
