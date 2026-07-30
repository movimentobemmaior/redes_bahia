#!/usr/bin/env python3
"""Gera as malhas geográficas do painel a partir das fontes públicas.

Por que um script e não um download em tempo de execução: o painel abre sem
rede e sem build (docs/04-arquitetura.md). A malha entra no repositório como
qualquer outro ativo — e este script é o registro de **de onde ela veio e o que
foi feito com ela**, para que alguém possa refazer o arquivo em vez de ter que
confiar num JSON de 200 KB que apareceu num commit.

Fontes:

  municípios  tbrugz/geodata-br · CC0 1.0    (malha do IBGE)
  população   wcota/covid19br · CC BY 4.0    (estimativa do IBGE)

A população entra na malha municipal porque um critério do edital é
territorial: só vale atuação em município baiano de até 200 mil habitantes. Sem
o número junto do contorno, o painel não teria como desenhar onde o edital pode
atuar — e a alternativa, uma lista escrita à mão, envelhece em silêncio.

O que o script faz com elas:

  1. simplifica o contorno (Douglas–Peucker) — a malha original tem detalhe de
     escala 1:250.000, e o painel desenha o estado inteiro em 500px de largura;
  2. arredonda a coordenada para 4 casas (~11 m), que é uma casa a mais do que
     um pixel desta escala consegue distinguir;
  3. joga fora tudo que não é geometria ou nome.

Rodar exige rede; o resultado é versionado, então o dia a dia não precisa.

Uso:  python scripts/gerar_malhas.py
"""

from __future__ import annotations

import csv
import json
import math
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DESTINO = RAIZ / "dashboard" / "assets" / "geo"

FONTES = {
    "bahia-municipios.json": {
        "url": "https://raw.githubusercontent.com/tbrugz/geodata-br/"
        "master/geojson/geojs-29-mun.json",
        "credito": "tbrugz/geodata-br (CC0 1.0), a partir do IBGE",
        "chave": lambda p: p.get("id"),
        "nome": lambda p: p.get("name"),
        # ~1,1 km. Município baiano pequeno tem ~20 km de lado; abaixo disto o
        # contorno some, acima dele os 417 polígonos ficam retos demais.
        "tolerancia": 0.01,
    },
}

# População estimada pelo IBGE, distribuída por wcota/covid19br. A coluna é a
# estimativa mais recente do arquivo; trocar de ano é trocar esta constante.
POPULACAO = {
    "url": "https://raw.githubusercontent.com/wcota/covid19br/master/cities_info.csv",
    "coluna": "pop2021",
    "uf": "BA",
    "credito": "população estimada pelo IBGE (2021), via wcota/covid19br (CC BY 4.0)",
    "aplica_em": "bahia-municipios.json",
}

CASAS = 4


def _distancia_ponto_reta(p, a, b) -> float:
    """Distância perpendicular de p ao segmento a–b, em graus."""
    (px, py), (ax, ay), (bx, by) = p, a, b
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def simplificar(pontos: list, tolerancia: float) -> list:
    """Douglas–Peucker iterativo.

    Iterativo e não recursivo de propósito: um anel costeiro tem dezenas de
    milhares de vértices, e a versão recursiva estoura a pilha do Python em
    alguns municípios do Recôncavo.
    """
    if len(pontos) < 3:
        return pontos

    manter = [False] * len(pontos)
    manter[0] = manter[-1] = True
    pilha = [(0, len(pontos) - 1)]

    while pilha:
        inicio, fim = pilha.pop()
        pior, indice = 0.0, -1
        for i in range(inicio + 1, fim):
            d = _distancia_ponto_reta(pontos[i], pontos[inicio], pontos[fim])
            if d > pior:
                pior, indice = d, i
        if pior > tolerancia:
            manter[indice] = True
            pilha.append((inicio, indice))
            pilha.append((indice, fim))

    return [p for p, guardar in zip(pontos, manter, strict=True) if guardar]


def _anel(pontos: list, tolerancia: float) -> list | None:
    """Simplifica um anel e o descarta se ele deixou de ser polígono.

    Ilha pequena vira triângulo degenerado depois da simplificação. Devolver
    None é melhor que desenhar um risco perdido no mar.
    """
    simples = simplificar([tuple(p[:2]) for p in pontos], tolerancia)
    if len(simples) < 4:
        return None
    if simples[0] != simples[-1]:
        simples.append(simples[0])
    return [[round(x, CASAS), round(y, CASAS)] for x, y in simples]


