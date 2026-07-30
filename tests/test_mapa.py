"""As malhas do mapa e o acoplamento entre contrato, painel e ativo em disco.

O mapa é o único bloco do painel que depende de um arquivo que não é gerado
pelo pipeline. Se o contrato passar a pedir um nível cuja malha não existe, o
painel não quebra — ele só deixa de desenhar o mapa, em silêncio. Estes testes
existem para que esse silêncio vire falha de CI.
"""

from __future__ import annotations

import json
import math
import re

from pipeline.config import RAIZ

PAINEL_JS = RAIZ / "dashboard" / "assets" / "painel.js"
DIR_GEO = RAIZ / "dashboard" / "assets" / "geo"


def _malhas_declaradas_no_painel() -> dict[str, str]:
    """Lê o mapa nivel -> arquivo direto do JavaScript do painel."""
    fonte = PAINEL_JS.read_text(encoding="utf-8")
    return dict(re.findall(r'(\w+):\s*\{\s*arquivo:\s*"([^"]+)"', fonte))


def test_toda_malha_declarada_no_painel_existe_em_disco():
    declaradas = _malhas_declaradas_no_painel()
    assert declaradas, "painel.js deveria declarar ao menos uma malha em MALHAS"
    for nivel, arquivo in declaradas.items():
        caminho = PAINEL_JS.parent / arquivo
        assert caminho.exists(), f"nível '{nivel}' aponta para {arquivo}, que não existe"


def test_nivel_do_contrato_tem_malha(contrato_real):
    """Trocar `geografia.nivel` sem ter a malha esconderia o mapa sem avisar."""
    if contrato_real.geografia is None:
        return
    declaradas = _malhas_declaradas_no_painel()
    assert contrato_real.geografia.nivel in declaradas, (
        f"o contrato pede o nível '{contrato_real.geografia.nivel}', "
        f"e o painel só sabe desenhar: {', '.join(sorted(declaradas))}"
    )


def test_malhas_tem_a_forma_que_o_painel_espera():
    for caminho in sorted(DIR_GEO.glob("*.json")):
        malha = json.loads(caminho.read_text(encoding="utf-8"))
        assert malha["type"] == "FeatureCollection", caminho.name
        assert malha["features"], f"{caminho.name} está sem feições"
        assert malha.get("credito"), f"{caminho.name} deve creditar a fonte"
        for f in malha["features"]:
            props = f["properties"]
            assert props.get("chave"), f"{caminho.name}: feição sem 'chave'"
            assert props.get("nome"), f"{caminho.name}: feição sem 'nome'"
            assert f["geometry"]["type"] in {"Polygon", "MultiPolygon"}


def test_destaque_do_contrato_existe_na_malha(contrato_real):
    """Destaque que não casa com nenhuma feição não desenha contorno nenhum."""
    geo = contrato_real.geografia
    if geo is None or not geo.destaque:
        return
    arquivo = _malhas_declaradas_no_painel()[geo.nivel]
    malha = json.loads((PAINEL_JS.parent / arquivo).read_text(encoding="utf-8"))
    chaves = {f["properties"]["chave"].casefold() for f in malha["features"]}
    assert geo.destaque.casefold() in chaves, (
        f"geografia > destaque: '{geo.destaque}' não está em {arquivo}"
    )


# --- Simplificação da malha ----------------------------------------------------


def test_simplificar_preserva_extremos_e_descarta_o_que_e_reto():
    """Douglas–Peucker: os cantos ficam, os pontos sobre a reta somem."""
    from scripts.gerar_malhas import simplificar

    reta_com_ruido = [(0, 0), (1, 0.001), (2, 0), (3, 0.001), (4, 0)]
    assert simplificar(reta_com_ruido, 0.01) == [(0, 0), (4, 0)]

    canto = [(0, 0), (1, 0), (2, 0), (2, 2)]
    resultado = simplificar(canto, 0.01)
    assert resultado[0] == (0, 0) and resultado[-1] == (2, 2)
    assert (2, 0) in resultado, "o vértice do canto não pode ser descartado"


def test_simplificar_aguenta_anel_longo_sem_estourar_a_pilha():
    """A versão recursiva estourava em municípios do Recôncavo."""
    from scripts.gerar_malhas import simplificar

    circulo = [
        (math.cos(i / 20000 * 2 * math.pi), math.sin(i / 20000 * 2 * math.pi))
        for i in range(20000)
    ]
    assert 3 < len(simplificar(circulo, 0.05)) < 200
