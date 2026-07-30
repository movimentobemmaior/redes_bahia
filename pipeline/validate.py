"""Camada 3 — validação contra o contrato.

Regra de ouro do piloto: **o painel não pode publicar dado que ele mesmo sabe
que está quebrado, mas também não pode travar por causa de uma célula estranha.**
Por isso há dois níveis:

- erro  -> quebra de estrutura (coluna que sumiu, chave duplicada, aba vazia).
           Bloqueia a publicação: o painel continua com os dados de ontem.
- aviso -> quebra de conteúdo (valor fora do intervalo, categoria nova).
           Publica, mas fica registrado no manifesto e visível no painel.

`--estrito` promove avisos a erros, para uso em revisão de dados.
"""

from __future__ import annotations

import pandas as pd

from .config import Config, Dataset
from .problemas import AVISO, ERRO, Problema


def _rotulos(df: pd.DataFrame, ds: Dataset, mascara: pd.Series, limite: int = 5) -> list[str]:
    """Identifica as linhas afetadas pela chave do dataset (ou pela posição).

    Devolver o id da inscrição é muito mais útil que devolver "linha 417": quem
    vai corrigir procura na planilha pelo identificador, não pela posição.
    """
    chave = [c for c in ds.chave if c in df.columns]
    if chave:
        alvo = df.loc[mascara, chave].head(limite)
        return [
            " | ".join("(vazio)" if pd.isna(v) else str(v) for v in linha)
            for linha in alvo.to_numpy()
        ]
    return [f"linha {i + 1}" for i in df.index[mascara][:limite]]


def _obrigatorias(df: pd.DataFrame, ds: Dataset) -> list[Problema]:
    achados = []
    for col in ds.colunas:
        if not col.obrigatorio or col.nome not in df.columns:
            continue
        vazias = df[col.nome].isna()
        if vazias.any():
            achados.append(
                Problema(
                    dataset=ds.nome,
                    codigo="obrigatorio_vazio",
                    gravidade=ERRO,
                    coluna=col.nome,
                    mensagem="coluna obrigatória com valor vazio",
                    linhas_afetadas=int(vazias.sum()),
                    exemplos=_rotulos(df, ds, vazias),
                )
            )
    return achados


def _regra_unico(df: pd.DataFrame, ds: Dataset, regra: dict) -> list[Problema]:
    colunas = [c for c in regra.get("colunas", []) if c in df.columns]
    if not colunas:
        return []
    duplicadas = df.duplicated(subset=colunas, keep=False) & df[colunas].notna().all(axis=1)
    if not duplicadas.any():
        return []
    return [
        Problema(
            dataset=ds.nome,
            codigo="chave_duplicada",
            gravidade=ERRO,
            coluna=", ".join(colunas),
            mensagem=f"há linhas repetidas para a chave ({', '.join(colunas)})",
            linhas_afetadas=int(duplicadas.sum()),
            exemplos=_rotulos(df, ds, duplicadas),
        )
    ]


def _regra_valores(df: pd.DataFrame, ds: Dataset, regra: dict) -> list[Problema]:
    coluna = regra["coluna"]
    if coluna not in df.columns:
        return []
    permitidos = {str(v) for v in regra["valores"]}
    serie = df[coluna].astype("string")
    fora = serie.notna() & ~serie.isin(permitidos)
    if not fora.any():
        return []
    novos = sorted({str(v) for v in serie[fora].unique()})
    return [
        Problema(
            dataset=ds.nome,
            codigo="valor_nao_previsto",
            gravidade=AVISO,
            coluna=coluna,
            mensagem=(
                "valores que não constam na lista prevista no contrato. "
                "Se são legítimos, acrescente-os em config/fontes.yml"
            ),
            linhas_afetadas=int(fora.sum()),
            exemplos=novos,
        )
    ]


