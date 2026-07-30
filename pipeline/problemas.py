"""Tipo comum para tudo que der errado com os DADOS (não com a configuração).

Padronizar isso em um só lugar é o que permite que padronização e validação
alimentem o mesmo relatório, o mesmo manifesto e o mesmo código de saída.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

ERRO = "erro"
AVISO = "aviso"


@dataclass
class Problema:
    dataset: str
    codigo: str
    gravidade: str
    mensagem: str
    coluna: str | None = None
    linhas_afetadas: int = 0
    exemplos: list[Any] = field(default_factory=list)

    @property
    def bloqueia(self) -> bool:
        return self.gravidade == ERRO

    def como_dict(self) -> dict[str, Any]:
        return {
            "dataset": self.dataset,
            "codigo": self.codigo,
            "gravidade": self.gravidade,
            "mensagem": self.mensagem,
            "coluna": self.coluna,
            "linhas_afetadas": self.linhas_afetadas,
            "exemplos": [str(e) for e in self.exemplos[:5]],
        }

    def como_linha(self) -> str:
        marca = "ERRO " if self.bloqueia else "aviso"
        alvo = f"{self.dataset}.{self.coluna}" if self.coluna else self.dataset
        sufixo = f" ({self.linhas_afetadas} linha(s))" if self.linhas_afetadas else ""
        exemplos = f" ex.: {', '.join(str(e) for e in self.exemplos[:3])}" if self.exemplos else ""
        return f"  [{marca}] {alvo}: {self.mensagem}{sufixo}{exemplos}"


def contar(problemas: list[Problema]) -> tuple[int, int]:
    """Devolve (erros, avisos)."""
    erros = sum(1 for p in problemas if p.bloqueia)
    return erros, len(problemas) - erros
