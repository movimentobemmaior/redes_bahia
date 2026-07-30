"""O contrato de dados é a peça central: erro nele precisa falhar alto e claro."""

from __future__ import annotations

from datetime import date

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


# --- Geografia ----------------------------------------------------------------


def test_geografia_ausente_e_valida(tmp_path, contrato):
    """Sem o bloco, o painel simplesmente não desenha o mapa."""
    cfg = carregar(escrever_contrato(tmp_path, contrato))
    assert cfg.geografia is None


def test_geografia_e_lida(tmp_path, contrato):
    contrato["geografia"] = {"coluna": "status", "nivel": "estado", "destaque": "BA"}
    cfg = carregar(escrever_contrato(tmp_path, contrato))
    assert (cfg.geografia.coluna, cfg.geografia.nivel, cfg.geografia.destaque) == (
        "status",
        "estado",
        "BA",
    )


def test_geografia_com_coluna_inexistente_e_recusada(tmp_path, contrato):
    """O mapa mudo é indistinguível de 'sem dado' — o erro tem de vir aqui."""
    contrato["geografia"] = {"coluna": "municipio", "nivel": "municipio"}
    with pytest.raises(ErroConfig, match="'municipio' não está declarada"):
        carregar(escrever_contrato(tmp_path, contrato))


def test_geografia_com_nivel_desconhecido_e_recusada(tmp_path, contrato):
    contrato["geografia"] = {"coluna": "status", "nivel": "bairro"}
    with pytest.raises(ErroConfig, match="bairro"):
        carregar(escrever_contrato(tmp_path, contrato))


def test_datas_do_edital_viram_iso(tmp_path, contrato):
    """O YAML entrega `date`; o manifesto precisa de texto AAAA-MM-DD."""
    contrato["edital"] = {"inicio_inscricoes": date(2026, 7, 27), "fim_inscricoes": "2026-08-17"}
    cfg = carregar(escrever_contrato(tmp_path, contrato))
    assert cfg.edital.inicio_inscricoes == "2026-07-27"
    assert cfg.edital.fim_inscricoes == "2026-08-17"