def _regra_intervalo(df: pd.DataFrame, ds: Dataset, regra: dict) -> list[Problema]:
    coluna = regra["coluna"]
    if coluna not in df.columns:
        return []
    serie = pd.to_numeric(df[coluna], errors="coerce")
    fora = pd.Series(False, index=df.index)
    if "min" in regra:
        fora |= serie.notna() & (serie < float(regra["min"]))
    if "max" in regra:
        fora |= serie.notna() & (serie > float(regra["max"]))
    if not fora.any():
        return []
    faixa = f"[{regra.get('min', '-∞')}, {regra.get('max', '+∞')}]"
    return [
        Problema(
            dataset=ds.nome,
            codigo="fora_do_intervalo",
            gravidade=AVISO,
            coluna=coluna,
            mensagem=f"valores fora da faixa esperada {faixa}",
            linhas_afetadas=int(fora.sum()),
            exemplos=list(serie[fora].head(5)),
        )
    ]


def _regra_nao_nulo(df: pd.DataFrame, ds: Dataset, regra: dict) -> list[Problema]:
    achados = []
    colunas = list(regra.get("colunas", []))
    if "coluna" in regra:
        colunas.append(regra["coluna"])
    for coluna in colunas:
        if coluna not in df.columns:
            continue
        vazias = df[coluna].isna()
        if vazias.any():
            achados.append(
                Problema(
                    dataset=ds.nome,
                    codigo="valor_nulo",
                    gravidade=ERRO,
                    coluna=coluna,
                    mensagem="coluna que o contrato exige preenchida está vazia",
                    linhas_afetadas=int(vazias.sum()),
                    exemplos=_rotulos(df, ds, vazias),
                )
            )
    return achados


def _regra_minimo_linhas(df: pd.DataFrame, ds: Dataset, regra: dict) -> list[Problema]:
    minimo = int(regra.get("valor", 1))
    if len(df) >= minimo:
        return []
    return [
        Problema(
            dataset=ds.nome,
            codigo="poucas_linhas",
            gravidade=ERRO,
            mensagem=(
                f"a aba '{ds.aba}' trouxe {len(df)} linha(s), abaixo do mínimo de {minimo}. "
                "Planilha exportada pela metade?"
            ),
        )
    ]


def _regra_referencia(
    df: pd.DataFrame, ds: Dataset, regra: dict, tabelas: dict[str, pd.DataFrame]
) -> list[Problema]:
    coluna, alvo_ds = regra["coluna"], regra["dataset"]
    alvo_col = regra.get("coluna_alvo", coluna)
    if coluna not in df.columns or alvo_ds not in tabelas:
        return []
    alvo = tabelas[alvo_ds]
    if alvo_col not in alvo.columns:
        return []
    validos = set(alvo[alvo_col].dropna().astype("string"))
    serie = df[coluna].astype("string")
    orfas = serie.notna() & ~serie.isin(validos)
    if not orfas.any():
        return []
    return [
        Problema(
            dataset=ds.nome,
            codigo="referencia_orfa",
            gravidade=AVISO,
            coluna=coluna,
            mensagem=f"valores que não existem em {alvo_ds}.{alvo_col}",
            linhas_afetadas=int(orfas.sum()),
            exemplos=sorted({str(v) for v in serie[orfas].unique()})[:5],
        )
    ]


_DESPACHO = {
    "unico": _regra_unico,
    "valores_permitidos": _regra_valores,
    "intervalo": _regra_intervalo,
    "nao_nulo": _regra_nao_nulo,
    "minimo_linhas": _regra_minimo_linhas,
}


def validar(tabelas: dict[str, pd.DataFrame], cfg: Config, estrito: bool = False) -> list[Problema]:
    """Aplica o contrato às tabelas já padronizadas."""
    achados: list[Problema] = []
    for nome, df in tabelas.items():
        ds = cfg.datasets[nome]
        achados.extend(_obrigatorias(df, ds))
        for regra in ds.regras:
            tipo = regra["tipo"]
            if tipo == "referencia":
                achados.extend(_regra_referencia(df, ds, regra, tabelas))
            else:
                achados.extend(_DESPACHO[tipo](df, ds, regra))

    if estrito:
        for p in achados:
            p.gravidade = ERRO
    return achados
