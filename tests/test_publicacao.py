"""Montagem do site e a trava que impede vazamento na hospedagem.

O teste que mais importa aqui é o que **planta um vazamento de propósito** e
exige que a trava falhe. Uma trava que nunca foi vista falhando não é trava.
"""

from __future__ import annotations

import importlib.util
import json

import pytest
import yaml

from pipeline.config import RAIZ


def _carregar(nome: str):
    spec = importlib.util.spec_from_file_location(nome, RAIZ / "scripts" / f"{nome}.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


montar_site = _carregar("montar_site")
checar_publicacao = _carregar("checar_publicacao")
Vazamento = checar_publicacao.Vazamento

CONTRATO = RAIZ / "config" / "fontes.yml"


@pytest.fixture
def repo(tmp_path):
    """Repositório de mentira com o mínimo que a montagem espera encontrar."""
    (tmp_path / "dashboard" / "assets").mkdir(parents=True)
    (tmp_path / "dashboard" / "index.html").write_text("<h1>painel</h1>", encoding="utf-8")
    (tmp_path / "dashboard" / "assets" / "painel.css").write_text("body{}", encoding="utf-8")
    (tmp_path / "dashboard" / "README.md").write_text("doc interna", encoding="utf-8")

    (tmp_path / "design" / "tokens").mkdir(parents=True)
    (tmp_path / "design" / "tokens" / "tokens.css").write_text(":root{}", encoding="utf-8")

    publicados = tmp_path / "data" / "published"
    publicados.mkdir(parents=True)
    (publicados / "credenciamento.csv").write_text(
        "id,organizacao,status_credenciamento\n110167,Org,Aprovado automaticamente\n",
        encoding="utf-8",
    )
    (publicados / "credenciamento.json").write_text(
        json.dumps(
            [{"id": "110167", "organizacao": "Org", "status_credenciamento": "Aprovado"}]
        ),
        encoding="utf-8",
    )
    (publicados / "manifest.json").write_text(
        json.dumps(
            {
                "datasets": [
                    {
                        "nome": "credenciamento",
                        "colunas_omitidas_por_sigilo": [
                            "respondente_nome",
                            "respondente_email",
                        ],
                        "colunas": [
                            {"nome": "id", "publicada": True},
                            {"nome": "respondente_nome", "publicada": False},
                            {"nome": "respondente_email", "publicada": False},
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    # O que NÃO pode sair daqui de jeito nenhum.
    (tmp_path / "data" / "raw").mkdir(parents=True)
    (tmp_path / "data" / "raw" / "2026-08-01_redes_bahia.xlsx").write_bytes(b"planilha")
    (tmp_path / "data" / "processed").mkdir(parents=True)
    (tmp_path / "data" / "processed" / "credenciamento.csv").write_text(
        "id,respondente_nome,respondente_email\n110167,Fulana,a@b.org\n", encoding="utf-8"
    )
    return tmp_path


@pytest.fixture
def site(repo, tmp_path):
    destino = tmp_path / "_site"
    montar_site.montar(destino, raiz=repo)
    return destino


# --- Montagem -----------------------------------------------------------------


def test_monta_apenas_o_que_esta_na_lista(site):
    assert (site / "dashboard" / "index.html").exists()
    assert (site / "dashboard" / "assets" / "painel.css").exists()
    assert (site / "design" / "tokens" / "tokens.css").exists()
    assert (site / "data" / "published" / "credenciamento.csv").exists()
    assert (site / "index.html").exists(), "falta o redirecionador na raiz"


def test_planilha_e_base_interna_ficam_de_fora(site):
    caminhos = {p.relative_to(site).as_posix() for p in site.rglob("*") if p.is_file()}
    assert not any("raw" in c for c in caminhos)
    assert not any("processed" in c for c in caminhos)
    assert not any(c.endswith((".xlsm", ".xlsx")) for c in caminhos)


def test_documentacao_interna_nao_vai_para_o_site(site):
    assert not (site / "dashboard" / "README.md").exists()


def test_remontar_limpa_o_destino_antes(repo, tmp_path):
    destino = tmp_path / "_site"
    montar_site.montar(destino, raiz=repo)
    (destino / "sobra.txt").write_text("de uma montagem anterior", encoding="utf-8")
    montar_site.montar(destino, raiz=repo)
    assert not (destino / "sobra.txt").exists()


# --- Trava --------------------------------------------------------------------


def test_pacote_limpo_e_aprovado(site):
    resumo = checar_publicacao.checar(site, CONTRATO)
    assert "conferido" in resumo


def test_csv_com_coluna_sigilosa_bloqueia(site):
    (site / "data" / "published" / "credenciamento.csv").write_text(
        "id,respondente_email\n110167,a@b.org\n", encoding="utf-8"
    )
    with pytest.raises(Vazamento, match="respondente_email"):
        checar_publicacao.checar(site, CONTRATO)


def test_json_com_coluna_sigilosa_bloqueia(site):
    (site / "data" / "published" / "credenciamento.json").write_text(
        json.dumps([{"id": "110167", "respondente_nome": "Fulana"}]), encoding="utf-8"
    )
    with pytest.raises(Vazamento, match="respondente_nome"):
        checar_publicacao.checar(site, CONTRATO)


def test_arquivo_com_nome_desconhecido_bloqueia(site):
    """Regressão: a primeira versão da trava só conferia arquivos cujo nome
    batia com um dataset do contrato. Uma cópia manual com outro nome — que é
    o vazamento mais provável na prática — passava sem nenhuma conferência."""
    (site / "data" / "published" / "backup_planilha.csv").write_text(
        "id,respondente_nome,respondente_email\n110167,Fulana,a@b.org\n", encoding="utf-8"
    )
    with pytest.raises(Vazamento, match="inesperado"):
        checar_publicacao.checar(site, CONTRATO)


def test_coluna_sigilosa_de_outro_dataset_tambem_bloqueia(site):
    """A conferência é contra a união das colunas sigilosas, não as do dataset."""
    (site / "data" / "published" / "historico.csv").write_text(
        "data_execucao,respondente_email\n2026-08-01,a@b.org\n", encoding="utf-8"
    )
    with pytest.raises(Vazamento, match="respondente_email"):
        checar_publicacao.checar(site, CONTRATO)


def test_historico_e_manifesto_sao_aceitos(site):
    (site / "data" / "published" / "historico.csv").write_text(
        "data_execucao,dataset,valor\n2026-08-01,inscricoes,120\n", encoding="utf-8"
    )
    assert checar_publicacao.checar(site, CONTRATO)


def test_planilha_no_pacote_bloqueia(site):
    (site / "data" / "published" / "vazou.xlsm").write_bytes(b"x")
    with pytest.raises(Vazamento, match="planilha"):
        checar_publicacao.checar(site, CONTRATO)


def test_arquivo_da_base_interna_bloqueia(site):
    interna = site / "data" / "processed"
    interna.mkdir(parents=True)
    (interna / "inscricoes.csv").write_text("id_inscricao,cnpj\n", encoding="utf-8")
    with pytest.raises(Vazamento, match="processed"):
        checar_publicacao.checar(site, CONTRATO)


def test_manifesto_que_declara_sigiloso_como_publicado_bloqueia(site):
    caminho = site / "data" / "published" / "manifest.json"
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    dados["datasets"][0]["colunas"][1]["publicada"] = True
    caminho.write_text(json.dumps(dados), encoding="utf-8")
    with pytest.raises(Vazamento, match="respondente_nome"):
        checar_publicacao.checar(site, CONTRATO)


def test_site_inexistente_bloqueia(tmp_path):
    with pytest.raises(Vazamento, match="não encontrado"):
        checar_publicacao.checar(tmp_path / "nao_existe", CONTRATO)


def test_trava_le_o_contrato_de_verdade():
    """Se alguém tirar a marcação `sensivel` do contrato, a trava perde o alvo."""
    sensiveis = checar_publicacao.sensiveis_por_dataset(CONTRATO)
    assert sensiveis["credenciamento"] == {"respondente_nome", "respondente_email"}


def test_contrato_e_montagem_concordam_sobre_o_que_e_publicado():
    """A lista de permissão nunca pode incluir data/raw ou data/processed."""
    origens = {origem for origem, _ in montar_site.CONTEUDO}
    assert not any(o.startswith(("data/raw", "data/processed")) for o in origens)
    assert yaml.safe_load(CONTRATO.read_text(encoding="utf-8"))["datasets"]
