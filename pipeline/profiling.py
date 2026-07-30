"""Ferramenta de reconhecimento: o que existe dentro do xlsm?

Quando a planilha real chega (ou muda de formato), esta é a primeira coisa a
rodar. Ela não depende do contrato — ao contrário, ela **propõe** um contrato:

    make perfil

gera reports/perfil_<arquivo>.md (relatório para leitura humana) e
reports/rascunho_fontes.yml (rascunho de config/fontes.yml para comparar e
ajustar à mão). O rascunho nunca sobrescreve o contrato em uso: quem decide o
que é obrigatório, sensível ou categórico é uma pessoa, não a inferência.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from .config import RAIZ

DIR_RELATORIOS = RAIZ / "reports"
# Acima deste número de valores distintos, a coluna deixa de ser tratada como
# categoria (não faria sentido virar filtro ou fatia de gráfico).
LIMITE_CATEGORIA = 40
_NAO_ALFANUM = re.compile(r"[^a-z0-9]+")


def slug(texto: str) -> str:
    """'Território de Identidade' -> 'territorio_identidade'."""
    sem_acento = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return _NAO_ALFANUM.sub("_", sem_acento.lower()).strip("_") or "coluna"


@dataclass
class PerfilColuna:
    original: str
    sugerido: str
    tipo: str
    preenchimento: float
    distintos: int
    exemplos: list[Any] = field(default_factory=list)
    provavel_sensivel: bool = False


@dataclass
class PerfilAba:
    aba: str
    n_linhas: int
    linha_cabecalho: int
    colunas: list[PerfilColuna]
    colunas_sem_nome: int = 0


# Comparado palavra a palavra, não por substring: "organizacao" contém "rg",
# e marcar o nome da organização como sigiloso quebraria o painel inteiro.
_PISTAS_SENSIVEIS = {
    "cpf",
    "cnpj",
    "rg",
    "email",
    "mail",
    "telefone",
    "fone",
    "celular",
    "whatsapp",
    "endereco",
    "cep",
    "nascimento",
    "passaporte",
}


def _parece_sensivel(sugerido: str) -> bool:
    return bool(set(sugerido.split("_")) & _PISTAS_SENSIVEIS)


def _inferir_tipo(serie: pd.Series) -> str:
    limpa = serie.dropna()
    if limpa.empty:
        return "texto"
    if pd.api.types.is_bool_dtype(limpa):
        return "booleano"
    if pd.api.types.is_datetime64_any_dtype(limpa):
        return "data"

    try:
        numerica = pd.to_numeric(limpa, errors="coerce")
    except (TypeError, ValueError):  # pragma: no cover - coluna mista exótica
        numerica = pd.Series(dtype="float64")
    validos = numerica.dropna()
    if len(numerica) and numerica.notna().mean() >= 0.95 and len(validos):
        return "inteiro" if bool((validos % 1 == 0).all()) else "decimal"

    como_data = pd.to_datetime(limpa, errors="coerce", dayfirst=True, format="mixed")
    if como_data.notna().mean() >= 0.9:
        return "data"

    textos = limpa.astype(str).str.strip().str.lower()
    if set(textos.unique()) <= {"sim", "não", "nao", "s", "n", "true", "false", "0", "1"}:
        return "booleano"
    if limpa.nunique() <= LIMITE_CATEGORIA and limpa.nunique() < max(2, len(limpa) * 0.5):
        return "categoria"
    return "texto"


def _achar_linha_cabecalho(cru: pd.DataFrame, maximo: int = 10) -> int:
    """Descobre em que linha está o cabeçalho (planilha costuma ter título em cima).

    Heurística: a primeira linha em que a maioria das células está preenchida e é
    texto curto e sem repetição — o padrão de um cabeçalho.
    """
    for i in range(min(maximo, len(cru))):
        linha = cru.iloc[i]
        preenchidas = linha.notna().sum()
        if preenchidas < max(2, len(linha) * 0.5):
            continue
        valores = [str(v).strip() for v in linha.dropna()]
        if len(set(valores)) < len(valores):
            continue
        if all(len(v) <= 60 for v in valores):
            return i + 1
    return 1


def perfilar_arquivo(caminho: Path, max_abas: int = 30) -> list[PerfilAba]:
    """Perfila todas as abas de uma planilha, sem depender do contrato."""
    excel = pd.ExcelFile(caminho, engine="openpyxl")
    perfis: list[PerfilAba] = []

    for aba in excel.sheet_names[:max_abas]:
        cru = pd.read_excel(excel, sheet_name=aba, header=None, dtype=object)
        cru = cru.dropna(axis=1, how="all").dropna(axis=0, how="all")
        if cru.empty:
            perfis.append(PerfilAba(aba=aba, n_linhas=0, linha_cabecalho=1, colunas=[]))
            continue

        linha_cabecalho = _achar_linha_cabecalho(cru)
        df = (
            pd.read_excel(excel, sheet_name=aba, header=linha_cabecalho - 1, dtype=object)
            .dropna(axis=1, how="all")
            .dropna(axis=0, how="all")
        )

        colunas, sem_nome = [], 0
        for nome in df.columns:
            rotulo = str(nome).strip()
            if rotulo.startswith("Unnamed:"):
                sem_nome += 1
                continue
            serie = df[nome]
            distintos = int(serie.nunique(dropna=True))
            sugerido = slug(rotulo)
            colunas.append(
                PerfilColuna(
                    original=rotulo,
                    sugerido=sugerido,
                    tipo=_inferir_tipo(serie),
                    preenchimento=round(float(serie.notna().mean()), 4) if len(df) else 0.0,
                    distintos=distintos,
                    exemplos=[str(v) for v in serie.dropna().unique()[:3]],
                    provavel_sensivel=_parece_sensivel(sugerido),
                )
            )
        perfis.append(
            PerfilAba(
                aba=aba,
                n_linhas=len(df),
                linha_cabecalho=linha_cabecalho,
                colunas=colunas,
                colunas_sem_nome=sem_nome,
            )
        )
    return perfis


def relatorio_markdown(caminho: Path, perfis: list[PerfilAba]) -> str:
    partes = [
        f"# Perfil da planilha `{caminho.name}`",
        "",
        "Gerado por `make perfil` (`python -m pipeline perfil`). Documento de apoio: "
        "use-o para preencher `config/fontes.yml`, não como fonte de verdade.",
        "",
        f"- Abas encontradas: **{len(perfis)}**",
        "",
    ]
    for p in perfis:
        partes += [
            f"## Aba `{p.aba}`",
            "",
            f"- Linhas de dados: **{p.n_linhas}**",
            f"- Linha do cabeçalho (detectada): **{p.linha_cabecalho}**",
            f"- Colunas sem nome ignoradas: {p.colunas_sem_nome}",
            "",
        ]
        if not p.colunas:
            partes += ["_Aba vazia ou sem cabeçalho legível._", ""]
            continue
        partes += [
            "| Coluna na planilha | Nome sugerido | Tipo | Preenchida | Distintos | Exemplos |",
            "|---|---|---|---:|---:|---|",
        ]
        for c in p.colunas:
            marca = " 🔒" if c.provavel_sensivel else ""
            exemplos = ", ".join(e.replace("|", "\\|")[:40] for e in c.exemplos)
            partes.append(
                f"| {c.original}{marca} | `{c.sugerido}` | {c.tipo} | "
                f"{c.preenchimento:.0%} | {c.distintos} | {exemplos} |"
            )
        partes += [
            "",
            "🔒 = provável dado pessoal/identificação; marque como `sensivel: true`.",
            "",
        ]
    return "\n".join(partes)


def rascunho_contrato(perfis: list[PerfilAba]) -> str:
    """Monta um rascunho de config/fontes.yml a partir do que foi encontrado."""
    datasets: dict[str, Any] = {}
    for p in perfis:
        if not p.colunas:
            continue
        colunas: dict[str, Any] = {}
        for c in p.colunas:
            bloco: dict[str, Any] = {"origem": c.original, "tipo": c.tipo, "descricao": ""}
            if c.preenchimento == 1.0:
                bloco["obrigatorio"] = True
            if c.provavel_sensivel:
                bloco["sensivel"] = True
            colunas[c.sugerido] = bloco
        primeira = p.colunas[0]
        datasets[slug(p.aba)] = {
            "aba": p.aba,
            "descricao": "",
            "linha_cabecalho": p.linha_cabecalho,
            "chave": [primeira.sugerido],
            "colunas": colunas,
            "regras": [{"tipo": "minimo_linhas", "valor": 1}],
        }

    cabecalho = (
        "# RASCUNHO gerado por `make perfil` — NÃO é o contrato em uso.\n"
        "# Compare com config/fontes.yml, ajuste chave/obrigatório/sensível/descrição\n"
        "# e só então copie o que fizer sentido.\n"
    )
    corpo = yaml.safe_dump(
        {"versao": 1, "datasets": datasets}, allow_unicode=True, sort_keys=False, indent=2
    )
    return cabecalho + corpo


def salvar(caminho: Path, perfis: list[PerfilAba]) -> tuple[Path, Path]:
    DIR_RELATORIOS.mkdir(parents=True, exist_ok=True)
    md = DIR_RELATORIOS / f"perfil_{caminho.stem}.md"
    yml = DIR_RELATORIOS / "rascunho_fontes.yml"
    md.write_text(relatorio_markdown(caminho, perfis), encoding="utf-8")
    yml.write_text(rascunho_contrato(perfis), encoding="utf-8")
    return md, yml
