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


def test_malha_do_territorio_existe(contrato_real):
    """Trocar `territorio.malha` sem ter o arquivo esconderia o mapa sem avisar."""
    territorio = getattr(contrato_real.geografia, "territorio", None)
    if territorio is None:
        return
    declaradas = _malhas_declaradas_no_painel()
    assert territorio.malha in declaradas, (
        f"o contrato pede a malha '{territorio.malha}', "
        f"e o painel só sabe desenhar: {', '.join(sorted(declaradas))}"
    )


def test_malha_do_territorio_tem_populacao(contrato_real):
    """O recorte é por população: malha sem o número não classifica nada.

    Sem este teste, um município sem população cairia em "fora do território" —
    dizendo o oposto do que se quer dizer, e sem erro nenhum na tela.
    """
    territorio = getattr(contrato_real.geografia, "territorio", None)
    if territorio is None:
        return
    arquivo = _malhas_declaradas_no_painel()[territorio.malha]
    malha = json.loads((PAINEL_JS.parent / arquivo).read_text(encoding="utf-8"))
    assert malha.get("credito_populacao"), f"{arquivo} deve creditar a fonte da população"
    sem = [f["properties"]["nome"] for f in malha["features"] if "populacao" not in f["properties"]]
    assert not sem, f"{arquivo}: {len(sem)} município(s) sem população — {', '.join(sem[:5])}"


def test_recorte_do_territorio_nao_e_vazio_nem_total(contrato_real):
    """Um corte que não corta nada, ou que corta tudo, é corte errado."""
    territorio = getattr(contrato_real.geografia, "territorio", None)
    if territorio is None:
        return
    arquivo = _malhas_declaradas_no_painel()[territorio.malha]
    malha = json.loads((PAINEL_JS.parent / arquivo).read_text(encoding="utf-8"))
    populacoes = [f["properties"]["populacao"] for f in malha["features"]]
    dentro = sum(1 for p in populacoes if p <= territorio.limite_populacao)
    assert 0 < dentro < len(populacoes), (
        f"limite de {territorio.limite_populacao} habitantes deixa "
        f"{dentro} de {len(populacoes)} municípios no recorte"
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
