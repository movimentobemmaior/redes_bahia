"""Gera o dicionário de dados a partir do contrato.

O dicionário é derivado, nunca escrito à mão: documentação de dados que é
mantida em paralelo com o código sempre desatualiza. Quem quer mudar o
dicionário muda `config/fontes.yml` e roda `make dicionario`.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from .config import RAIZ, Config

DESTINO = RAIZ / "docs" / "03-dicionario-de-dados.md"
MANIFESTO = RAIZ / "data" / "published" / "manifest.json"


def _stats_do_manifesto() -> dict[str, dict[str, Any]]:
    """Enriquece o dicionário com preenchimento real, se já houver publicação."""
    if not MANIFESTO.exists():
        return {}
    dados = json.loads(MANIFESTO.read_text(encoding="utf-8"))
    return {
        ds["nome"]: {
            "n_linhas": ds["n_linhas"],
            "colunas": {c["nome"]: c for c in ds["colunas"]},
        }
        for ds in dados.get("datasets", [])
    }


def gerar(cfg: Config, hoje: date | None = None) -> str:
    stats = _stats_do_manifesto()
    hoje = hoje or date.today()
    linhas = [
        "# Dicionário de dados",
        "",
        "> **Arquivo gerado automaticamente — não edite à mão.**",
        "> Fonte: `config/fontes.yml`. Para atualizar: `make dicionario`.",
        f"> Última geração: {hoje.isoformat()} · versão do contrato: {cfg.versao}",
        "",
        "## Como ler",
        "",
        "- **Coluna** — nome técnico, usado nos arquivos publicados e no painel.",
        "- **Origem** — cabeçalho correspondente na planilha de origem.",
        "- **Tipo** — `texto`, `categoria`, `inteiro`, `decimal`, `data`, `booleano`.",
        "- **Obr.** — obrigatória: se vier vazia, a publicação é bloqueada.",
        "- **Sigilo** — dado pessoal/identificação: fica em `data/processed/` e "
        "**não** é publicado.",
        "- **Preench.** — percentual preenchido na última execução do pipeline.",
        "",
    ]

    for nome, ds in cfg.datasets.items():
        info = stats.get(nome, {})
        linhas += [f"## `{nome}`", ""]
        if ds.descricao:
            linhas += [ds.descricao, ""]
        linhas += [
            f"- Aba na planilha: `{ds.aba}` (cabeçalho na linha {ds.linha_cabecalho})",
            f"- Grão / chave: {', '.join(f'`{c}`' for c in ds.chave) or '_não definido_'}",
        ]
        if "n_linhas" in info:
            linhas.append(f"- Linhas na última execução: **{info['n_linhas']}**")
        linhas += [
            "",
            "| Coluna | Origem | Tipo | Obr. | Sigilo | Preench. | Descrição |",
            "|---|---|---|:-:|:-:|---:|---|",
        ]
        for col in ds.colunas:
            c_stats = info.get("colunas", {}).get(col.nome, {})
            preench = c_stats.get("preenchimento")
            preench_txt = f"{preench:.0%}" if isinstance(preench, int | float) else "—"
            linhas.append(
                f"| `{col.nome}` | {col.origem} | {col.tipo} | "
                f"{'sim' if col.obrigatorio else '—'} | {'🔒' if col.sensivel else '—'} | "
                f"{preench_txt} | {col.descricao or '—'} |"
            )
        linhas.append("")

        if ds.regras:
            linhas += ["**Regras de validação**", ""]
            for regra in ds.regras:
                linhas.append(f"- {_descrever_regra(regra)}")
            linhas.append("")

    linhas += [
        "## Colunas não publicadas (LGPD)",
        "",
        "Estas colunas existem na base interna e são removidas de `data/published/`:",
        "",
    ]
    algum = False
    for nome, ds in cfg.datasets.items():
        for col in ds.sensiveis:
            linhas.append(f"- `{nome}.{col}`")
            algum = True
    if not algum:
        linhas.append("- _nenhuma coluna marcada como sensível no contrato._")
    linhas.append("")
    return "\n".join(linhas)


def _descrever_regra(regra: dict[str, Any]) -> str:
    tipo = regra["tipo"]
    if tipo == "unico":
        return f"**unicidade** em ({', '.join(regra['colunas'])}) — duplicata bloqueia (erro)."
    if tipo == "valores_permitidos":
        valores = ", ".join(f"`{v}`" for v in regra["valores"])
        return (
            f"**valores previstos** em `{regra['coluna']}`: {valores} — fora da lista gera aviso."
        )
    if tipo == "intervalo":
        minimo, maximo = regra.get("min", "—"), regra.get("max", "—")
        return (
            f"**faixa** de `{regra['coluna']}`: mín. {minimo}, máx. {maximo} "
            "— fora da faixa gera aviso."
        )
    if tipo == "nao_nulo":
        alvos = regra.get("colunas", [regra.get("coluna")])
        return f"**preenchimento obrigatório** em {', '.join(f'`{a}`' for a in alvos)} (erro)."
    if tipo == "minimo_linhas":
        return f"**mínimo de {regra.get('valor', 1)} linha(s)** — abaixo disso bloqueia (erro)."
    if tipo == "referencia":
        alvo = f"{regra['dataset']}.{regra.get('coluna_alvo', regra['coluna'])}"
        return f"**referência**: `{regra['coluna']}` deve existir em `{alvo}` — órfão gera aviso."
    return tipo  # pragma: no cover


def salvar(cfg: Config, destino: Path | None = None) -> Path:
    destino = destino or DESTINO
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(gerar(cfg) + "\n", encoding="utf-8")
    return destino
