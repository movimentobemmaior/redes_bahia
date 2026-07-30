"""Leitura da planilha: o que é resíduo do Excel e o que é dado de verdade.

Os dois testes de coluna vazia vieram de um defeito real, encontrado na
primeira planilha de produção (30/07/2026): a coluna `Edital` existia no
formulário mas estava sem nenhuma resposta, e o pipeline a tratava como
inexistente. No perfil ela sumia em silêncio; na leitura viraria
`coluna_ausente`, que é erro e bloquearia a publicação todo dia.
"""

from __future__ import annotations

import pandas as pd
import pytest
from openpyxl import Workbook

from pipeline import profiling
from pipeline.ingest import ErroFonte, ler_aba
from pipeline.transform import padronizar


@pytest.fixture
def planilha(tmp_path):
    """Planilha com uma coluna preenchida, uma vazia-com-nome e uma fantasma."""

    def criar(aba="Dados", linhas=(("110167", "Org A", None), ("110218", "Org B", None))):
        wb = Workbook()
        ws = wb.active
        ws.title = aba
        ws.append(["ID", "Respondente", "Edital", None])
        for linha in linhas:
            ws.append([*linha, None])
        caminho = tmp_path / "planilha.xlsx"
        wb.save(caminho)
        return caminho

    return criar


class _Ds:
    """Dataset mínimo, só com o que ler_aba consulta."""

    def __init__(self, aba="Dados"):
        self.nome = "credenciamento"
        self.aba = aba
        self.linha_cabecalho = 1


def test_coluna_com_nome_e_sem_dado_e_mantida(planilha):
    df = ler_aba(planilha(), _Ds())
    assert "Edital" in df.columns, "coluna vazia com nome não pode sumir da leitura"
    assert df["Edital"].isna().all()


def test_coluna_fantasma_do_excel_e_descartada(planilha):
    df = ler_aba(planilha(), _Ds())
    assert not any(str(c).startswith("Unnamed:") for c in df.columns)


def test_coluna_vazia_declarada_nao_bloqueia_a_publicacao(planilha, contrato, cfg):
    """Coluna vazia é coluna nula, não coluna ausente — a diferença é erro x nada."""
    from pipeline.config import Coluna, Dataset

    ds = Dataset(
        nome="credenciamento",
        aba="Dados",
        descricao="",
        linha_cabecalho=1,
        chave=("id",),
        colunas=(
            Coluna(nome="id", origem="ID", tipo="texto", obrigatorio=True),
            Coluna(nome="edital", origem="Edital", tipo="texto"),
        ),
        regras=(),
    )
    resultado = padronizar(ler_aba(planilha(), ds), ds)
    assert not [p for p in resultado.problemas if p.codigo == "coluna_ausente"]
    assert resultado.df["edital"].isna().all()


def test_perfil_mostra_coluna_vazia_com_zero_por_cento(planilha):
    perfis = profiling.perfilar_arquivo(planilha())
    colunas = {c.original: c for c in perfis[0].colunas}
    assert "Edital" in colunas, "o perfil precisa revelar a coluna vazia, não escondê-la"
    assert colunas["Edital"].preenchimento == 0.0
    assert colunas["Respondente"].preenchimento == 1.0


def test_aba_inexistente_lista_as_disponiveis(planilha):
    with pytest.raises(ErroFonte, match="Dados"):
        ler_aba(planilha(), _Ds(aba="Outra"))


def test_linhas_totalmente_vazias_sao_descartadas(planilha):
    df = ler_aba(planilha(linhas=(("110167", "Org A", None), (None, None, None))), _Ds())
    assert len(df) == 1


def test_data_com_as_horas(cfg):
    """Formulários brasileiros exportam "29/07/2026 às 12:16"."""
    from pipeline.config import Coluna
    from pipeline.transform import _converter

    coluna = Coluna(nome="data_resposta", origem="Data da Resposta", tipo="data")
    serie = _converter(pd.Series(["29/07/2026 às 12:16", "30/07/2026 às 08:05"]), coluna)
    assert serie.dt.date.astype(str).tolist() == ["2026-07-29", "2026-07-30"]
