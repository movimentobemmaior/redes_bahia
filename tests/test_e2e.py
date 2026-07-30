"""Teste de ponta a ponta: planilha .xlsx -> base publicada.

É o teste que garante a promessa do piloto — alguém solta o arquivo do dia na
pasta e um comando produz a base do painel.
"""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest
import yaml

from pipeline import cli, profiling, publish
from pipeline.config import RAIZ

CONTRATO_REAL = yaml.safe_load((RAIZ / "config" / "fontes.yml").read_text(encoding="utf-8"))


def _gerar_exemplo(destino: Path, linhas: int = 30) -> Path:
    spec = importlib.util.spec_from_file_location(
        "gerar_exemplo", RAIZ / "scripts" / "gerar_exemplo.py"
    )
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo.gerar(linhas, destino)


@pytest.fixture
def ambiente(tmp_path, monkeypatch):
    """Repositório de mentira: planilha, contrato e saídas todos em tmp_path."""
    entrada = tmp_path / "raw"
    _gerar_exemplo(entrada / "exemplo_2026-05-01_redes_bahia.xlsx")

    contrato = copy.deepcopy(CONTRATO_REAL)
    contrato["fonte"]["diretorio"] = str(entrada)
    contrato["historico"]["arquivo"] = str(tmp_path / "published" / "historico.csv")
    caminho = tmp_path / "fontes.yml"
    caminho.write_text(yaml.safe_dump(contrato, allow_unicode=True), encoding="utf-8")

    monkeypatch.setattr(publish, "DIR_PROCESSED", tmp_path / "processed")
    monkeypatch.setattr(publish, "DIR_PUBLISHED", tmp_path / "published")
    monkeypatch.setattr(profiling, "DIR_RELATORIOS", tmp_path / "reports")
    monkeypatch.setattr(cli, "DIR_RELATORIOS", tmp_path / "reports")
    return tmp_path, caminho


def test_fluxo_completo_publica_a_base(ambiente):
    tmp_path, contrato = ambiente
    assert cli.main(["--config", str(contrato), "dados", "--data", "2026-05-01"]) == 0

    publicado = tmp_path / "published"
    for esperado in ("credenciamento.csv", "credenciamento.json", "manifest.json", "historico.csv"):
        assert (publicado / esperado).exists(), f"faltou publicar {esperado}"

    manifesto = json.loads((publicado / "manifest.json").read_text(encoding="utf-8"))
    assert manifesto["data_execucao"] == "2026-05-01"
    assert {d["nome"] for d in manifesto["datasets"]} == {"credenciamento"}
    assert manifesto["validacao"]["erros"] == 0


def test_validar_nao_escreve_nada(ambiente):
    tmp_path, contrato = ambiente
    assert cli.main(["--config", str(contrato), "validar"]) == 0
    assert not (tmp_path / "published").exists()


def test_planilha_ausente_falha_com_codigo_2(tmp_path, ambiente, capsys):
    _, contrato = ambiente
    dados = yaml.safe_load(contrato.read_text(encoding="utf-8"))
    dados["fonte"]["diretorio"] = str(tmp_path / "vazio")
    (tmp_path / "vazio").mkdir(exist_ok=True)
    contrato.write_text(yaml.safe_dump(dados, allow_unicode=True), encoding="utf-8")

    assert cli.main(["--config", str(contrato), "dados"]) == 2
    assert "Nenhum arquivo" in capsys.readouterr().err


def test_erro_de_estrutura_bloqueia_publicacao(ambiente, monkeypatch):
    """Se uma coluna obrigatória sumir da planilha, nada é publicado."""
    tmp_path, contrato = ambiente
    dados = yaml.safe_load(contrato.read_text(encoding="utf-8"))
    dados["datasets"]["credenciamento"]["colunas"]["organizacao"]["origem"] = "Razão Social"
    contrato.write_text(yaml.safe_dump(dados, allow_unicode=True), encoding="utf-8")

    assert cli.main(["--config", str(contrato), "dados"]) == 1
    assert not (tmp_path / "published" / "manifest.json").exists()


def test_perfil_gera_relatorio_e_rascunho(ambiente):
    tmp_path, contrato = ambiente
    assert cli.main(["--config", str(contrato), "perfil"]) == 0
    rascunho = tmp_path / "reports" / "rascunho_fontes.yml"
    assert rascunho.exists()
    proposto = yaml.safe_load(rascunho.read_text(encoding="utf-8"))
    assert set(proposto["datasets"]) == {"credenciamento_redes_bahia"}
