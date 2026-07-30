"""Camada 1 — leitura crua do xlsm que foi colocado em data/raw/.

Nada é limpo aqui: a única responsabilidade é achar o arquivo do dia, abrir a
aba certa e devolver as células como vieram. Assim, quando algo estiver
estranho, dá para distinguir "veio errado da planilha" de "o pipeline quebrou".
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .config import Config, Dataset


class ErroFonte(Exception):
    """A planilha de origem não existe, não abre, ou não tem a aba esperada."""


@dataclass(frozen=True)
class Arquivo:
    caminho: Path
    hash_sha256: str
    bytes: int

    @property
    def nome(self) -> str:
        return self.caminho.name


def _hash_arquivo(caminho: Path) -> str:
    h = hashlib.sha256()
    with caminho.open("rb") as f:
        for bloco in iter(lambda: f.read(1024 * 1024), b""):
            h.update(bloco)
    return h.hexdigest()


def localizar(cfg: Config, diretorio: Path | None = None) -> list[Arquivo]:
    """Lista as planilhas de uma pasta, conforme fonte.selecao do contrato.

    A ordenação é por nome, e não por data de modificação: o nome
    (AAAA-MM-DD_...) é estável ao clonar o repositório, o mtime não.
    """
    diretorio = diretorio or cfg.fonte.diretorio
    if not diretorio.exists():
        raise ErroFonte(
            f"Pasta de origem não existe: {diretorio}\n"
            "Crie a pasta e coloque nela a planilha do dia."
        )
    encontrados = sorted(p for p in diretorio.glob(cfg.fonte.padrao_arquivo) if p.is_file())
    if not encontrados:
        raise ErroFonte(
            f"Nenhum arquivo '{cfg.fonte.padrao_arquivo}' em {diretorio}.\n"
            "Coloque a planilha do dia lá, com nome no formato "
            "AAAA-MM-DD_<etapa>.xlsx, e rode de novo."
        )
    if cfg.fonte.selecao == "mais_recente":
        encontrados = encontrados[-1:]
    return [Arquivo(p, _hash_arquivo(p), p.stat().st_size) for p in encontrados]


def localizar_por_etapa(cfg: Config) -> dict[str, Arquivo]:
    """Planilha mais recente de cada etapa que já tem dataset e arquivo.

    Etapa sem planilha não é erro: o edital anda por fases, e as últimas ficam
    vazias por meses. O painel precisa mostrar o funil inteiro desde o começo,
    então quem trata a ausência é a camada de publicação, não uma exceção aqui.
    """
    achados: dict[str, Arquivo] = {}
    for etapa in cfg.etapas:
        if not etapa.dataset:
            continue
        try:
            achados[etapa.dataset] = localizar(cfg, etapa.pasta)[-1]
        except ErroFonte:
            continue
    return achados


def abas_disponiveis(caminho: Path) -> list[str]:
    try:
        return pd.ExcelFile(caminho, engine="openpyxl").sheet_names
    except Exception as exc:  # arquivo corrompido, protegido por senha, etc.
        raise ErroFonte(f"Não foi possível abrir {caminho.name}: {exc}") from exc


def ler_aba(caminho: Path, ds: Dataset) -> pd.DataFrame:
    """Lê a aba de um dataset como texto/valores crus, sem inferência de tipo."""
    disponiveis = abas_disponiveis(caminho)
    if ds.aba not in disponiveis:
        raise ErroFonte(
            f"A aba '{ds.aba}' (dataset '{ds.nome}') não existe em {caminho.name}.\n"
            f"Abas encontradas: {', '.join(disponiveis)}.\n"
            "Ajuste 'aba' em config/fontes.yml ou renomeie a aba na planilha."
        )
    df = pd.read_excel(
        caminho,
        sheet_name=ds.aba,
        header=ds.linha_cabecalho - 1,
        engine="openpyxl",
        dtype=object,
    )
    df = df.dropna(axis=0, how="all")
    df.columns = [str(c).strip() for c in df.columns]

    # Descarta só as colunas-fantasma do Excel: sem nome E sem conteúdo.
    # Coluna COM nome e sem dado é coluna vazia, não coluna ausente — e a
    # diferença decide a publicação do dia: 'ausente' é erro e bloqueia,
    # 'vazia' apenas fica nula. Um campo do formulário que ninguém preencheu
    # ainda não pode derrubar o painel.
    fantasmas = [c for c in df.columns if c.startswith("Unnamed:") and df[c].isna().all()]
    return df.drop(columns=fantasmas).reset_index(drop=True)
