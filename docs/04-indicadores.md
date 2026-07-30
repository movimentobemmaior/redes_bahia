# Indicadores do painel

> Reescrito em 30/07/2026, a partir da planilha real de credenciamento
> (13 respostas). O catálogo anterior tinha sido escrito antes do dado existir
> e supunha uma base de inscrições com avaliações, valores e territórios — que
> não é o que existe nesta etapa.
>
> **Estado: proposta.** Cada indicador só entra no painel depois de ter
> definição escrita, fonte no dicionário de dados e uma pessoa responsável.

## O que a base é hoje

Uma linha por organização que respondeu o **formulário de credenciamento**.
Não é ainda a base de propostas: é a etapa anterior, em que a organização
declara se atende aos requisitos e o sistema aprova ou não automaticamente.

Isso define o que dá e o que não dá para medir:

| Dá para medir | Não dá (ainda não existe na base) |
|---|---|
| quantas organizações se credenciaram | propostas, projetos, valores |
| quantas foram aprovadas e quantas não | notas, avaliadores, critérios de mérito |
| **qual requisito está barrando quem** | município, território de identidade |
| natureza jurídica das respondentes | etapas de análise, prazos |
| estado de origem | |
| evolução diária de tudo isso | |

Quando a etapa de inscrição começar, entra uma segunda aba/planilha e o
catálogo cresce. Mapas por território dependem de uma coluna de município, que
o formulário de credenciamento não coleta.

## Cuidado que vale para o painel inteiro

São **13 respostas**. Qualquer percentual se move mais de 7 pontos com uma
resposta a mais. Enquanto a base for desse tamanho, o painel deve mostrar
**números absolutos**, com o percentual em segundo plano — ou não mostrar
percentual nenhum. Gráfico de pizza com 13 casos comunica uma precisão que o
dado não tem.

## Formato de cada ficha

```
ID · Nome
Pergunta que responde
Cálculo:      numerador / denominador
Fonte:        dataset.coluna
Forma:        como se lê melhor visualmente
Cuidado:      o que faz esse número mentir
```

---

## Bloco 1 — Alcance

### A1 · Organizações credenciadas
- **Pergunta:** quantas organizações passaram pelo formulário?
- **Cálculo:** contagem de linhas em `credenciamento`
- **Fonte:** `credenciamento.id`
- **Forma:** número de destaque, com a variação desde a última atualização
- **Cuidado:** conta respostas, não organizações distintas. Se a mesma
  organização puder responder duas vezes, A1 e A2 divergem — hoje
  `organizacao` é única nas 13 respostas, mas isso não está garantido por
  regra no contrato.

### A2 · Origem geográfica
- **Pergunta:** de onde vêm as respostas?
- **Cálculo:** contagem por `estado`
- **Fonte:** `credenciamento.estado`
- **Forma:** barras horizontais; a Bahia domina, então o valor informativo
  está nas outras
- **Cuidado:** o edital é para organizações com sede na Bahia, mas o
  formulário aceita respostas de outros estados. Resposta de fora não é erro
  de dado — é organização inelegível que respondeu mesmo assim, e ela precisa
  aparecer, não ser filtrada em silêncio.

### A3 · Natureza jurídica
- **Cálculo:** contagem por `representa`
- **Fonte:** `credenciamento.representa`
- **Cuidado:** "Nenhuma das opções" é o valor mais informativo da lista — é
  quem não se encaixa no desenho do edital. Não agrupar em "Outros".

---

## Bloco 2 — Funil de elegibilidade (o bloco central)

### B1 · Resultado do credenciamento
- **Pergunta:** quantas passaram?
- **Cálculo:** contagem por `status_credenciamento`
- **Fonte:** `credenciamento.status_credenciamento`
- **Forma:** duas barras ou dois números lado a lado, absolutos
- **Cuidado:** "Aprovado automaticamente" significa que o sistema conferiu as
  respostas declaradas — não que a organização foi verificada. A comprovação
  vem depois (ver `ciencia_comprovacao_receita`). O painel não pode dar a
  entender que é decisão final.

### B2 · Qual requisito está barrando — o indicador que gera ação
- **Pergunta:** entre as não aprovadas, qual critério cada uma deixou de
  atender?
