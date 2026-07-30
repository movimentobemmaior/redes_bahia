"""Camada 2 — padronização: da planilha humana para a tabela previsível.

Aqui mora todo o conhecimento sobre "sujeira de planilha": espaço sobrando,
célula vazia que parece texto, número em formato brasileiro (1.234,56), data
como número de série do Excel, "Sim"/"Não" no lugar de booleano, ID numérico
que virou 123.0.

Toda perda de informação vira um Problema — nada é descartado em silêncio.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import pandas as pd

from .config import Coluna, Dataset
from .problemas import AVISO, ERRO, Problema

_ESPACOS = re.compile(r"\s+")
_MILHAR_BR = re.compile(r"^\d{1,3}(\.\d{3})+$")
_VERDADEIROS = {"sim", "s", "true", "verdadeiro", "1", "x"}
_FALSOS = {"nao", "não", "n", "false", "falso", "0"}
# Faixa de números de série do Excel que corresponde a 1954-2079: o suficiente
# para reconhecer uma data que veio como número sem confundir com "ano" ou nota.
_SERIE_MIN, _SERIE_MAX = 20_000, 65_000


@dataclass
class Padronizado:
    dataset: str
    df: pd.DataFrame
    problemas: list[Problema] = field(default_factory=list)


def _texto_limpo(valor: object) -> object:
    """Normaliza uma célula para texto, devolvendo pd.NA quando não há conteúdo."""
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return pd.NA
    if valor is pd.NA or valor is pd.NaT:
        return pd.NA
    if isinstance(valor, float) and valor.is_integer():
        # IDs e códigos que o Excel entregou como 123.0 devem virar "123".
        valor = int(valor)
    if isinstance(valor, pd.Timestamp):
        return valor.date().isoformat()
    texto = _ESPACOS.sub(" ", str(valor)).strip()
    return texto or pd.NA


def _para_numero(valor: object) -> object:
    """Converte para número aceitando formato brasileiro e símbolo de moeda."""
    if valor is None or valor is pd.NA:
        return pd.NA
    if isinstance(valor, bool):
        return int(valor)
    if isinstance(valor, int | float):
        return pd.NA if pd.isna(valor) else valor
    texto = str(valor).strip()
    if not texto:
        return pd.NA
    texto = texto.replace("R$", "").replace("%", "").replace("\xa0", " ").strip()
    negativo = texto.startswith("(") and texto.endswith(")")
    if negativo:
        texto = texto[1:-1]
    texto = texto.replace(" ", "")
    if "," in texto:
        # Formato brasileiro: ponto é separador de milhar, vírgula é decimal.
        texto = texto.replace(".", "").replace(",", ".")
    elif _MILHAR_BR.match(texto.lstrip("+-")):
        # Sem vírgula, "2.000" é ambíguo (2000 ou 2.0). Grupos de exatamente três
        # dígitos só aparecem como separador de milhar — "2.5" e "2.50" não casam.
        texto = texto.replace(".", "")
    numero = pd.to_numeric(texto, errors="coerce")
    if pd.isna(numero):
        return pd.NA
    return -numero if negativo else numero


def _para_data(serie: pd.Series) -> pd.Series:
    """Converte para data aceitando texto dd/mm/aaaa, ISO e série do Excel."""
    numerico = pd.to_numeric(serie, errors="coerce")
    e_serie = numerico.between(_SERIE_MIN, _SERIE_MAX)

    # format="mixed" converte célula a célula. É mais lento que inferir um
    # formato único, mas é o que permite conviver com "21/04/2026" e
    # "2026-04-21" na mesma coluna — o que sempre acontece em planilha manual.
    convertido = pd.to_datetime(
        serie.where(~e_serie), errors="coerce", dayfirst=True, format="mixed"
    )
    if e_serie.any():
        das_series = pd.to_datetime(
            numerico.where(e_serie), unit="D", origin="1899-12-30", errors="coerce"
        )
        convertido = convertido.fillna(das_series)
    return convertido.dt.normalize()


def _para_booleano(valor: object) -> object:
    if valor is None or valor is pd.NA:
        return pd.NA
    if isinstance(valor, bool):
        return valor
    texto = str(valor).strip().lower()
    if texto in _VERDADEIROS:
        return True
    if texto in _FALSOS:
        return False
    return pd.NA


def _converter(serie: pd.Series, col: Coluna) -> pd.Series:
    limpa = serie.map(_texto_limpo)
    if col.tipo in ("texto", "categoria"):
        return limpa.astype("string")
    if col.tipo == "inteiro":
        return pd.to_numeric(limpa.map(_para_numero), errors="coerce").round().astype("Int64")
    if col.tipo == "decimal":
        return pd.to_numeric(limpa.map(_para_numero), errors="coerce").astype("Float64")
    if col.tipo == "data":
        return _para_data(limpa)
    if col.tipo == "booleano":
        return limpa.map(_para_booleano).astype("boolean")
    return limpa.astype("string")  # pragma: no cover - config.py já barra tipos novos


def padronizar(df_bruto: pd.DataFrame, ds: Dataset) -> Padronizado:
    """Renomeia, converte tipos e devolve a tabela no formato do contrato."""
    problemas: list[Problema] = []
    presentes = list(df_bruto.columns)
    saida = pd.DataFrame(index=df_bruto.index)

    for col in ds.colunas:
        if col.origem not in presentes:
            problemas.append(
                Problema(
                    dataset=ds.nome,
                    codigo="coluna_ausente",
                    gravidade=ERRO,
                    coluna=col.nome,
                    mensagem=(
                        f"a coluna '{col.origem}' não foi encontrada na aba '{ds.aba}'. "
                        "A planilha mudou de formato ou o cabeçalho foi renomeado"
                    ),
                )
            )
            saida[col.nome] = pd.Series(pd.NA, index=df_bruto.index, dtype="object")
            saida[col.nome] = _converter(saida[col.nome], col)
            continue

        origem = df_bruto[col.origem]
        antes = origem.map(_texto_limpo).notna()
        convertida = _converter(origem, col)
        perdidas = antes & convertida.isna()
        if perdidas.any():
            problemas.append(
                Problema(
                    dataset=ds.nome,
                    codigo="conversao_invalida",
                    gravidade=AVISO,
                    coluna=col.nome,
                    mensagem=f"valores que não puderam ser lidos como '{col.tipo}' viraram vazio",
                    linhas_afetadas=int(perdidas.sum()),
                    exemplos=list(origem[perdidas].head(5)),
                )
            )
        saida[col.nome] = convertida

    declaradas = {c.origem for c in ds.colunas}
    extras = [c for c in presentes if c not in declaradas]
    if extras:
        problemas.append(
            Problema(
                dataset=ds.nome,
                codigo="coluna_nao_declarada",
                gravidade=AVISO,
                mensagem=(
                    f"a aba '{ds.aba}' tem {len(extras)} coluna(s) que o contrato não conhece "
                    "e que ficaram fora da base. Se são necessárias, declare-as em "
                    "config/fontes.yml"
                ),
                linhas_afetadas=0,
                exemplos=extras,
            )
        )

    return Padronizado(dataset=ds.nome, df=saida.reset_index(drop=True), problemas=problemas)
