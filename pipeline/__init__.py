"""Pipeline de dados do Painel Redes Bahia.

Fluxo: data/raw/*.xlsm -> leitura -> padronização -> validação -> publicação
       -> data/processed/ (base completa) e data/published/ (base do painel).

Uso: python -m pipeline --help
"""

__all__ = ["__version__"]
__version__ = "0.1.0"
