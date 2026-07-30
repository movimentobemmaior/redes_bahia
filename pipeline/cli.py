"""Interface de linha de comando do pipeline.

    python -m pipeline perfil        # o que tem dentro do xlsm?
    python -m pipeline validar       # a planilha de hoje passa no contrato?
    python -m pipeline dados         # valida e publica a base do painel
    python -m pipeline dicionario    # regera docs/03-dicionario-de-dados.md

Códigos de saída: 0 = ok · 1 = dado reprovado · 2 = erro de configuração/fonte.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from . import __version__, dicionario, ingest, profiling, publish
from .config import ErroConfig, caminho_curto, carregar
from .ingest import ErroFonte
from .problemas import Problema, contar
from .transform import padronizar
from .validate import validar

DIR_RELATORIOS = Path(profiling.DIR_RELATORIOS)


def _titulo(texto: str) -> None:
    print(f"\n\033[1m{texto}\033[0m" if sys.stdout.isatty() else f"\n{texto}")


def _relatar(problemas: list[Problema]) -> None:
    erros, avisos = contar(problemas)
    if not problemas:
        print("  Nenhum problema encontrado.")
        return
    for p in sorted(problemas, key=lambda p: (not p.bloqueia, p.dataset, p.codigo)):
        print(p.como_linha())
    print(f"\n  Total: {erros} erro(s), {avisos} aviso(s).")


def _salvar_relatorio(problemas: list[Problema], arquivo: str, quando: datetime) -> Path:
    DIR_RELATORIOS.mkdir(parents=True, exist_ok=True)
    destino = DIR_RELATORIOS / "validacao.md"
    erros, avisos = contar(problemas)
    linhas = [
        "# Relatório de validação",
        "",
        f"- Planilha: `{arquivo}`",
        f"- Execução: {quando.isoformat(timespec='seconds')}",
        f"- Resultado: **{erros} erro(s), {avisos} aviso(s)**",
        "",
    ]
    if problemas:
        linhas += [
            "| Gravidade | Dataset | Coluna | Problema | Linhas | Exemplos |",
            "|---|---|---|---|---:|---|",
        ]
        for p in problemas:
            exemplos = ", ".join(str(e).replace("|", "\\|")[:40] for e in p.exemplos[:3])
            linhas.append(
                f"| {p.gravidade} | {p.dataset} | {p.coluna or '—'} | {p.mensagem} | "
                f"{p.linhas_afetadas or '—'} | {exemplos or '—'} |"
            )
    else:
        linhas.append("Nenhum problema encontrado. ✅")
    destino.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return destino


def _carregar_tabelas(
    cfg, arquivo: ingest.Arquivo
) -> tuple[dict[str, pd.DataFrame], list[Problema]]:
    tabelas: dict[str, pd.DataFrame] = {}
    problemas: list[Problema] = []
    for nome, ds in cfg.datasets.items():
        bruto = ingest.ler_aba(arquivo.caminho, ds)
        resultado = padronizar(bruto, ds)
        tabelas[nome] = resultado.df
        problemas.extend(resultado.problemas)
        print(f"  {nome:<14} {len(resultado.df):>6} linha(s)  (aba '{ds.aba}')")
    return tabelas, problemas


def cmd_perfil(args: argparse.Namespace) -> int:
    cfg = carregar(args.config)
    alvo = Path(args.arquivo) if args.arquivo else ingest.localizar(cfg)[-1].caminho
    _titulo(f"Perfilando {alvo.name}")
    perfis = profiling.perfilar_arquivo(alvo)
    for p in perfis:
        print(f"  aba '{p.aba}': {p.n_linhas} linha(s), {len(p.colunas)} coluna(s) nomeada(s)")
    md, yml = profiling.salvar(alvo, perfis)
    print(f"\n  Relatório: {caminho_curto(md)}")
    print(f"  Rascunho do contrato: {caminho_curto(yml)}")
    print("\n  Próximo passo: compare o rascunho com config/fontes.yml e ajuste à mão.")
    return 0


def _executar(args: argparse.Namespace, publicar: bool) -> int:
    cfg = carregar(args.config)
    arquivos = ingest.localizar(cfg)
    arquivo = arquivos[-1]
    _titulo(f"Lendo {arquivo.nome}")
    print(f"  sha256 {arquivo.hash_sha256[:12]}…  ({arquivo.bytes / 1024:.0f} KB)")

    tabelas, problemas = _carregar_tabelas(cfg, arquivo)

    _titulo("Validando contra o contrato")
    problemas += validar(tabelas, cfg, estrito=args.estrito)
    _relatar(problemas)

    agora = datetime.now()
    relatorio = _salvar_relatorio(problemas, arquivo.nome, agora)
    print(f"  Relatório salvo em {caminho_curto(relatorio)}")

    erros, _ = contar(problemas)
    if erros and not args.forcar:
        _titulo("Publicação bloqueada")
        print(
            "  Há erro(s) de estrutura. A base publicada continua como estava\n"
            "  (o painel segue mostrando os dados da última execução válida).\n"
            "  Corrija a planilha e rode de novo, ou use --forcar se souber o que está fazendo."
        )
        return 1
    if not publicar:
        _titulo("Validação concluída (nada foi publicado)")
        return 0

    _titulo("Publicando")
    data_execucao = date.fromisoformat(args.data) if args.data else agora.date()
    manifesto = publish.publicar(
        tabelas=tabelas,
        cfg=cfg,
        arquivo=arquivo,
        problemas=problemas,
        data_execucao=data_execucao,
        versao_pipeline=__version__,
    )
    for ds in manifesto["datasets"]:
        omitidas = ds["colunas_omitidas_por_sigilo"]
        extra = f" · {len(omitidas)} coluna(s) retida(s) por sigilo" if omitidas else ""
        print(f"  {ds['nome']:<14} {ds['n_linhas']:>6} linha(s){extra}")
    print(
        f"\n  Manifesto: data/published/manifest.json (status: {manifesto['validacao']['status']})"
    )

    caminho_dic = dicionario.salvar(cfg)
    print(f"  Dicionário: {caminho_curto(caminho_dic)}")
    return 0


def cmd_dados(args: argparse.Namespace) -> int:
    return _executar(args, publicar=True)


def cmd_validar(args: argparse.Namespace) -> int:
    return _executar(args, publicar=False)


def cmd_dicionario(args: argparse.Namespace) -> int:
    cfg = carregar(args.config)
    destino = dicionario.salvar(cfg)
    print(f"Dicionário gerado em {caminho_curto(destino)}")
    return 0


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m pipeline",
        description="Pipeline da base estática do Painel Redes Bahia.",
    )
    parser.add_argument("--version", action="version", version=f"pipeline {__version__}")
    parser.add_argument(
        "--config", default=None, help="caminho do contrato (padrão: config/fontes.yml)"
    )
    sub = parser.add_subparsers(dest="comando", required=True)

    p_perfil = sub.add_parser("perfil", help="inspeciona o xlsm e propõe um contrato")
    p_perfil.add_argument("--arquivo", help="planilha específica (padrão: a mais recente)")
    p_perfil.set_defaults(func=cmd_perfil)

    for nome, ajuda, func in (
        ("validar", "valida a planilha sem publicar", cmd_validar),
        ("dados", "valida e publica a base do painel", cmd_dados),
    ):
        p = sub.add_parser(nome, help=ajuda)
        p.add_argument("--estrito", action="store_true", help="trata avisos como erros")
        p.add_argument("--forcar", action="store_true", help="publica mesmo com erros")
        p.add_argument("--data", help="data da execução no histórico (AAAA-MM-DD)")
        p.set_defaults(func=func)

    p_dic = sub.add_parser("dicionario", help="regera docs/03-dicionario-de-dados.md")
    p_dic.set_defaults(func=cmd_dicionario)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = construir_parser().parse_args(argv)
    try:
        return args.func(args)
    except ErroConfig as exc:
        print(f"\n[erro de configuração] {exc}", file=sys.stderr)
        return 2
    except ErroFonte as exc:
        print(f"\n[erro na planilha de origem] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
