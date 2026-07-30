"""O contrato de dados é a peça central: erro nele precisa falhar alto e claro."""

from __future__ import annotations

import pytest

from pipeline.config import ErroConfig, carregar
from tests.conftest import escrever_contrato


def test_carrega_contrato_do_projeto(contrato_real):
    assert contrato_real.datasets, "config/fontes.yml deve declarar datasets"
    credenciamento = contrato_real.datasets["credenciamento"]
    assert credenciamento.chave == ("id",)
    # Se estas duas deixarem de estar marcadas, dado pessoal vai para o painel.
    assert set(credenciamento.sensiveis) == {"respondente_nome", "respondente_email"}


def test_tipo_desconhecido_e_recusado(tmp_path, contrato):
    contrato["datasets"]["inscricoes"]["colunas"]["status"]["tipo"] = "planilha"
    with pytest.raises(ErroConfig, match="tipo 'planilha' desconhecido"):
        carregar(escrever_contrato(tmp_path, contrato))


def test_regra_apontando_para_coluna_inexistente_e_recusada(tmp_path, contrato):
    contrato["datasets"]["inscricoes"]["regras"].append(
        {"tipo": "nao_nulo", "coluna": "coluna_fantasma"}
    )
    with pytest.raises(ErroConfig, match="coluna 'coluna_fantasma'"):
        carregar(escrever_contrato(tmp_path, contrato))


def test_chave_precisa_existir_entre_as_colunas(tmp_path, contrato):
    contrato["datasets"]["inscricoes"]["chave"] = ["nao_existe"]
    with pytest.raises(ErroConfig, match="chave"):
        carregar(escrever_contrato(tmp_path, contrato))


def test_referencia_para_dataset_inexistente_e_recusada(tmp_path, contrato):
    contrato["datasets"]["inscricoes"]["regras"].append(
        {"tipo": "referencia", "coluna": "id_inscricao", "dataset": "nao_existe"}
    )
    with pytest.raises(ErroConfig, match="dataset 'nao_existe'"):
        carregar(escrever_contrato(tmp_path, contrato))


def test_formato_de_publicacao_invalido_e_recusado(tmp_path, contrato):
    contrato["publicacao"]["formatos"] = ["csv", "xlsx"]
    with pytest.raises(ErroConfig, match="xlsx"):
        carregar(escrever_contrato(tmp_path, contrato))


def test_contrato_inexistente_da_mensagem_util(tmp_path):
    with pytest.raises(ErroConfig, match="não encontrado"):
        carregar(tmp_path / "nao_existe.yml")
