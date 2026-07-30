from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from pipeline.config import Dataset, carregar  # noqa: E402

CONTRATO_MINIMO = {
    "versao": 1,
    "fonte": {"diretorio": "data/raw", "padrao_arquivo": "*.xlsm", "selecao": "mais_recente"},
    "publicacao": {"formatos": ["csv", "json"], "remover_sensiveis": True},
    "historico": {"arquivo": "data/published/historico.csv", "agrupar_por": ["status"]},
    "datasets": {
        "inscricoes": {
            "aba": "Inscricoes",
            "descricao": "teste",
            "linha_cabecalho": 1,
            "chave": ["id_inscricao"],
            "colunas": {
                "id_inscricao": {"origem": "ID", "tipo": "texto", "obrigatorio": True},
                "cnpj": {"origem": "CNPJ", "tipo": "texto", "sensivel": True},
                "status": {"origem": "Status", "tipo": "categoria"},
                "data_inscricao": {"origem": "Data", "tipo": "data"},
                "valor_solicitado": {"origem": "Valor", "tipo": "decimal"},
            },
            "regras": [
                {"tipo": "unico", "colunas": ["id_inscricao"]},
                {
                    "tipo": "valores_permitidos",
                    "coluna": "status",
                    "valores": ["Inscrita", "Em análise"],
                },
                {"tipo": "intervalo", "coluna": "valor_solicitado", "min": 0, "max": 1000},
                {"tipo": "minimo_linhas", "valor": 1},
            ],
        }
    },
}


def escrever_contrato(tmp_path: Path, contrato: dict) -> Path:
    caminho = tmp_path / "fontes.yml"
    caminho.write_text(
        yaml.safe_dump(contrato, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    return caminho


@pytest.fixture
def contrato() -> dict:
    """Cópia profunda do contrato mínimo, para os testes poderem sujá-lo à vontade."""
    import copy

    return copy.deepcopy(CONTRATO_MINIMO)


@pytest.fixture
def cfg(tmp_path: Path, contrato: dict):
    return carregar(escrever_contrato(tmp_path, contrato))


@pytest.fixture
def ds(cfg) -> Dataset:
    return cfg.datasets["inscricoes"]


@pytest.fixture
def contrato_com_referencia(tmp_path, contrato):
    """Contrato sintético com dois datasets e uma regra `referencia`.

    A regra é testada aqui, e não contra config/fontes.yml, para que o teste
    da funcionalidade não quebre toda vez que o contrato do projeto mudar.
    """
    contrato["datasets"]["avaliacoes"] = {
        "aba": "Avaliacoes",
        "descricao": "teste",
        "linha_cabecalho": 1,
        "chave": ["id_inscricao"],
        "colunas": {
            "id_inscricao": {"origem": "ID", "tipo": "texto", "obrigatorio": True},
            "nota": {"origem": "Nota", "tipo": "decimal"},
        },
        "regras": [
            {
                "tipo": "referencia",
                "coluna": "id_inscricao",
                "dataset": "inscricoes",
                "coluna_alvo": "id_inscricao",
            }
        ],
    }
    return carregar(escrever_contrato(tmp_path, contrato))


@pytest.fixture
def contrato_real():
    """O contrato de verdade do projeto — garante que ele nunca fica inválido."""
    return carregar(RAIZ / "config" / "fontes.yml")
