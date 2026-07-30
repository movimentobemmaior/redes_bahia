"""Leitura e checagem do contrato de dados (config/fontes.yml).

O contrato é a única fonte de verdade sobre a estrutura da planilha. Erros aqui
são erros de configuração (culpa do arquivo YAML), não de dados — por isso têm
uma exceção própria e mensagens que apontam a chave problemática.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

RAIZ = Path(__file__).resolve().parents[1]
CAMINHO_PADRAO = RAIZ / "config" / "fontes.yml"

TIPOS_VALIDOS = {"texto", "inteiro", "decimal", "data", "booleano", "categoria"}
REGRAS_VALIDAS = {
    "unico",
    "valores_permitidos",
    "intervalo",
    "nao_nulo",
    "minimo_linhas",
    "referencia",
}
FORMATOS_VALIDOS = {"csv", "parquet", "json"}
SELECOES_VALIDAS = {"mais_recente", "todos"}


class ErroConfig(Exception):
    """Contrato de dados inválido ou incompleto."""


@dataclass(frozen=True)
class Coluna:
    nome: str
    origem: str
    tipo: str
    obrigatorio: bool = False
    sensivel: bool = False
    descricao: str = ""


@dataclass(frozen=True)
class Dataset:
    nome: str
    aba: str
    descricao: str
    linha_cabecalho: int
    chave: tuple[str, ...]
    colunas: tuple[Coluna, ...]
    regras: tuple[dict[str, Any], ...]

    def coluna(self, nome: str) -> Coluna | None:
        return next((c for c in self.colunas if c.nome == nome), None)

    @property
    def nomes(self) -> list[str]:
        return [c.nome for c in self.colunas]

    @property
    def sensiveis(self) -> list[str]:
        return [c.nome for c in self.colunas if c.sensivel]


@dataclass(frozen=True)
class Fonte:
    diretorio: Path
    padrao_arquivo: str
    selecao: str


@dataclass(frozen=True)
class Publicacao:
    formatos: tuple[str, ...]
    remover_sensiveis: bool
    limite_linhas_json: int


@dataclass(frozen=True)
class Historico:
    arquivo: Path
    agrupar_por: tuple[str, ...]


@dataclass(frozen=True)
class Config:
    versao: int
    fonte: Fonte
    publicacao: Publicacao
    historico: Historico
    datasets: dict[str, Dataset]
    caminho: Path


def caminho_curto(caminho: Path) -> str:
    """Caminho relativo à raiz quando possível, absoluto quando não (testes, NFS)."""
    try:
        return str(caminho.relative_to(RAIZ))
    except ValueError:
        return str(caminho)


def _exigir(bloco: dict[str, Any], chave: str, onde: str) -> Any:
    if chave not in bloco:
        raise ErroConfig(f"{onde}: chave obrigatória '{chave}' ausente.")
    return bloco[chave]


def _resolver(caminho: str | Path) -> Path:
    """Caminhos do contrato são relativos à raiz do repositório."""
    p = Path(caminho)
    return p if p.is_absolute() else RAIZ / p


def _ler_coluna(nome: str, bruto: Any, onde: str) -> Coluna:
    if not isinstance(bruto, dict):
        raise ErroConfig(f"{onde}: a coluna '{nome}' deve ser um bloco com 'origem' e 'tipo'.")
    tipo = str(_exigir(bruto, "tipo", f"{onde} > {nome}"))
    if tipo not in TIPOS_VALIDOS:
        raise ErroConfig(
            f"{onde} > {nome}: tipo '{tipo}' desconhecido. "
            f"Use um de: {', '.join(sorted(TIPOS_VALIDOS))}."
        )
    return Coluna(
        nome=nome,
        origem=str(bruto.get("origem", nome)),
        tipo=tipo,
        obrigatorio=bool(bruto.get("obrigatorio", False)),
        sensivel=bool(bruto.get("sensivel", False)),
        descricao=str(bruto.get("descricao", "")).strip(),
    )


def _ler_regras(bruto: Any, ds_nome: str, nomes: set[str]) -> tuple[dict[str, Any], ...]:
    regras: list[dict[str, Any]] = []
    for i, regra in enumerate(bruto or [], start=1):
        onde = f"datasets > {ds_nome} > regras[{i}]"
        if not isinstance(regra, dict):
            raise ErroConfig(f"{onde}: cada regra deve ser um bloco com a chave 'tipo'.")
        tipo = str(_exigir(regra, "tipo", onde))
        if tipo not in REGRAS_VALIDAS:
            raise ErroConfig(
                f"{onde}: regra '{tipo}' desconhecida. "
                f"Use uma de: {', '.join(sorted(REGRAS_VALIDAS))}."
            )
        alvos = list(regra.get("colunas", []))
        if "coluna" in regra:
            alvos.append(regra["coluna"])
        for alvo in alvos:
            # 'dataset'/'coluna_alvo' de uma regra 'referencia' apontam para outro
            # dataset e são checados depois, quando todos já foram carregados.
            if alvo not in nomes:
                raise ErroConfig(
                    f"{onde}: aponta para a coluna '{alvo}', que não está declarada "
                    f"em datasets > {ds_nome} > colunas."
                )
        if tipo == "intervalo" and "min" not in regra and "max" not in regra:
            raise ErroConfig(f"{onde}: regra 'intervalo' precisa de 'min' e/ou 'max'.")
        if tipo == "valores_permitidos" and not regra.get("valores"):
            raise ErroConfig(f"{onde}: regra 'valores_permitidos' precisa da lista 'valores'.")
        if tipo == "referencia":
            for chave in ("coluna", "dataset"):
                _exigir(regra, chave, onde)
        if tipo == "unico" and not regra.get("colunas"):
            raise ErroConfig(f"{onde}: regra 'unico' precisa da lista 'colunas'.")
        regras.append(dict(regra))
    return tuple(regras)


def _ler_dataset(nome: str, bruto: Any) -> Dataset:
    onde = f"datasets > {nome}"
    if not isinstance(bruto, dict):
        raise ErroConfig(f"{onde}: deve ser um bloco de configuração.")
    colunas_brutas = _exigir(bruto, "colunas", onde)
    if not isinstance(colunas_brutas, dict) or not colunas_brutas:
        raise ErroConfig(f"{onde} > colunas: declare ao menos uma coluna.")

    colunas = tuple(_ler_coluna(n, c, onde) for n, c in colunas_brutas.items())
    nomes = {c.nome for c in colunas}

    chave = tuple(str(c) for c in bruto.get("chave", []))
    for c in chave:
        if c not in nomes:
            raise ErroConfig(f"{onde} > chave: '{c}' não está declarada em colunas.")

    linha_cabecalho = int(bruto.get("linha_cabecalho", 1))
    if linha_cabecalho < 1:
        raise ErroConfig(f"{onde} > linha_cabecalho: deve ser 1 ou maior.")

    return Dataset(
        nome=nome,
        aba=str(_exigir(bruto, "aba", onde)),
        descricao=str(bruto.get("descricao", "")).strip(),
        linha_cabecalho=linha_cabecalho,
        chave=chave,
        colunas=colunas,
        regras=_ler_regras(bruto.get("regras"), nome, nomes),
    )


def _checar_referencias(datasets: dict[str, Dataset]) -> None:
    """Só é possível checar regras 'referencia' depois de ler todos os datasets."""
    for nome, ds in datasets.items():
        for regra in ds.regras:
            if regra["tipo"] != "referencia":
                continue
            alvo = str(regra["dataset"])
            onde = f"datasets > {nome} > regras (referencia)"
            if alvo not in datasets:
                raise ErroConfig(
                    f"{onde}: aponta para o dataset '{alvo}', que não existe. "
                    f"Declarados: {', '.join(datasets)}."
                )
            alvo_col = str(regra.get("coluna_alvo", regra["coluna"]))
            if datasets[alvo].coluna(alvo_col) is None:
                raise ErroConfig(f"{onde}: aponta para '{alvo}.{alvo_col}', coluna não declarada.")


def carregar(caminho: str | Path | None = None) -> Config:
    """Lê o contrato de dados e devolve a configuração já checada."""
    caminho = Path(caminho) if caminho else CAMINHO_PADRAO
    if not caminho.exists():
        raise ErroConfig(f"Contrato de dados não encontrado em {caminho}.")

    bruto = yaml.safe_load(caminho.read_text(encoding="utf-8")) or {}
    if not isinstance(bruto, dict):
        raise ErroConfig(f"{caminho}: o conteúdo deve ser um mapeamento YAML.")

    fonte_bruta = _exigir(bruto, "fonte", str(caminho.name))
    selecao = str(fonte_bruta.get("selecao", "mais_recente"))
    if selecao not in SELECOES_VALIDAS:
        raise ErroConfig(
            f"fonte > selecao: '{selecao}' inválido. "
            f"Use um de: {', '.join(sorted(SELECOES_VALIDAS))}."
        )
    fonte = Fonte(
        diretorio=_resolver(fonte_bruta.get("diretorio", "data/raw")),
        padrao_arquivo=str(fonte_bruta.get("padrao_arquivo", "*.xlsm")),
        selecao=selecao,
    )

    pub_bruta = bruto.get("publicacao") or {}
    formatos = tuple(str(f) for f in pub_bruta.get("formatos", ["csv", "json"]))
    invalidos = set(formatos) - FORMATOS_VALIDOS
    if invalidos:
        raise ErroConfig(
            f"publicacao > formatos: {', '.join(sorted(invalidos))} não suportado(s). "
            f"Use: {', '.join(sorted(FORMATOS_VALIDOS))}."
        )
    publicacao = Publicacao(
        formatos=formatos,
        remover_sensiveis=bool(pub_bruta.get("remover_sensiveis", True)),
        limite_linhas_json=int(pub_bruta.get("limite_linhas_json", 0)),
    )

    hist_bruto = bruto.get("historico") or {}
    historico = Historico(
        arquivo=_resolver(hist_bruto.get("arquivo", "data/published/historico.csv")),
        agrupar_por=tuple(str(c) for c in hist_bruto.get("agrupar_por", [])),
    )

    datasets_brutos = _exigir(bruto, "datasets", str(caminho.name))
    if not isinstance(datasets_brutos, dict) or not datasets_brutos:
        raise ErroConfig("datasets: declare ao menos um dataset.")
    datasets = {n: _ler_dataset(n, d) for n, d in datasets_brutos.items()}
    _checar_referencias(datasets)

    return Config(
        versao=int(bruto.get("versao", 1)),
        fonte=fonte,
        publicacao=publicacao,
        historico=historico,
        datasets=datasets,
        caminho=caminho,
    )
