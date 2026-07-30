"""Validação: a fronteira entre 'bloqueia a publicação' e 'apenas avisa'.

Essa distinção é a decisão de produto mais importante do piloto — se ela
regredir, ou o painel trava toda semana, ou publica dado quebrado calado.
"""

from __future__ import annotations

import pandas as pd

from pipeline.validate import validar


def _tabela(**colunas) -> dict[str, pd.DataFrame]:
    base = {
        "id_inscricao": pd.Series(dtype="string"),
        "cnpj": pd.Series(dtype="string"),
        "status": pd.Series(dtype="string"),
        "data_inscricao": pd.Series(dtype="datetime64[ns]"),
        "valor_solicitado": pd.Series(dtype="Float64"),
    }
    df = pd.DataFrame({**base, **{k: pd.Series(v) for k, v in colunas.items()}})
    return {"inscricoes": df.reindex(columns=list(base))}


def _codigos(problemas) -> set[str]:
    return {p.codigo for p in problemas}


def test_base_limpa_nao_gera_problema(cfg):
    tabelas = _tabela(
        id_inscricao=["a", "b"], status=["Inscrita", "Em análise"], valor_solicitado=[10.0, 20.0]
    )
    assert validar(tabelas, cfg) == []


def test_obrigatorio_vazio_bloqueia(cfg):
    problemas = validar(_tabela(id_inscricao=[None, "b"], status=["Inscrita", "Inscrita"]), cfg)
    erro = next(p for p in problemas if p.codigo == "obrigatorio_vazio")
    assert erro.bloqueia and erro.linhas_afetadas == 1


def test_chave_duplicada_bloqueia_e_identifica_a_chave(cfg):
    problemas = validar(_tabela(id_inscricao=["a", "a"], status=["Inscrita", "Inscrita"]), cfg)
    erro = next(p for p in problemas if p.codigo == "chave_duplicada")
    assert erro.bloqueia
    assert erro.linhas_afetadas == 2
    assert "a" in erro.exemplos


def test_categoria_nova_apenas_avisa(cfg):
    problemas = validar(_tabela(id_inscricao=["a"], status=["Reformulada"]), cfg)
    aviso = next(p for p in problemas if p.codigo == "valor_nao_previsto")
    assert not aviso.bloqueia
    assert aviso.exemplos == ["Reformulada"]


def test_valor_fora_do_intervalo_apenas_avisa(cfg):
    problemas = validar(
        _tabela(id_inscricao=["a"], status=["Inscrita"], valor_solicitado=[9999.0]), cfg
    )
    aviso = next(p for p in problemas if p.codigo == "fora_do_intervalo")
    assert not aviso.bloqueia


def test_aba_vazia_bloqueia(cfg):
    assert "poucas_linhas" in _codigos(validar(_tabela(), cfg))


def test_modo_estrito_promove_avisos_a_erros(cfg):
    tabelas = _tabela(id_inscricao=["a"], status=["Reformulada"])
    assert all(p.bloqueia for p in validar(tabelas, cfg, estrito=True))


def test_referencia_orfa_avisa(contrato_real):
    inscricoes = pd.DataFrame(
        {
            "id_inscricao": ["RB-1"],
            "municipio": ["Salvador"],
            "organizacao": ["Org"],
            "territorio_identidade": ["T"],
            "status": ["Inscrita"],
            "data_inscricao": [pd.Timestamp("2026-01-01")],
        }
    )
    avaliacoes = pd.DataFrame(
        {
            "id_inscricao": ["RB-1", "RB-999"],
            "avaliador": ["AV-1", "AV-1"],
            "criterio": ["C1", "C1"],
            "nota": [8.0, 9.0],
        }
    )
    municipios = pd.DataFrame({"municipio": ["Salvador"], "territorio_identidade": ["T"]})
    problemas = validar(
        {"inscricoes": inscricoes, "avaliacoes": avaliacoes, "municipios": municipios},
        contrato_real,
    )
    orfa = next(p for p in problemas if p.codigo == "referencia_orfa")
    assert not orfa.bloqueia
    assert orfa.exemplos == ["RB-999"]
