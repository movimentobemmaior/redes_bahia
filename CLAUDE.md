# Convenções deste repositório

Notas para quem (pessoa ou agente) for trabalhar aqui.

## Publicação

**Publique direto.** Terminou uma mudança com testes e lint passando: abra o
PR, merje e deixe o painel no ar. Não pare para pedir confirmação de merge —
a decisão já foi dada.

O que continua exigindo confirmação é o que muda o rumo do projeto: trocar a
audiência do painel, mudar o que bloqueia publicação, expor dado de
identificação. Isso vira ADR e passa pela coordenação.

## Antes de publicar

```bash
make lint && make teste && make dados && make site
```

`make site` é a trava de sigilo: monta o pacote por lista de permissão e falha
se algo que não devia sair aparecer nele.

## Onde as decisões moram

- **Estrutura da planilha** → `config/fontes.yml`, não no código Python.
- **Regra de elegibilidade** (`exclui_quando`) → contrato, não no JavaScript
  do painel. Três critérios do edital têm sentido invertido: "Sim" exclui.
- **Etapas do edital** → bloco `etapas:` do contrato. O painel monta o funil a
  partir dele.
- **Mapa: nível e recorte territorial** → bloco `geografia:` do contrato,
  inclusive o corte de população do edital (`territorio.limite_populacao`). A
  malha e a população ficam em `dashboard/assets/geo/`, geradas por
  `make malhas`.
- **Cor e tipografia** → `design/tokens/`, derivados de
  `docs/Edital-RedesBahia.pdf`.
- **Decisão de rumo** → um ADR em `docs/adr/`.

## Cuidados que já custaram caro

- Trocar hex de série exige revalidar a paleta para daltonismo e contraste nos
  dois modos. A ordem dos slots faz parte da acessibilidade.
- Teste que escreve fora de `tmp_path` suja o repositório. Já aconteceu com o
  dicionário de dados e com a leitura de `data/raw/`.
- Coluna com nome e sem dado é coluna vazia, não coluna ausente.
- O repositório está público e as planilhas de origem ficam fora do git por
  isso (ver `.gitignore` e `docs/06-governanca-e-lgpd.md`).

## Idioma

Tudo em português: código, comentários, documentação e commits. Nomes técnicos
sem acento e sem espaço.
