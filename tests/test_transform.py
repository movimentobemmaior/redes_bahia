"""Padronização: a sujeira típica de planilha precisa entrar limpa — e o que
não puder ser convertido precisa virar aviso, nunca sumir em silêncio."""

from __future__ import annotations

import pandas as pd
import pytest

from pipeline.transform import padronizar


def _bruto(**colunas) -> pd.DataFrame:
    return pd.DataFrame(colunas)


def test_espacos_sobrando_sao_removidos(ds):
    r = padronizar(
        _bruto(
            ID=["  RB-001  "], CNPJ=["1"], Status=["Inscrita  "], Data=["01/03/2026"], Valor=[10]
        ),
        ds,
    )
    assert r.df.loc[0, "id_inscricao"] == "RB-001"
    assert r.df.loc[0, "status"] == "Inscrita"


def test_id_numerico_nao_vira_float(ds):
    """O Excel entrega 123 como 123.0; publicar '123.0' quebra qualquer junção."""
    r = padronizar(
        _bruto(ID=[123.0], CNPJ=[None], Status=["Inscrita"], Data=[None], Valor=[None]), ds
    )
    assert r.df.loc[0, "id_inscricao"] == "123"


def test_numero_em_formato_brasileiro(ds):
    r = padronizar(
        _bruto(
            ID=["a", "b", "c"],
            CNPJ=[None] * 3,
            Status=["Inscrita"] * 3,
            Data=[None] * 3,
            Valor=["R$ 1.234,56", "2.000", "-45,5"],
        ),
        ds,
    )
    assert r.df["valor_solicitado"].tolist() == [1234.56, 2000, -45.5]


def test_datas_em_formatos_misturados(ds):
    r = padronizar(
        _bruto(
            ID=["a", "b", "c"],
            CNPJ=[None] * 3,
            Status=["Inscrita"] * 3,
            Data=["21/04/2026", "2026-04-21", pd.Timestamp("2026-04-21")],
            Valor=[None] * 3,
        ),
        ds,
    )
    assert r.df["data_inscricao"].dt.date.astype(str).tolist() == ["2026-04-21"] * 3


def test_serie_numerica_do_excel_vira_data(ds):
    # 45000 = 2023-03-15 no calendário do Excel.
    r = padronizar(
        _bruto(ID=["a"], CNPJ=[None], Status=["Inscrita"], Data=[45000], Valor=[None]), ds
    )
    assert str(r.df.loc[0, "data_inscricao"].date()) == "2023-03-15"


def test_celula_vazia_e_texto_em_branco_viram_nulo(ds):
    r = padronizar(
        _bruto(
            ID=["a", "b"],
            CNPJ=[None, "  "],
            Status=["Inscrita", ""],
            Data=[None, None],
            Valor=[None, None],
        ),
        ds,
    )
    assert r.df["cnpj"].isna().all()
    assert r.df["status"].isna().sum() == 1


def test_valor_ilegivel_vira_aviso_com_exemplo(ds):
    r = padronizar(
        _bruto(ID=["a"], CNPJ=[None], Status=["Inscrita"], Data=[None], Valor=["a combinar"]), ds
    )
    aviso = next(p for p in r.problemas if p.codigo == "conversao_invalida")
    assert aviso.coluna == "valor_solicitado"
    assert aviso.linhas_afetadas == 1
    assert "a combinar" in [str(e) for e in aviso.exemplos]


def test_coluna_que_sumiu_da_planilha_e_erro(ds):
    r = padronizar(_bruto(ID=["a"], CNPJ=["1"], Status=["Inscrita"], Data=[None]), ds)
    erro = next(p for p in r.problemas if p.codigo == "coluna_ausente")
    assert erro.bloqueia
    assert erro.coluna == "valor_solicitado"
    # Mesmo ausente, a coluna existe na saída — o formato da base não muda.
    assert "valor_solicitado" in r.df.columns


def test_coluna_nova_na_planilha_vira_aviso(ds):
    r = padronizar(
        _bruto(ID=["a"], CNPJ=["1"], Status=["Inscrita"], Data=[None], Valor=[1], Observacao=["x"]),
        ds,
    )
    aviso = next(p for p in r.problemas if p.codigo == "coluna_nao_declarada")
    assert "Observacao" in aviso.exemplos
    assert "Observacao" not in r.df.columns


@pytest.mark.parametrize("entrada,esperado", [("Sim", True), ("NÃO", False), ("talvez", pd.NA)])
def test_booleano_aceita_sim_e_nao(cfg, ds, entrada, esperado):
    from pipeline.config import Coluna
    from pipeline.transform import _converter

    coluna = Coluna(nome="ativo", origem="Ativo", tipo="booleano")
    resultado = _converter(pd.Series([entrada]), coluna).iloc[0]
    if esperado is pd.NA:
        assert pd.isna(resultado)
    else:
        assert resultado == esperado
