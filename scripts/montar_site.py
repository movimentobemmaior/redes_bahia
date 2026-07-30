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
import hashlib
import os
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


def _versionar(destino: Path) -> int:
    """Acrescenta a impressão do conteúdo às referências de CSS e JS.

    Sem isso, o navegador guarda `painel.js` e `painel.css` pelo nome e continua
    servindo a versão antiga contra o HTML novo. Já aconteceu: o JS em cache
    lia um campo que o manifesto tinha renomeado, dava erro e a tela dizia que a
    base não fora publicada — com a base publicada e correta no servidor.

    O nome do arquivo não muda (o caminho continua legível); muda a consulta,
    que é o suficiente para o navegador buscar de novo quando o conteúdo mudar.
    """
    pagina = destino / "dashboard" / "index.html"
    if not pagina.exists():
        return 0

    html = pagina.read_text(encoding="utf-8")
    trocas = 0
    for arquivo in sorted(destino.rglob("*")):
        if arquivo.suffix not in {".css", ".js"}:
            continue
        # relpath e não Path.relative_to: o alvo pode estar acima de dashboard/
        # (tokens.css está em design/), e walk_up só existe a partir do 3.12.
        rel = os.path.relpath(arquivo, destino / "dashboard").replace(os.sep, "/")
        marca = hashlib.sha256(arquivo.read_bytes()).hexdigest()[:8]
        for atributo in (f'href="{rel}"', f'src="{rel}"'):
            if atributo in html:
                html = html.replace(atributo, atributo[:-1] + f'?v={marca}"')
                trocas += 1
    pagina.write_text(html, encoding="utf-8")
    return trocas


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

    versionadas = _versionar(destino)
    if versionadas:
        print(f"  {versionadas} referência(s) de CSS/JS versionada(s) contra cache")
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
