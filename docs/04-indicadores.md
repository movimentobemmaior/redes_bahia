# Indicadores do painel

> **Estado: proposta.** Este catálogo foi escrito a partir da estrutura provável
> da planilha, antes da validação com a coordenação do edital. Serve para abrir
> a conversa: o que confirmar, o que cortar, o que falta.
>
> Cada indicador só entra no painel depois de ter: definição escrita, fonte no
> dicionário de dados, e uma pessoa responsável por respondê-lo.

## Por que catalogar antes de desenhar

Um indicador sem definição escrita vira três números diferentes em três telas.
"Taxa de habilitação" pode ser sobre o total inscrito, sobre o total analisado
ou sobre o total que chegou ao comitê. As três leituras são defensáveis; o que
não é defensável é o painel não dizer qual delas está mostrando.

Por isso todo indicador aqui declara **numerador, denominador e recorte**.

## Formato de cada ficha

```
ID · Nome
Pergunta que responde
Cálculo:      numerador / denominador
Fonte:        dataset.coluna
Recorte:      dimensões em que pode ser fatiado
Forma:        como se lê melhor visualmente
Cuidado:      o que faz esse número mentir
```

---

## Bloco 1 — Alcance do edital

### A1 · Inscrições recebidas
- **Pergunta:** quantas propostas o edital atraiu?
- **Cálculo:** contagem de linhas em `inscricoes`
- **Fonte:** `inscricoes.id_inscricao`
- **Recorte:** território, eixo, município, semana
- **Forma:** número de destaque, com a variação desde a última atualização
- **Cuidado:** conta propostas, não organizações. Uma organização pode inscrever
  mais de uma proposta — se isso for comum, separar A1 de A2.

### A2 · Organizações proponentes
- **Pergunta:** quantas organizações diferentes o edital alcançou?
- **Cálculo:** contagem de `organizacao` distintos
- **Fonte:** `inscricoes.organizacao`
- **Cuidado:** depende da grafia estar padronizada. "Assoc. Rede" e "Associação
  Rede" contam como duas. Vale conferir com o CNPJ (base interna) e padronizar
  a grafia na planilha.

### A3 · Cobertura territorial
- **Pergunta:** quantos dos 27 Territórios de Identidade têm ao menos uma
  proposta?
- **Cálculo:** territórios com inscrição / 27
- **Fonte:** `inscricoes.territorio_identidade`
- **Forma:** mapa da Bahia com rampa sequencial de uma cor só; ao lado, a lista
  dos territórios sem nenhuma inscrição
- **Cuidado:** o vazio no mapa é o dado mais importante, e é o que a maioria dos
  mapas esconde. Território sem inscrição precisa ficar visualmente distinto de
  território com poucas inscrições.

### A4 · Concentração territorial
- **Pergunta:** o edital está concentrado em poucos territórios?
- **Cálculo:** % das inscrições nos 3 territórios com mais propostas
- **Cuidado:** número alto pode significar tanto desigualdade de acesso quanto
  concentração populacional. Ler junto com A5.

### A5 · Inscrições por 100 mil habitantes
- **Pergunta:** onde a mobilização foi proporcionalmente maior?
- **Cálculo:** inscrições do município / população × 100.000
- **Fonte:** `inscricoes` + `municipios.populacao`
- **Cuidado:** em município pequeno, uma inscrição a mais desloca muito a taxa.
  Suprimir municípios abaixo de um limite de população, ou mostrar o valor
  absoluto junto.

---

## Bloco 2 — Andamento da análise

### B1 · Funil do edital
- **Pergunta:** onde estão as propostas agora?
- **Cálculo:** contagem por `status`, na ordem do processo
- **Fonte:** `inscricoes.status`
- **Forma:** funil ou barras horizontais ordenadas pela etapa, com o percentual
  em relação ao total inscrito
- **Cuidado:** `status` e `etapa` são coisas diferentes (situação × ponto do
  fluxo). Misturar as duas é o erro mais provável deste painel.

