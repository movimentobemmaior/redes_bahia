# Publicação do painel

Como o painel chega até o comitê, e por que não é só "ligar o GitHub Pages".

## A decisão

O painel é **restrito ao comitê**. Não é público. Ver
[ADR 0004](adr/0004-painel-restrito-ao-comite.md).

Isso tem uma consequência que costuma pegar as pessoas de surpresa:

> **GitHub Pages serve o site publicamente mesmo quando o repositório é
> privado.** Repositório privado protege o *código* e os *arquivos*; não
> protege o *site* gerado a partir deles. A única exceção é o GitHub
> Enterprise Cloud, que tem controle de acesso no Pages.

E há um segundo risco, pior: configurado no modo padrão ("deploy from branch,
pasta raiz"), o Pages serve **o repositório inteiro** — inclusive
`data/raw/*.xlsm` e `data/processed/*.csv`, com CNPJ e e-mail. Sem login, e
indexável por buscadores.

Por isso o projeto nunca hospeda a pasta raiz.

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
   | `data/published/` | os dados (já sem colunas sigilosas) |

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
contrato estiver errado. Ambas rodam no fluxo **Publicar painel**, e a trava
tem testes que plantam vazamentos de propósito
(`tests/test_publicacao.py`).

## Onde hospedar — decisão em aberto

O pacote está pronto (o fluxo **Publicar painel** o deixa como artefato
`painel` a cada atualização). Falta escolher onde ele fica, e "restrito ao
comitê" exige autenticação em algum ponto — não existe link que só algumas
pessoas conseguem abrir sem alguém verificar quem elas são.

| Opção | Como funciona | Custo / condição |
|---|---|---|
| **A. Cloudflare Pages + Cloudflare Access** | O pacote é publicado no Cloudflare Pages e o Access fica na frente, liberando por lista de e-mails. Quem não está na lista não abre. | Gratuito até 50 pessoas. Exige um domínio no Cloudflare e configurar o Access uma vez. **É a recomendação.** |
| **B. GitHub Pages com controle de acesso** | Os passos já estão no fluxo, comentados. | Só existe no **GitHub Enterprise Cloud**. Em qualquer outro plano, o site fica público — o que contraria a decisão. |
| **C. Servidor interno da organização** | O pacote é copiado para um servidor que já exige login corporativo. | Depende de haver esse servidor e de alguém para operá-lo. |
| **D. Sem link: cada pessoa baixa o artefato** | Baixar o artefato `painel` do Actions e abrir localmente. | Funciona hoje, sem nenhuma configuração, mas é ruim para comitê: exige conta no repositório e descompactar arquivo. Serve como paliativo. |

**O que não é opção:** publicar em URL pública "difícil de adivinhar". Link não
listado não é controle de acesso — basta uma pessoa encaminhar o link, ou um
buscador achar, e o painel está aberto. Com nome de organização, valores
solicitados e notas na tela, isso é uma publicação de fato.

## Quando a hospedagem for escolhida

1. Registrar a escolha em um ADR novo.
2. Descomentar (ou substituir) o passo de hospedagem em
   `.github/workflows/publicar-painel.yml`.
3. Conferir, com uma janela anônima e sem login, que o painel **não** abre.
4. Atualizar este documento com o endereço e quem tem acesso.

O passo 3 não é formalidade: é o único jeito de saber que o controle de acesso
está mesmo ligado.
