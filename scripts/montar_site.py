#!/usr/bin/env python3
"""Monta o pacote do painel para hospedagem, em _site/.

A propriedade de segurança está no formato: o site é montado por **lista de
permissão**. Nada é copiado por padrão — só o que está em CONTEUDO abaixo.
Assim, uma pasta nova no repositório (ou um .xlsm esquecido em data/raw/)
nunca vira arquivo publicado por descuido.

Depois de montar, rode scripts/checar_publicacao.py, que confere o resultado
contra o contrato de dados. As duas coisas são complementares: esta escolhe o
que entra, aquela confere o que entrou.

Uso:  python scripts/montar_site.py [--destino _site]
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

# (origem no repositório, destino dentro do site). A árvore é preservada
# porque a página usa caminhos relativos (../design/, ../data/published/).
CONTEUDO: list[tuple[str, str]] = [
    ("dashboard/index.html", "dashboard/index.html"),
    ("dashboard/assets", "dashboard/assets"),
    ("design/tokens", "design/tokens"),
    ("data/published", "data/published"),
]

# Arquivos que nunca entram, mesmo estando dentro de uma pasta permitida.
NUNCA_COPIAR = {".md", ".xlsm", ".xlsx", ".xls", ".xlsb"}

REDIRECIONADOR = """<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <title>Painel Redes Bahia</title>
  <meta http-equiv="refresh" content="0; url=dashboard/">
  <link rel="canonical" href="dashboard/">
</head>
<body>
  <p>Redirecionando para o <a href="dashboard/">Painel Redes Bahia</a>…</p>
</body>
</html>
"""


def _copiar(origem: Path, destino: Path) -> list[Path]:
    """Copia arquivo ou pasta, pulando extensões vetadas. Devolve o que copiou."""
    copiados: list[Path] = []
    if origem.is_file():
        if origem.suffix.lower() in NUNCA_COPIAR:
            return copiados
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origem, destino)
        return [destino]

    for item in sorted(origem.rglob("*")):
        if not item.is_file() or item.suffix.lower() in NUNCA_COPIAR:
            continue
        alvo = destino / item.relative_to(origem)
        alvo.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, alvo)
        copiados.append(alvo)
    return copiados


def montar(destino: Path, raiz: Path = RAIZ) -> list[Path]:
    if destino.exists():
        shutil.rmtree(destino)
    destino.mkdir(parents=True)

    copiados: list[Path] = []
    for origem_rel, destino_rel in CONTEUDO:
        origem = raiz / origem_rel
        if not origem.exists():
            print(f"  aviso: {origem_rel} não existe — nada a copiar")
            continue
        copiados += _copiar(origem, destino / destino_rel)

    indice = destino / "index.html"
    indice.write_text(REDIRECIONADOR, encoding="utf-8")
    copiados.append(indice)
    return copiados


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destino", type=Path, default=RAIZ / "_site")
    args = parser.parse_args()

    print(f"Montando o site em {args.destino}")
    copiados = montar(args.destino)
    for caminho in copiados:
        print(f"  + {caminho.relative_to(args.destino)}")

    tem_dados = (args.destino / "data" / "published" / "manifest.json").exists()
    print(f"\n  {len(copiados)} arquivo(s).")
    if not tem_dados:
        print("  aviso: sem manifest.json — o painel vai abrir no estado 'base não publicada'.")
    print("\n  Próximo passo obrigatório: python scripts/checar_publicacao.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