### B2 · Propostas sem análise há mais de N dias
- **Pergunta:** o que está parado?
- **Cálculo:** inscrições em `Em análise` com `data_inscricao` anterior a N dias
- **Forma:** número de destaque com cor de status, mais a lista
- **Cuidado:** é o indicador que gera ação. Vale definir N com a coordenação
  antes de publicar.

### B3 · Tempo médio até a decisão
- **Pergunta:** quanto tempo leva para uma proposta ser decidida?
- **Cálculo:** média de (`data_avaliacao` mais recente − `data_inscricao`)
- **Cuidado:** média esconde a cauda. Mostrar também a mediana e o percentil 90,
  ou preferir a distribuição à média.

### B4 · Evolução do funil
- **Pergunta:** o processo está andando?
- **Cálculo:** série de `historico.csv`, agrupamento `status`
- **Forma:** linhas no tempo, uma por status, com rótulo direto nas séries
- **Cuidado:** a série só existe a partir do primeiro dia em que o pipeline
  rodou. Deixar isso explícito no eixo.

---

## Bloco 3 — Avaliação

### C1 · Distribuição das notas finais
- **Forma:** histograma
- **Cuidado:** média de notas de propostas em etapas diferentes compara coisas
  diferentes. Filtrar por etapa antes.

### C2 · Dispersão entre avaliadores
- **Pergunta:** avaliadores diferentes dão notas parecidas para a mesma
  proposta?
- **Cálculo:** desvio-padrão das notas por `id_inscricao`
- **Fonte:** `avaliacoes`
- **Cuidado:** indicador sensível — mede o processo, e pode ser lido como
  avaliação de pessoas. Definir com a coordenação se entra no painel público.

### C3 · Desempenho por critério
- **Forma:** barras horizontais, um critério por barra, ordenadas pela média
- **Cuidado:** critérios com pesos diferentes não são comparáveis na mesma
  escala sem normalizar.

---

## Bloco 4 — Recursos

### D1 · Valor total solicitado
- **Cálculo:** soma de `valor_solicitado`
- **Cuidado:** só faz sentido junto com o valor disponível no edital. Sozinho,
  não informa nada.

### D2 · Valor solicitado por proposta
- **Forma:** distribuição (boxplot ou histograma), não média
- **Cuidado:** poucas propostas grandes deslocam a média. A distribuição é a
  leitura honesta.

### D3 · Razão demanda/oferta
- **Cálculo:** valor total solicitado / valor disponível no edital
- **Pendência:** o valor disponível não está na planilha. Precisa entrar como
  parâmetro de configuração.

---

## Bloco 5 — Qualidade da base (sempre visível)

Um painel que não mostra a saúde do próprio dado convida a decisão errada.

### E1 · Última atualização
- **Fonte:** `manifest.json → data_execucao`
- **Cuidado:** se a base tem mais de 24h, precisa ficar evidente na tela.

### E2 · Status da validação
- **Fonte:** `manifest.json → validacao.status`
- **Forma:** selo com cor de status **e** rótulo em texto (nunca cor sozinha)

### E3 · Preenchimento por coluna
- **Fonte:** `manifest.json → datasets[].colunas[].preenchimento`
- **Cuidado:** coluna abaixo de 100% em indicador de contagem significa que o
  total do painel não bate com o total da planilha.

---

## Pendências para a coordenação

1. Qual a lista oficial e a ordem dos `status`? (hoje o contrato tem uma
   suposição)
2. `status` e `etapa` são dimensões independentes?
3. Qual o valor total disponível no edital? (D3)
4. Qual o prazo aceitável de análise? (B2)
5. C2 (dispersão entre avaliadores) entra no painel ou fica em relatório
   interno?
6. O painel será público ou restrito? A resposta muda o que pode ser publicado
   (ver [governança](06-governanca-e-lgpd.md)).
