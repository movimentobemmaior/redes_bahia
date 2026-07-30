# Roteiro

## Onde estamos

**Fase 1 — Base estática (esta entrega).** A planilha do dia entra, vira base
validada, versionada e documentada. O painel ainda não existe; o que existe é
o chão em que ele vai ser construído.

Entregue:

- contrato de dados declarativo (`config/fontes.yml`);
- pipeline de leitura, padronização, validação e publicação;
- separação entre base interna e base publicada, com retenção de dado sigiloso;
- histórico diário, que permite série temporal a partir de fotos diárias;
- manifesto com procedência e resultado da validação;
- dicionário de dados gerado a partir do contrato;
- ferramenta de perfilamento para quando a planilha mudar;
- automação: subiu o `.xlsm`, a base se atualiza sozinha;
- tokens de design e regras visuais definidos e verificados;
- página de estado da base (`dashboard/`);
- testes cobrindo o caminho completo.

## Fase 2 — Ajuste ao dado real

Assunto para o dia em que o `.xlsm` de verdade chegar.

1. `make perfil` na planilha real.
2. Reescrever `config/fontes.yml` a partir do que existe de fato (o contrato
   atual é uma suposição).
3. Confirmar com a coordenação: lista de `status`, relação entre `status` e
   `etapa`, quais colunas são sigilosas, qual é a chave de cada aba.
4. Rodar com dados reais por alguns dias e ajustar as regras que gerarem ruído.
5. Fechar o catálogo de indicadores ([04](04-indicadores.md)).

**Critério para sair da fase 2:** uma semana de execuções diárias sem erro de
estrutura, e o catálogo de indicadores assinado pela coordenação.

## Fase 3 — Painel

1. Telas: visão geral, território, funil, avaliação.
2. Gráficos seguindo [05](05-identidade-visual.md), sobre `data/published/`.
3. Filtros: período, território, eixo, status.
4. Bloco de qualidade da base sempre visível (E1–E3 do catálogo).
5. Publicação (GitHub Pages ou hospedagem própria) — depende da decisão sobre
   painel público ou restrito.

## Fase 4 — Além do piloto

Coisas que o piloto deliberadamente não resolve, com o gatilho de quando passam
a valer a pena:

| Item | Quando passa a valer a pena |
|---|---|
| Banco de dados (DuckDB/Postgres) no lugar de arquivos | quando o JSON publicado passar de ~5 MB ou a leitura ficar lenta |
| Ingestão direta do sistema de inscrição, sem planilha | quando existir API |
| Mais de uma fonte por dia | quando outra base (execução, prestação de contas) entrar |
| Alerta automático quando a validação falha | quando o painel virar rotina de decisão |
| Comparação entre editais | a partir da segunda edição |
| Camada semântica (dbt ou equivalente) | quando os indicadores começarem a divergir entre telas |

## Riscos conhecidos

| Risco | Efeito | Como está tratado |
|---|---|---|
| A planilha muda de formato sem aviso | pipeline para | erro claro apontando a coluna + `make perfil` para diagnosticar |
| Grafia inconsistente (município, status) | contagem errada, buraco no mapa | vira aviso na validação, com os valores listados |
| Ninguém sobe a planilha por vários dias | painel desatualizado sem parecer | data da última atualização em destaque na tela |
| Dado sigiloso vazar para a camada publicada | incidente de LGPD | remoção automática + teste que falha se acontecer |
| Chave duplicada | todo total do painel fica errado | erro que bloqueia a publicação |
| O contrato atual é uma suposição | retrabalho na fase 2 | aviso explícito no topo de `config/fontes.yml` |
