# `data/raw/` — a planilha do dia entra aqui

Esta é a **única pasta** em que se mexe na rotina diária.

## O que fazer

1. Exporte/salve a planilha do edital como `.xlsx`.
2. Renomeie usando a data de referência, no formato:

   ```
   AAAA-MM-DD_redes_bahia.xlsx
   ```

   Exemplo: `2026-08-01_redes_bahia.xlsx`

3. Coloque o arquivo aqui e faça o commit (ou arraste pelo site do GitHub).
4. O fluxo **Atualizar base** roda sozinho e regera `data/published/`.
   Para rodar na sua máquina: `make dados`.

## Regras

- **Nunca sobrescreva** um arquivo de dia anterior. Cada dia é um arquivo novo:
  o histórico da pasta é o que permite refazer qualquer publicação passada.
- O nome define qual arquivo é o mais recente (a ordenação é por nome, não pela
  data do sistema). Data errada no nome = base errada publicada.
- Se a estrutura da planilha mudar (coluna nova, aba renomeada), o pipeline
  **para e avisa**. Rode `make perfil` para ver o que mudou e ajuste
  `config/fontes.yml`.

## Atenção — LGPD

Os arquivos desta pasta contêm dados de identificação (CNPJ, e-mail) e ficam
versionados no repositório. Por isso o repositório é **privado**, e precisa
continuar sendo.

As colunas marcadas como `sensivel: true` no contrato nunca chegam a
`data/published/`, mas isso protege a camada publicada, **não** esta pasta:
aqui o arquivo fica como veio. Ver `docs/06-governanca-e-lgpd.md`.
