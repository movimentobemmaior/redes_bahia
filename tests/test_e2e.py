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

from pipeline import cli, dicionario, profiling, publish
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
    """Repositório de mentira: planilhas, contrato e saídas todos em tmp_path.

    Cada etapa aponta para uma pasta dentro de tmp_path. Redirecionar apenas
    `fonte.diretorio` não basta desde que a fonte passou a vir da etapa: o teste
    acabaria lendo `data/raw/` do repositório de verdade e passando por engano.
    """
    contrato = copy.deepcopy(CONTRATO_REAL)
    for etapa in contrato["etapas"]:
        pasta = tmp_path / "raw" / etapa["chave"]
        pasta.mkdir(parents=True, exist_ok=True)
        etapa["pasta"] = str(pasta)
        if etapa["dataset"]:
            _gerar_exemplo(pasta / f"exemplo_2026-05-01_{etapa['chave']}.xlsx")

    contrato["fonte"]["diretorio"] = str(tmp_path / "raw")
    contrato["historico"]["arquivo"] = str(tmp_path / "published" / "historico.csv")
    caminho = tmp_path / "fontes.yml"
    caminho.write_text(
        yaml.safe_dump(contrato, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )

    monkeypatch.setattr(publish, "DIR_PROCESSED", tmp_path / "processed")
    monkeypatch.setattr(publish, "DIR_PUBLISHED", tmp_path / "published")
    monkeypatch.setattr(profiling, "DIR_RELATORIOS", tmp_path / "reports")
    monkeypatch.setattr(cli, "DIR_RELATORIOS", tmp_path / "reports")
    # Sem isto, `pipeline dados` reescreve docs/03-dicionario-de-dados.md do
    # próprio repositório durante os testes — a suíte suja o projeto.
    monkeypatch.setattr(dicionario, "DESTINO", tmp_path / "dicionario.md")
    return tmp_path, caminho


def test_fluxo_completo_publica_a_base(ambiente):
    tmp_path, contrato = ambiente
    assert cli.main(["--config", str(contrato), "dados", "--data", "2026-05-01"]) == 0

    publicado = tmp_path / "published"
    for esperado in ("credenciamento.csv", "credenciamento.json", "manifest.json", "historico.csv"):
        assert (publicado / esperado).exists(), f"faltou publicar {esperado}"

    assert (tmp_path / "dicionario.md").exists(), "o dicionário precisa sair no destino isolado"
    manifesto = json.loads((publicado / "manifest.json").read_text(encoding="utf-8"))
    assert manifesto["data_execucao"] == "2026-05-01"
    assert {d["nome"] for d in manifesto["datasets"]} == {"credenciamento"}
    assert manifesto["validacao"]["erros"] == 0


def test_validar_nao_escreve_nada(ambiente):
    tmp_path, contrato = ambiente
    assert cli.main(["--config", str(contrato), "validar"]) == 0
    assert not (tmp_path / "published").exists()


def test_nenhuma_etapa_com_planilha_falha_com_codigo_2(tmp_path, ambiente, capsys):
    """Sem planilha em etapa nenhuma não há o que publicar — e isso precisa ser
    dito, não virar uma publicação vazia."""
    _, contrato = ambiente
    dados = yaml.safe_load(contrato.read_text(encoding="utf-8"))
    vazio = tmp_path / "vazio"
    vazio.mkdir(exist_ok=True)
    for etapa in dados["etapas"]:
        etapa["pasta"] = str(vazio)
    contrato.write_text(
        yaml.safe_dump(dados, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )

    assert cli.main(["--config", str(contrato), "dados"]) == 2
    assert "Nenhuma etapa" in capsys.readouterr().err


def test_etapa_sem_planilha_nao_impede_as_outras(ambiente):
    """O edital anda por fases: as etapas finais ficam vazias por meses, e isso
    não pode impedir a publicação das que já têm dado."""
    tmp_path, contrato = ambiente
    assert cli.main(["--config", str(contrato), "dados", "--data", "2026-05-01"]) == 0

    manifesto = json.loads(
        (tmp_path / "published" / "manifest.json").read_text(encoding="utf-8")
    )
    estados = {e["chave"]: e["estado"] for e in manifesto["etapas"]}
    assert estados["cadastramento"] == "com_dados"
    assert set(estados.values()) - {"com_dados"}, "as demais etapas precisam aparecer no funil"
    assert len(manifesto["etapas"]) == 5


def test_gerador_de_exemplo_escreve_onde_o_pipeline_procura():
    """Regressão: o gerador escrevia em data/raw/ enquanto a fonte passou a vir
    de data/raw/<etapa>/. O CI gerava o exemplo e o pipeline não achava nada,
    saindo com código 2. Gerador e pipeline têm de concordar sobre o caminho,
    e os dois tiram essa informação do contrato."""
    spec = importlib.util.spec_from_file_location(
        "gerar_exemplo", RAIZ / "scripts" / "gerar_exemplo.py"
    )
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)

    from pipeline.config import carregar

    cfg = carregar()
    destino = modulo.destino_padrao()
    pastas = {e.pasta for e in cfg.etapas if e.dataset}
    assert destino.parent in pastas, (
        f"o exemplo cairia em {destino.parent}, que não é pasta de nenhuma etapa com dataset"
    )
    assert destino.match(cfg.fonte.padrao_arquivo), "o nome não casa com fonte.padrao_arquivo"


def test_erro_de_estrutura_bloqueia_publicacao(ambiente, monkeypatch):
    """Se uma coluna obrigatória sumir da planilha, nada é publicado."""
    tmp_path, contrato = ambiente
    dados = yaml.safe_load(contrato.read_text(encoding="utf-8"))
    dados["datasets"]["credenciamento"]["colunas"]["organizacao"]["origem"] = "Razão Social"
    contrato.write_text(
        yaml.safe_dump(dados, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )

    assert cli.main(["--config", str(contrato), "dados"]) == 1
    assert not (tmp_path / "published" / "manifest.json").exists()


def test_perfil_gera_relatorio_e_rascunho(ambiente):
    tmp_path, contrato = ambiente
    assert cli.main(["--config", str(contrato), "perfil"]) == 0
    rascunho = tmp_path / "reports" / "rascunho_fontes.yml"
    assert rascunho.exists()
    proposto = yaml.safe_load(rascunho.read_text(encoding="utf-8"))
    assert set(proposto["datasets"]) == {"credenciamento_redes_bahia"}