def _geometria(geo: dict, tolerancia: float) -> dict | None:
    if geo["type"] == "Polygon":
        aneis = [a for a in (_anel(r, tolerancia) for r in geo["coordinates"]) if a]
        return {"type": "Polygon", "coordinates": aneis} if aneis else None

    if geo["type"] == "MultiPolygon":
        partes = []
        for poligono in geo["coordinates"]:
            aneis = [a for a in (_anel(r, tolerancia) for r in poligono) if a]
            if aneis:
                partes.append(aneis)
        return {"type": "MultiPolygon", "coordinates": partes} if partes else None

    raise ValueError(f"geometria não suportada: {geo['type']}")


def _populacao_por_codigo() -> tuple[dict[str, int], str]:
    """Código IBGE -> habitantes, só da UF que interessa."""
    with urllib.request.urlopen(POPULACAO["url"], timeout=120) as resposta:
        linhas = resposta.read().decode("utf-8").splitlines()

    leitor = csv.DictReader(linhas)
    coluna = POPULACAO["coluna"]
    tabela: dict[str, int] = {}
    for linha in leitor:
        if linha.get("state") != POPULACAO["uf"]:
            continue
        valor = (linha.get(coluna) or "").strip()
        if valor.isdigit():
            tabela[str(linha["ibge"])] = int(valor)
    if not tabela:
        raise ValueError(f"nenhuma população lida de {POPULACAO['url']} (coluna {coluna})")
    return tabela, POPULACAO["credito"]


def _baixar(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=120) as resposta:
        # A fonte dos estados vem em latin-1; a dos municípios, em utf-8.
        bruto = resposta.read()
    for codificacao in ("utf-8", "latin-1"):
        try:
            return json.loads(bruto.decode(codificacao))
        except UnicodeDecodeError:
            continue
    raise ValueError(f"não consegui decodificar {url}")


def gerar(nome_arquivo: str, receita: dict, destino: Path) -> Path:
    print(f"  {nome_arquivo}: baixando…")
    origem = _baixar(receita["url"])

    populacao: dict[str, int] = {}
    credito_populacao = ""
    if nome_arquivo == POPULACAO["aplica_em"]:
        populacao, credito_populacao = _populacao_por_codigo()

    features = []
    sem_populacao = []
    for f in origem["features"]:
        geometria = _geometria(f["geometry"], receita["tolerancia"])
        if geometria is None:
            continue
        chave = str(receita["chave"](f["properties"]))
        props = {"chave": chave, "nome": receita["nome"](f["properties"])}
        if populacao:
            if chave in populacao:
                props["populacao"] = populacao[chave]
            else:
                # Município sem número é município que o painel não sabe
                # classificar. Falha alto: silenciosamente ele viraria "fora do
                # território" no mapa, que é o oposto do que se quer dizer.
                sem_populacao.append(props["nome"])
        features.append({"type": "Feature", "properties": props, "geometry": geometria})

    if sem_populacao:
        raise ValueError(
            f"{nome_arquivo}: sem população para {len(sem_populacao)} município(s): "
            f"{', '.join(sem_populacao[:5])}…"
        )

    saida = {
        "type": "FeatureCollection",
        "credito": receita["credito"],
        "credito_populacao": credito_populacao or None,
        "gerado_por": "scripts/gerar_malhas.py",
        "features": features,
    }
    caminho = destino / nome_arquivo
    caminho.parent.mkdir(parents=True, exist_ok=True)
    compacto = json.dumps(saida, ensure_ascii=False, separators=(",", ":"))
    caminho.write_text(compacto, encoding="utf-8")

    vertices = sum(
        len(anel)
        for f in features
        for poligono in (
            f["geometry"]["coordinates"]
            if f["geometry"]["type"] == "MultiPolygon"
            else [f["geometry"]["coordinates"]]
        )
        for anel in poligono
    )
    tamanho = caminho.stat().st_size / 1024
    print(f"  {nome_arquivo}: {len(features)} feições · {vertices} vértices · {tamanho:.0f} KB")
    return caminho


def main() -> int:
    print(f"Gerando as malhas em {DESTINO.relative_to(RAIZ)}")
    for nome, receita in FONTES.items():
        gerar(nome, receita, DESTINO)
    print("\n  Confira o resultado no painel antes de commitar: `make painel`.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
