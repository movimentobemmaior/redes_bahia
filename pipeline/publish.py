"""Camada 4 — publicação: gera a base estática que o painel consome.

Duas camadas de saída, com públicos diferentes:

- data/processed/  base completa (inclui colunas sensíveis). Uso interno.
- data/published/  base do painel: sem colunas sensíveis, + manifesto + histórico.
                   É o único diretório que a camada visual deve ler.

O manifesto (published/manifest.json) é o contrato de saída: o painel lê dele
a data da última atualização, as contagens e o resultado da validação — nunca
precisa abrir os dados para saber se pode confiar neles.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from .config import RAIZ, Config, caminho_curto
from .ingest import Arquivo
from .problemas import Problema, contar

DIR_PROCESSED = RAIZ / "data" / "processed"
DIR_PUBLISHED = RAIZ / "data" / "published"


def _serializavel(valor: Any) -> Any:
    if valor is None or valor is pd.NA or valor is pd.NaT:
        return None
    if isinstance(valor, pd.Timestamp | datetime):
        return valor.date().isoformat()
    if isinstance(valor, date):
        return valor.isoformat()
    if isinstance(valor, float | int | bool | str):
        return None if isinstance(valor, float) and pd.isna(valor) else valor
    return str(valor)


def _para_registros(df: pd.DataFrame) -> list[dict[str, Any]]:
    return [
        {col: _serializavel(valor) for col, valor in linha.items()}
        for linha in df.to_dict(orient="records")
    ]


def _escrever_csv(df: pd.DataFrame, destino: Path) -> None:
    df.to_csv(destino, index=False, encoding="utf-8", date_format="%Y-%m-%d")


def _escrever_parquet(df: pd.DataFrame, destino: Path) -> None:
    df.to_parquet(destino, index=False)


def _escrever_json(dados: Any, destino: Path) -> None:
    destino.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2, default=_serializavel) + "\n",
        encoding="utf-8",
    )


def _resumo_colunas(cfg: Config, nome: str, df: pd.DataFrame, publicaveis: list[str]) -> list[dict]:
    ds = cfg.datasets[nome]
    resumo = []
    for col in ds.colunas:
        serie = df[col.nome] if col.nome in df.columns else pd.Series(dtype="object")
        preenchidas = int(serie.notna().sum())
        resumo.append(
            {
                "nome": col.nome,
                "origem": col.origem,
                "tipo": col.tipo,
                "descricao": col.descricao,
                "obrigatorio": col.obrigatorio,
                "sensivel": col.sensivel,
                "exclui_quando": col.exclui_quando,
                "publicada": col.nome in publicaveis,
                "preenchimento": round(preenchidas / len(df), 4) if len(df) else 0.0,
                "valores_distintos": int(serie.nunique(dropna=True)),
            }
        )
    return resumo


def _atualizar_historico(
    cfg: Config, tabelas: dict[str, pd.DataFrame], data_execucao: date, fonte: str
) -> Path:
    """Acrescenta as contagens do dia ao histórico (formato longo).

    A planilha diária é uma foto do momento; o histórico é o que transforma
    essas fotos em série temporal. Reexecutar no mesmo dia substitui as linhas
    daquele dia em vez de duplicá-las.
    """
    linhas: list[dict[str, Any]] = []
    dia = data_execucao.isoformat()

    for nome, df in tabelas.items():
        linhas.append(
            {
                "data_execucao": dia,
                "arquivo_fonte": fonte,
                "dataset": nome,
                "agrupamento": "total",
                "categoria": "todos",
                "metrica": "n_linhas",
                "valor": len(df),
            }
        )
        for coluna in cfg.historico.agrupar_por:
            if coluna not in df.columns:
                continue
            contagem = df[coluna].astype("string").fillna("(vazio)").value_counts()
            for categoria, valor in contagem.items():
                linhas.append(
                    {
                        "data_execucao": dia,
                        "arquivo_fonte": fonte,
                        "dataset": nome,
                        "agrupamento": coluna,
                        "categoria": str(categoria),
                        "metrica": "n_linhas",
                        "valor": int(valor),
                    }
                )

    novo = pd.DataFrame(linhas)
    destino = cfg.historico.arquivo
    destino.parent.mkdir(parents=True, exist_ok=True)
    if destino.exists():
        antigo = pd.read_csv(destino, dtype={"data_execucao": "string"})
        antigo = antigo[antigo["data_execucao"] != dia]
        novo = pd.concat([antigo, novo], ignore_index=True)
    novo = novo.sort_values(["data_execucao", "dataset", "agrupamento", "categoria"])
    _escrever_csv(novo, destino)
    return destino


def _resumo_etapas(cfg: Config, tabelas: dict[str, pd.DataFrame]) -> list[dict[str, Any]]:
    """O funil do edital, do jeito que o painel precisa desenhar.

    Toda etapa entra, inclusive as que ainda não têm planilha: o funil só
    informa a decisão se mostrar para onde o processo ainda vai.
    """
    resumo = []
    for etapa in cfg.etapas:
        df = tabelas.get(etapa.dataset) if etapa.dataset else None
        if etapa.dataset is None:
            estado = "sem_contrato"
        elif df is None:
            estado = "aguardando"
        else:
            estado = "com_dados"
        resumo.append(
            {
                "chave": etapa.chave,
                "nome": etapa.nome,
                "resumo": etapa.resumo,
                "ordem": etapa.ordem,
                "dataset": etapa.dataset,
                "pasta": caminho_curto(etapa.pasta),
                "estado": estado,
                "n_linhas": len(df) if df is not None else None,
            }
        )
    return resumo


def publicar(
    tabelas: dict[str, pd.DataFrame],
    cfg: Config,
    fontes: dict[str, Arquivo],
    problemas: list[Problema],
    data_execucao: date,
    versao_pipeline: str,
) -> dict[str, Any]:
    """Grava as duas camadas de saída e devolve o manifesto."""
    DIR_PROCESSED.mkdir(parents=True, exist_ok=True)
    DIR_PUBLISHED.mkdir(parents=True, exist_ok=True)

    erros, avisos = contar(problemas)
    datasets_meta = []

    for nome, df in tabelas.items():
        ds = cfg.datasets[nome]
        _escrever_csv(df, DIR_PROCESSED / f"{nome}.csv")
        _escrever_parquet(df, DIR_PROCESSED / f"{nome}.parquet")

        publicaveis = [
            c.nome for c in ds.colunas if not (cfg.publicacao.remover_sensiveis and c.sensivel)
        ]
        publico = df[[c for c in publicaveis if c in df.columns]]
        limite = cfg.publicacao.limite_linhas_json
        recortado = publico.head(limite) if limite else publico

        if "csv" in cfg.publicacao.formatos:
            _escrever_csv(publico, DIR_PUBLISHED / f"{nome}.csv")
        if "parquet" in cfg.publicacao.formatos:
            _escrever_parquet(publico, DIR_PUBLISHED / f"{nome}.parquet")
        if "json" in cfg.publicacao.formatos:
            _escrever_json(_para_registros(recortado), DIR_PUBLISHED / f"{nome}.json")

        datasets_meta.append(
            {
                "nome": nome,
                "etapa": ds.etapa,
                "aba": ds.aba,
                "descricao": ds.descricao,
                "grao": list(ds.chave),
                "n_linhas": len(df),
                "n_colunas_publicadas": len(publico.columns),
                "colunas_omitidas_por_sigilo": [c for c in ds.nomes if c not in publicaveis],
                "colunas": _resumo_colunas(cfg, nome, df, publicaveis),
            }
        )

    principal = next(iter(fontes.values()), None)
    historico = _atualizar_historico(
        cfg, tabelas, data_execucao, principal.nome if principal else "(sem planilha)"
    )

    manifesto = {
        "painel": "Redes Bahia",
        "gerado_em": datetime.now().astimezone().isoformat(timespec="seconds"),
        "data_execucao": data_execucao.isoformat(),
        "versao_pipeline": versao_pipeline,
        "versao_contrato": cfg.versao,
        "edital": {
            "nome": cfg.edital.nome,
            "periodo_inscricoes": cfg.edital.periodo_inscricoes,
            "duracao_parceria": cfg.edital.duracao_parceria,
            "territorio": cfg.edital.territorio,
        },
        "etapas": _resumo_etapas(cfg, tabelas),
        "fontes": {
            nome: {
                "arquivo": a.nome,
                "hash_sha256": a.hash_sha256,
                "bytes": a.bytes,
            }
            for nome, a in fontes.items()
        },
        "validacao": {
            "status": "reprovado" if erros else ("com_avisos" if avisos else "aprovado"),
            "erros": erros,
            "avisos": avisos,
            "problemas": [p.como_dict() for p in problemas],
        },
        "datasets": datasets_meta,
        "arquivos": {
            "historico": caminho_curto(historico),
            # O manifesto entra na própria lista: ele ainda não existe em disco
            # neste ponto, mas é um arquivo publicado como os outros.
            "publicados": sorted(
                {caminho_curto(p) for p in DIR_PUBLISHED.iterdir() if p.is_file()}
                | {caminho_curto(DIR_PUBLISHED / "manifest.json")}
            ),
        },
    }
    _escrever_json(manifesto, DIR_PUBLISHED / "manifest.json")
    return manifesto
