#!/usr/bin/env python3
"""Gera uma planilha de exemplo com a estrutura descrita em config/fontes.yml.

Serve para dois propósitos:

1. rodar o pipeline de ponta a ponta sem tocar em dado real — é o que o CI usa;
2. exercitar o validador — o exemplo inclui de propósito os defeitos típicos de
   formulário exportado (espaço sobrando, categoria fora da lista prevista,
   data como texto com "às").

Os cabeçalhos saem do próprio contrato (`origem` de cada coluna), não de uma
cópia. Assim, coluna nova no contrato aparece aqui automaticamente em vez de o
exemplo divergir da planilha real em silêncio — e as perguntas do formulário,
que passam de 150 caracteres, ficam num lugar só.

Os defeitos plantados são todos de nível AVISO. Nenhum é erro de estrutura,
porque o CI espera que `python -m pipeline dados` termine com sucesso.

Uso:  python scripts/gerar_exemplo.py [--linhas 40] [--saida data/raw/...]

O arquivo gerado é ignorado pelo git (ver .gitignore: data/raw/exemplo_*).
"""

from __future__ import annotations

import argparse
import random
import sys
from datetime import date, timedelta
from pathlib import Path

from openpyxl import Workbook

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from pipeline.config import carregar  # noqa: E402

PREFIXOS = ["Associação", "Instituto", "Coletivo", "Movimento", "Rede"]
TEMAS = ["Sertão", "Recôncavo", "Chapada", "Litoral", "Semiárido", "Vale", "Serra"]
ESTADOS = ["Bahia"] * 12 + ["Pernambuco", "Sergipe"]
REPRESENTA = ["Associação sem fins lucrativos"] * 8 + ["Coletivo"] * 3 + ["Nenhuma das opções"]
DOIS_REPRESENTANTES = [
    "Sim",
    "Não",
    "Não se aplica, pois somos uma organização social (ONG, OSC)",
]


def _sim_nao(rnd: random.Random, peso_sim: float) -> str:
    return "Sim" if rnd.random() < peso_sim else "Não"


def _resposta(rnd: random.Random, i: int, base: date) -> dict[str, object]:
    """Uma linha, indexada pelo nome técnico das colunas do contrato."""
    organizacao = f"{rnd.choice(PREFIXOS)} {rnd.choice(TEMAS)} {i:03d}"
    if i == 3:
        organizacao = f"  {organizacao}  "  # defeito: espaço sobrando

    sede_bahia = _sim_nao(rnd, 0.9)
    receita_alta = _sim_nao(rnd, 0.15)
    partidario = _sim_nao(rnd, 0.05)
    religioso = _sim_nao(rnd, 0.08)
    aprovado = (
        sede_bahia == "Sim"
        and receita_alta == "Não"
        and partidario == "Não"
        and religioso == "Não"
    )
    status = "Aprovado automaticamente" if aprovado else "Não aprovado"
    if i == 5:
        status = "Aprovado"  # defeito: categoria fora da lista prevista (aviso)

    dia = base + timedelta(days=rnd.randint(0, 9))
    hora = f"{rnd.randint(8, 22):02d}:{rnd.randint(0, 59):02d}"

    return {
        "id": 110000 + i,
        "organizacao": organizacao,
        "estado": rnd.choice(ESTADOS),
        "respondente_nome": f"Pessoa Exemplo {i:03d}",
        "respondente_email": f"contato{i:03d}@exemplo.org.br",
        "formulario": "Credenciamento Redes Bahia",
        "data_resposta": f"{dia.strftime('%d/%m/%Y')} às {hora}",
        "status_credenciamento": status,
        "representa": rnd.choice(REPRESENTA),
        "criterio_estatuto_registrado": _sim_nao(rnd, 0.85),
        "criterio_regularidade_credito": "Sim",
        "criterio_dois_representantes": rnd.choice(DOIS_REPRESENTANTES),
        "criterio_sede_bahia": sede_bahia,
        "criterio_atuacao_apenas_bahia": _sim_nao(rnd, 0.8),
        "criterio_municipios_ate_200mil": _sim_nao(rnd, 0.75),
        "criterio_em_atividade": "Sim",
        "criterio_receita_acima_500mil": receita_alta,
        "ciencia_comprovacao_receita": "Ciente",
        "criterio_atuacao_minima_3_anos": _sim_nao(rnd, 0.85),
        "criterio_vinculo_partidario": partidario,
        "criterio_fins_religiosos": religioso,
        # 'edital' fica de fora: veio vazia na exportação real de 30/07/2026.
    }


def gerar(linhas: int, saida: Path, semente: int = 7, contrato: Path | None = None) -> Path:
    cfg = carregar(contrato)
    ds = next(iter(cfg.datasets.values()))

    rnd = random.Random(semente)
    wb = Workbook()
    ws = wb.active
    ws.title = ds.aba
    ws.append([c.origem for c in ds.colunas])

    base = date(2026, 7, 20)
    for i in range(1, linhas + 1):
        resposta = _resposta(rnd, i, base)
        ws.append([resposta.get(c.nome) for c in ds.colunas])

    saida.parent.mkdir(parents=True, exist_ok=True)
    wb.save(saida)
    return saida


def destino_padrao(contrato: Path | None = None) -> Path:
    """Pasta da etapa dona do dataset, tirada do contrato.

    Fixar `data/raw/` aqui já quebrou o CI uma vez: a fonte passou a vir da
    etapa e o exemplo continuou caindo na raiz, onde o pipeline não olha mais.
    """
    cfg = carregar(contrato)
    ds = next(iter(cfg.datasets.values()))
    etapa = next(e for e in cfg.etapas if e.dataset == ds.nome)
    return etapa.pasta / f"exemplo_{date.today().isoformat()}_{etapa.chave}.xlsx"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--linhas", type=int, default=40, help="número de respostas")
    parser.add_argument("--saida", type=Path, default=None)
    args = parser.parse_args()
    destino = gerar(args.linhas, args.saida or destino_padrao())
    print(f"Planilha de exemplo criada em {destino}")
    print("Rode agora: make dados")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
