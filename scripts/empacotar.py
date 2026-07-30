#!/usr/bin/env python3
"""Empacota o painel num .zip para enviar a quem vai mexer nele fora do git.

Existe porque "me manda o HTML do painel" não tem resposta de um arquivo só: a
página depende do CSS, de quatro módulos de JavaScript, da fonte Raleway, dos
logos, da malha dos municípios e dos dados publicados. Mandar só o .html
entrega uma tela em branco.

O conteúdo é exatamente o de `_site/` — o mesmo pacote que vai ao ar, montado
pela lista de permissão de `montar_site.py`, já conferido por
`checar_publicacao.py`. Não há caminho separado para o zip, de propósito: um
pacote montado por outras regras seria um segundo lugar de onde dado sigiloso
poderia escapar.

Vão junto um LEIA-ME e dois atalhos para abrir. Os atalhos existem porque a
página **não abre com clique duplo**: o navegador recusa módulo de JavaScript e
fonte vindos de `file://`, e o painel fica em branco com erro de CORS no
console. Precisa de um servidor local, e é isso que os atalhos fazem.

Uso:  make pacote     (ou python scripts/empacotar.py)
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
PADRAO_SAIDA = RAIZ / "dist" / "redes-bahia-painel.zip"

LEIA_ME = """# Painel Redes Bahia — cópia para edição

Este é o painel inteiro, do jeito que está no ar, para você mexer localmente.

## Como abrir

**Clique duplo no `index.html` não funciona.** O navegador recusa módulo de
JavaScript e fonte vindos de `file://`, e a tela fica em branco. É preciso um
servidor local — os atalhos abaixo fazem isso e abrem o navegador.

- **macOS / Linux:** abra o Terminal nesta pasta e rode `./abrir.sh`
- **Windows:** clique duas vezes em `abrir.bat`

Qualquer um dos dois deixa o painel em <http://localhost:8000>. Para parar,
feche a janela do terminal (ou Ctrl+C).

Se preferir na mão, dentro desta pasta:

```
python3 -m http.server 8000
```

e abra <http://localhost:8000>.

## Entrar

A tela de entrada é a mesma do site publicado — use a credencial do comitê. A
sessão dura 12 horas, então você entra uma vez e mexe à vontade.

## O que editar

| Arquivo | O que é |
|---|---|
| `dashboard/painel.html` | a estrutura da página |
| `dashboard/assets/painel.css` | todo o estilo (o único arquivo de CSS do painel) |
| `dashboard/assets/painel.js` | o que monta cada bloco a partir dos dados |
| `dashboard/assets/graficos.js` | as barras, a linha do tempo, a tabela equivalente |
| `dashboard/assets/mapa.js` | os dois mapas |
| `design/tokens/tokens.css` | cor, tipografia e espaçamento — a fonte de tudo |
| `dashboard/index.html` | a tela de entrada |

**Cor e tamanho de fonte não se escrevem na mão.** Todos saem de
`design/tokens/tokens.css`, e mudar lá muda a tela inteira de uma vez. Se
precisar de um valor que não existe lá, é sinal de que falta um token — vale
conversar antes de escrever o número solto.

O painel tem **um modo só, o claro**. Não há tema escuro para manter em
sincronia.

## Cuidado com os arquivos versionados

Os nomes de CSS e JS dentro do HTML têm um `?v=` no fim (ex.:
`painel.css?v=3365f73e`). É a impressão do conteúdo, que o site usa para o
navegador não servir uma versão velha. Pode ignorar enquanto edita — quem gera
o pacote refaz esses números.

## Os dados

`data/published/` traz a base que o painel lê, já sem nenhuma coluna que
identifique pessoa. Se precisar testar com outros números, dá para editar o
`credenciamento.json` à vontade: é uma cópia local e não volta para lugar
nenhum.

## Como devolver a mudança

O projeto vive em <https://github.com/movimentobemmaior/redes_bahia>. O mais
simples é mandar de volta os arquivos que você mexeu, dizendo o que mudou — a
gente aplica no repositório e republica.
"""

ABRIR_SH = """#!/bin/sh
# Sobe um servidor local e abre o painel no navegador.
# O painel não funciona com clique duplo: módulo de JavaScript e fonte vindos
# de file:// são recusados pelo navegador. Daí este atalho.
cd "$(dirname "$0")" || exit 1
PORTA=8000
echo "Painel em http://localhost:$PORTA  (Ctrl+C para parar)"
( sleep 1; (command -v open >/dev/null && open "http://localhost:$PORTA") \\
  || (command -v xdg-open >/dev/null && xdg-open "http://localhost:$PORTA") ) &
python3 -m http.server "$PORTA" 2>/dev/null || python -m http.server "$PORTA"
"""

ABRIR_BAT = """@echo off
rem Sobe um servidor local e abre o painel no navegador.
rem O painel nao funciona com clique duplo: modulo de JavaScript e fonte vindos
rem de file:// sao recusados pelo navegador. Dai este atalho.
cd /d "%~dp0"
set PORTA=8000
echo Painel em http://localhost:%PORTA%  (Ctrl+C para parar)
start "" "http://localhost:%PORTA%"
python -m http.server %PORTA%
"""


def _montar_site(destino: Path) -> None:
    """Refaz `_site/` e roda a trava de sigilo antes de empacotar."""
    for script in ("montar_site.py", "checar_publicacao.py"):
        resultado = subprocess.run(  # noqa: S603
            [sys.executable, str(RAIZ / "scripts" / script)],
            capture_output=True,
            text=True,
        )
        if resultado.returncode != 0:
            print(resultado.stdout, resultado.stderr, file=sys.stderr)
            raise SystemExit(f"{script} falhou — nada foi empacotado.")
    if not destino.exists():
        raise SystemExit(f"{destino} não existe depois da montagem.")


def empacotar(saida: Path, site: Path) -> Path:
    saida.parent.mkdir(parents=True, exist_ok=True)
    if saida.exists():
        saida.unlink()

    arquivos = sorted(p for p in site.rglob("*") if p.is_file())
    with zipfile.ZipFile(saida, "w", zipfile.ZIP_DEFLATED) as zip_:
        for arquivo in arquivos:
            zip_.write(arquivo, arquivo.relative_to(site))
        zip_.writestr("LEIA-ME.md", LEIA_ME)
        # ZipInfo com permissão de execução: sem isso o .sh chega sem +x e o
        # atalho do macOS/Linux não roda com clique nem com ./abrir.sh.
        info = zipfile.ZipInfo("abrir.sh")
        info.external_attr = 0o755 << 16
        zip_.writestr(info, ABRIR_SH)
        zip_.writestr("abrir.bat", ABRIR_BAT)

    return saida


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, default=PADRAO_SAIDA)
    parser.add_argument(
        "--pular-montagem",
        action="store_true",
        help="usa o _site/ que já está em disco, sem remontar nem conferir",
    )
    args = parser.parse_args()

    site = RAIZ / "_site"
    if not args.pular_montagem:
        print("Montando e conferindo o pacote…")
        _montar_site(site)

    caminho = empacotar(args.saida, site)
    tamanho = caminho.stat().st_size / 1024
    with zipfile.ZipFile(caminho) as zip_:
        n = len(zip_.namelist())
    print(f"\n  {caminho.relative_to(RAIZ)} · {n} arquivos · {tamanho:.0f} KB")
    print("  Contém LEIA-ME.md e os atalhos abrir.sh / abrir.bat.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
