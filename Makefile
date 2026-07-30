.DEFAULT_GOAL := ajuda
PY ?= python3

.PHONY: ajuda instalar exemplo perfil validar dados dicionario malhas teste lint formatar painel site limpar tudo

ajuda:  ## mostra esta ajuda
	@echo "Painel Redes Bahia — comandos disponíveis:"
	@echo
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[1m%-12s\033[0m %s\n", $$1, $$2}'
	@echo
	@echo "Rotina do dia: coloque o .xlsm em data/raw/ e rode 'make dados'."

instalar:  ## instala as dependências de desenvolvimento
	$(PY) -m pip install -r requirements-dev.txt

exemplo:  ## gera uma planilha de exemplo em data/raw/ (para testar sem o arquivo real)
	$(PY) scripts/gerar_exemplo.py

perfil:  ## inspeciona o .xlsm mais recente e propõe um contrato de dados
	$(PY) -m pipeline perfil

validar:  ## valida a planilha do dia sem publicar nada
	$(PY) -m pipeline validar

dados:  ## ROTINA DIÁRIA: valida a planilha e publica a base do painel
	$(PY) -m pipeline dados

dicionario:  ## regera docs/03-dicionario-de-dados.md a partir do contrato
	$(PY) -m pipeline dicionario

malhas:  ## refaz as malhas do mapa a partir das fontes públicas (precisa de rede)
	$(PY) scripts/gerar_malhas.py

teste:  ## roda os testes
	$(PY) -m pytest

lint:  ## checa o estilo do código
	$(PY) -m ruff check .

formatar:  ## formata o código
	$(PY) -m ruff format pipeline tests scripts && $(PY) -m ruff check . --fix

painel:  ## abre o painel local em http://localhost:8000
	@echo "Painel em http://localhost:8000/dashboard/  (Ctrl+C para parar)"
	@$(PY) -m http.server 8000

site:  ## monta o pacote do painel em _site/ e roda a trava de sigilo
	$(PY) scripts/montar_site.py
	$(PY) scripts/checar_publicacao.py

limpar:  ## apaga saídas intermediárias e relatórios locais
	rm -rf data/interim/* reports/* _site .pytest_cache .ruff_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +

tudo: lint teste dados  ## checagem completa: estilo, testes e pipeline
