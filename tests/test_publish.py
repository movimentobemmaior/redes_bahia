"""Publicação: o que sai para o painel, e o que nunca pode sair."""

from __future__ import annotations

import dataclasses
import json
from datetime import date

import pandas as pd
import pytest

from pipeline import publish
from pipeline.ingest import Arquivo
from pipeline.problemas import AVISO, Problema


@pytest.fixture
def saidas(tmp_path, monkeypatch):
    monkeypatch.setattr(publish, "DIR_PROCESSED", tmp_path / "processed")
    monkeypatch.setattr(publish, "DIR_PUBLISHED", tmp_path / "published")
    return tmp_path


@pytest.fixture
def cfg_temp(cfg, tmp_path):
    historico = dataclasses.replace(cfg.historico, arquivo=tmp_path / "historico.csv")
    return dataclasses.replace(cfg, historico=historico)


@pytest.fixture
def tabelas():
    return {
        "inscricoes": pd.DataFrame(
            {
                "id_inscricao": pd.Series(["a", "b"], dtype="string"),
                "cnpj": pd.Series(["11.111.111/0001-11", "22"], dtype="string"),
                "status": pd.Series(["Inscrita", "Em análise"], dtype="string"),
                "data_inscricao": pd.to_datetime(["2026-01-01", "2026-01-02"]),
                "valor_solicitado": pd.Series([10.0, 20.0], dtype="Float64"),
            }
        )
    }


def _publicar(cfg_temp, tabelas, problemas=None, dia="2026-05-01"):
    return publish.publicar(
        tabelas=tabelas,
        cfg=cfg_temp,
        arquivo=Arquivo(caminho=pd.io.common.Path("planilha.xlsm"), hash_sha256="abc", bytes=1),
        problemas=problemas or [],
        data_execucao=date.fromisoformat(dia),
        versao_pipeline="teste",
    )


def test_coluna_sensivel_nao_sai_para_o_painel(saidas, cfg_temp, tabelas):
    _publicar(cfg_temp, tabelas)
    publicado = pd.read_csv(saidas / "published" / "inscricoes.csv")
    interno = pd.read_csv(saidas / "processed" / "inscricoes.csv")
    assert "cnpj" not in publicado.columns
    assert "cnpj" in interno.columns, "a base interna precisa manter o dado completo"


def test_json_do_painel_serializa_datas_e_nulos(saidas, cfg_temp, tabelas):
    tabelas["inscricoes"].loc[0, "valor_solicitado"] = pd.NA
    _publicar(cfg_temp, tabelas)
    registros = json.loads((saidas / "published" / "inscricoes.json").read_text(encoding="utf-8"))
    assert registros[0]["data_inscricao"] == "2026-01-01"
    assert registros[0]["valor_solicitado"] is None


def test_manifesto_registra_status_e_origem(saidas, cfg_temp, tabelas):
    problema = Problema(dataset="inscricoes", codigo="x", gravidade=AVISO, mensagem="teste")
    manifesto = _publicar(cfg_temp, tabelas, [problema])
    assert manifesto["validacao"]["status"] == "com_avisos"
    assert manifesto["fonte"]["hash_sha256"] == "abc"
    assert manifesto["datasets"][0]["colunas_omitidas_por_sigilo"] == ["cnpj"]
    gravado = json.loads((saidas / "published" / "manifest.json").read_text(encoding="utf-8"))
    assert gravado == manifesto


def test_historico_acumula_dias_diferentes(saidas, cfg_temp, tabelas):
    _publicar(cfg_temp, tabelas, dia="2026-05-01")
    _publicar(cfg_temp, tabelas, dia="2026-05-02")
    hist = pd.read_csv(cfg_temp.historico.arquivo)
    assert sorted(hist["data_execucao"].unique()) == ["2026-05-01", "2026-05-02"]


def test_reexecutar_no_mesmo_dia_substitui_em_vez_de_duplicar(saidas, cfg_temp, tabelas):
    _publicar(cfg_temp, tabelas, dia="2026-05-01")
    antes = len(pd.read_csv(cfg_temp.historico.arquivo))
    _publicar(cfg_temp, tabelas, dia="2026-05-01")
    assert len(pd.read_csv(cfg_temp.historico.arquivo)) == antes


def test_historico_conta_por_categoria(saidas, cfg_temp, tabelas):
    _publicar(cfg_temp, tabelas)
    hist = pd.read_csv(cfg_temp.historico.arquivo)
    por_status = hist[hist["agrupamento"] == "status"].set_index("categoria")["valor"]
    assert por_status["Inscrita"] == 1
    assert hist[hist["agrupamento"] == "total"]["valor"].iloc[0] == 2
