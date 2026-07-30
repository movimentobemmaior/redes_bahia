#!/usr/bin/env python3
"""Trava de segurança: confere o pacote do site antes de ele ser hospedado.

`montar_site.py` decide o que entra; este script confere o que entrou. São
duas camadas de propósito — a primeira pode errar por engano de configuração,
a segunda erra apenas se o próprio contrato estiver errado.

O que é verificado:

1. nenhuma planilha (.xlsm/.xlsx/.xls) no pacote;
2. nenhum arquivo vindo de data/raw/ ou data/processed/;
3. nenhuma coluna marcada como `sensivel: true` presente nos dados publicados;
4. o manifesto confirma que toda coluna sigilosa ficou de fora.

Sai com código 1 e mensagem específica na primeira falha encontrada.

Uso:  python scripts/checar_publicacao.py [--site _site]
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[1]
EXTENSOES_DE_PLANILHA = {".xlsm", ".xlsx", ".xls", ".xlsb", ".csvz"}
PASTAS_PROIBIDAS = ("data/raw", "data/processed")


class Vazamento(Exception):
    """Algo que não podia sair do repositório está no pacote do site."""


def sensiveis_por_dataset(contrato: Path) -> dict[str, set[str]]:
    dados = yaml.safe_load(contrato.read_text(encoding="utf-8")) or {}
    return {
        nome: {
            coluna
            for coluna, spec in (ds.get("colunas") or {}).items()
            if isinstance(spec, dict) and spec.get("sensivel")
        }
        for nome, ds in (dados.get("datasets") or {}).items()
    }


def _checar_extensoes(site: Path) -> None:
    achados = [
        p for p in site.rglob("*") if p.is_file() and p.suffix.lower() in EXTENSOES_DE_PLANILHA
    ]
    if achados:
        nomes = ", ".join(str(p.relative_to(site)) for p in achados[:5])
        raise Vazamento(f"planilha(s) dentro do pacote do site: {nomes}")


def _checar_pastas(site: Path) -> None:
    for p in site.rglob("*"):
        if not p.is_file():
            continue
        relativo = p.relative_to(site).as_posix()
        for proibida in PASTAS_PROIBIDAS:
            if relativo.startswith(proibida) or f"/{proibida}/" in f"/{relativo}":
                raise Vazamento(f"arquivo vindo de {proibida}/ no pacote: {relativo}")


def _colunas_do_csv(caminho: Path) -> set[str]:
    with caminho.open(encoding="utf-8", newline="") as f:
        cabecalho = next(csv.reader(f), [])
    return {c.strip() for c in cabecalho}


def _colunas_do_json(caminho: Path) -> set[str]:
    conteudo = json.loads(caminho.read_text(encoding="utf-8"))
    if isinstance(conteudo, list) and conteudo and isinstance(conteudo[0], dict):
        return set(conteudo[0])
    return set()


def _checar_dados(site: Path, sensiveis: dict[str, set[str]]) -> int:
    """Confere as colunas de cada arquivo de dados publicado.

    A comparação é contra a união das colunas sigilosas de TODOS os datasets,
    e não contra as do dataset de mesmo nome. A diferença importa: um arquivo
    com nome inesperado (uma cópia manual, um resto de teste) não tem dataset
    correspondente e escaparia inteiro da conferência.
    """
    publicados = site / "data" / "published"
    if not publicados.exists():
        return 0

    # Toda coluna sigilosa de qualquer dataset, em qualquer arquivo.
    proibidas = set().union(*sensiveis.values()) if sensiveis else set()
    conhecidos = set(sensiveis) | {"manifest", "historico"}

    verificados = 0
    for caminho in sorted(publicados.iterdir()):
        if not caminho.is_file() or caminho.name == "manifest.json":
            continue
        if caminho.stem not in conhecidos:
            raise Vazamento(
                f"arquivo inesperado na camada publicada: {caminho.name}. "
                "Só devem existir ali os datasets do contrato, o histórico e o manifesto — "
                "um arquivo fora dessa lista não passou por nenhuma remoção de sigilo"
            )
        if caminho.suffix == ".csv":
            colunas = _colunas_do_csv(caminho)
        elif caminho.suffix == ".json":
            colunas = _colunas_do_json(caminho)
        else:
            continue  # .parquet é conferido pelo manifesto, não abrimos binário aqui

        vazadas = colunas & proibidas
        if vazadas:
            raise Vazamento(
                f"{caminho.name} publica coluna(s) sigilosa(s): {', '.join(sorted(vazadas))}"
            )
        verificados += 1
    return verificados


def _checar_manifesto(site: Path, sensiveis: dict[str, set[str]]) -> None:
    manifesto = site / "data" / "published" / "manifest.json"
    if not manifesto.exists():
        return
    dados = json.loads(manifesto.read_text(encoding="utf-8"))
    for ds in dados.get("datasets", []):
        proibidas = sensiveis.get(ds["nome"], set())
        publicadas = {c["nome"] for c in ds.get("colunas", []) if c.get("publicada")}
        vazadas = publicadas & proibidas
        if vazadas:
            raise Vazamento(
                f"o manifesto declara como publicada(s) a(s) coluna(s) sigilosa(s) "
                f"{', '.join(sorted(vazadas))} em '{ds['nome']}'"
            )
        omitidas = set(ds.get("colunas_omitidas_por_sigilo", []))
        if proibidas - omitidas:
            raise Vazamento(
                f"o manifesto de '{ds['nome']}' não registra "
                f"{', '.join(sorted(proibidas - omitidas))} como retida(s) por sigilo"
            )


def checar(site: Path, contrato: Path) -> str:
    if not site.exists():
        raise Vazamento(f"pacote do site não encontrado em {site} — rode montar_site.py antes")

    sensiveis = sensiveis_por_dataset(contrato)
    _checar_extensoes(site)
    _checar_pastas(site)
    verificados = _checar_dados(site, sensiveis)
    _checar_manifesto(site, sensiveis)

    total = sum(len(v) for v in sensiveis.values())
    return (
        f"{len(list(site.rglob('*')))} item(ns) no pacote · "
        f"{verificados} arquivo(s) de dados conferido(s) · "
        f"{total} coluna(s) sigilosa(s) do contrato ausente(s), como esperado"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, default=RAIZ / "_site")
    parser.add_argument("--contrato", type=Path, default=RAIZ / "config" / "fontes.yml")
    args = parser.parse_args()

    try:
        resumo = checar(args.site, args.contrato)
    except Vazamento as exc:
        print(f"\n[PUBLICAÇÃO BLOQUEADA] {exc}\n", file=sys.stderr)
        print(
            "Nada deve ser hospedado enquanto isso não for corrigido.\n"
            "Confira config/fontes.yml (marcação `sensivel`) e a lista CONTEUDO\n"
            "em scripts/montar_site.py.",
            file=sys.stderr,
        )
        return 1

    print(f"Pacote aprovado para hospedagem.\n  {resumo}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