- **Cálculo:** entre linhas com `status_credenciamento = "Não aprovado"`,
  contagem de cada critério na condição de exclusão:

  | Critério | Exclui quando |
  |---|---|
  | `criterio_sede_bahia` | `Não` |
  | `criterio_atuacao_apenas_bahia` | `Não` |
  | `criterio_municipios_ate_200mil` | `Não` |
  | `criterio_em_atividade` | `Não` |
  | `criterio_estatuto_registrado` | `Não` |
  | `criterio_regularidade_credito` | `Não` |
  | `criterio_atuacao_minima_3_anos` | `Não` |
  | `criterio_receita_acima_500mil` | **`Sim`** |
  | `criterio_vinculo_partidario` | **`Sim`** |
  | `criterio_fins_religiosos` | **`Sim`** |

- **Forma:** barras horizontais ordenadas pela frequência
- **Cuidado:** **três critérios têm o sentido invertido** — neles, "Sim"
  exclui. Ler todos como "Sim = bom" é o erro mais provável deste painel, e
  produziria um gráfico exatamente ao contrário da realidade. O sentido está
  registrado na descrição de cada coluna no
  [dicionário](03-dicionario-de-dados.md).
- **Cuidado 2:** uma organização pode falhar em mais de um critério, então a
  soma das barras é maior que o número de não aprovadas. O eixo precisa dizer
  isso, ou o leitor soma e não bate.

### B3 · Requisito mais restritivo
- **Pergunta:** qual exigência do edital exclui mais gente?
- **Cálculo:** entre **todas** as respostas (não só as reprovadas), proporção
  que não atende cada critério
- **Cuidado:** diferente de B2. B2 explica quem já foi barrado; B3 informa o
  desenho do próximo edital. Vale separar as duas telas.

### B4 · Coletivos sem dois representantes
- **Fonte:** `credenciamento.criterio_dois_representantes`
- **Cuidado:** não é Sim/Não. Organizações formais respondem "Não se aplica",
  e tratá-lo como booleano descarta ou distorce metade das respostas.

---

## Bloco 3 — Evolução

### C1 · Credenciamentos por dia
- **Cálculo:** contagem por `data_resposta`
- **Forma:** linha no tempo
- **Cuidado:** só cobre o período em que o formulário esteve aberto. Com dez
  dias de dados, é cedo para falar em tendência.

### C2 · Evolução do funil
- **Cálculo:** série de `historico.csv`, agrupamento `status_credenciamento`
- **Cuidado:** a série começa no primeiro dia em que o pipeline rodou
  (30/07/2026), não no início do edital. Deixar isso explícito no eixo.

---

## Bloco 4 — Qualidade da base (sempre visível)

Um painel que não mostra a saúde do próprio dado convida à decisão errada.

### D1 · Última atualização
- **Fonte:** `manifest.json → data_execucao`
- **Cuidado:** base com mais de 24h precisa ficar evidente na tela.

### D2 · Status da validação
- **Fonte:** `manifest.json → validacao.status`
- **Forma:** selo com cor de status **e** rótulo em texto (nunca cor sozinha)

### D3 · Preenchimento por coluna
- **Fonte:** `manifest.json → datasets[].colunas[].preenchimento`
- **Cuidado:** `edital` está hoje em 0%. Coluna vazia no painel é diferente de
  coluna ausente — a primeira é normal, a segunda bloqueia a publicação.

---

## Pendências para a coordenação

1. `status_credenciamento` pode ter outros valores além de "Aprovado
   automaticamente" e "Não aprovado"? (há aprovação manual em algum caso?)
2. A coluna `Edital` vai passar a ser preenchida? Ela permitiria separar
   edições e comparar entre elas.
3. Organizações de fora da Bahia devem aparecer no painel ou ser filtradas?
   A recomendação aqui é aparecer — some do painel, some da análise.
4. A base de **inscrições** (propostas) virá em outra planilha? Se sim, o
   painel de funil de mérito é uma segunda etapa, com contrato próprio.
5. Confirmar o sentido de exclusão dos três critérios invertidos (B2) antes de
   qualquer gráfico ir ao ar.
