## O que muda

<!-- Uma ou duas frases. Se muda o contrato de dados, diga o que muda na planilha. -->

## Por quê

<!-- Que problema resolve. Se for decisão de rumo, aponte o ADR. -->

## Como conferir

<!-- Passos para quem revisa. Ex.: make exemplo && make dados; ver reports/validacao.md -->

## Checklist

- [ ] `make lint` e `make teste` passam
- [ ] `make dados` roda de ponta a ponta
- [ ] documentação afetada atualizada (o dicionário é gerado, não editado à mão)
- [ ] nenhuma coluna sigilosa nova sem `sensivel: true` no contrato
- [ ] decisão de rumo registrada em `docs/adr/`

## Impacto nos dados

- [ ] não altera a base publicada
- [ ] altera a base publicada — o quê:
- [ ] altera o contrato de dados — o quê:
