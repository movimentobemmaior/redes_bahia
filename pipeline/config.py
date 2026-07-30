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
    # Valor que torna a linha INELEGÍVEL. Existe porque parte dos critérios do
    # edital tem sentido invertido ("Sim" exclui), e ler todos como "Sim = bom"
    # produziria um painel exatamente ao contrário da realidade. Fica no
    # contrato, e não no código do painel, para haver um lugar só onde essa
    # regra é revisada.
    exclui_quando: str | None = None


@dataclass(frozen=True)
class Edital:
    """Dados de capa do regulamento, exibidos no cabeçalho do painel."""

    nome: str
    periodo_inscricoes: str
    duracao_parceria: str
    territorio: str
    # As mesmas datas do período, em ISO, para o painel contar quanto falta.
    inicio_inscricoes: str = ""
    fim_inscricoes: str = ""


@dataclass(frozen=True)
class Territorio:
    """O recorte territorial em que o edital pode atuar.

    Mesmo critério do `criterio_municipios_ate_200mil`, na forma que o mapa
    consegue desenhar. O número fica no contrato porque é regra de edital.
    """

    malha: str
    limite_populacao: int
    rotulo: str


@dataclass(frozen=True)
class Geografia:
    """De onde o mapa tira o lugar de cada linha.

    Existe para que a troca de estado → município seja uma edição do contrato,
    e não do JavaScript: muda `coluna` e `nivel`, e o painel troca a malha.
    """

    coluna: str
    nivel: str
    destaque: str
    territorio: Territorio | None = None


@dataclass(frozen=True)
class Etapa:
    """Uma etapa do edital. O painel monta o funil a partir desta lista.

    Etapa existe mesmo antes de haver planilha: é assim que o painel consegue
    mostrar o funil inteiro desde o primeiro dia, marcando o que ainda não
    chegou em vez de fingir que o edital começa onde os dados começam.
    """

    chave: str
    nome: str
    resumo: str
    pasta: Path
    dataset: str | None
    ordem: int


@dataclass(frozen=True)
class Dataset:
    nome: str
    etapa: str
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
    edital: Edital
    geografia: Geografia | None
    etapas: tuple[Etapa, ...]
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
        exclui_quando=(
            str(bruto["exclui_quando"]) if bruto.get("exclui_quando") is not None else None
        ),
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
        etapa=str(_exigir(bruto, "etapa", onde)),
        aba=str(_exigir(bruto, "aba", onde)),
        descricao=str(bruto.get("descricao", "")).strip(),
        linha_cabecalho=linha_cabecalho,
        chave=chave,
        colunas=colunas,
        regras=_ler_regras(bruto.get("regras"), nome, nomes),
    )


def _ler_etapas(bruto: Any, datasets: dict[str, Dataset]) -> tuple[Etapa, ...]:
    """Lê a lista de etapas do edital e amarra cada uma ao seu dataset."""
    if not isinstance(bruto, list) or not bruto:
        raise ErroConfig("etapas: declare a lista de etapas do edital, em ordem.")

    etapas: list[Etapa] = []
    chaves: set[str] = set()
    for i, item in enumerate(bruto, start=1):
        onde = f"etapas[{i}]"
        if not isinstance(item, dict):
            raise ErroConfig(f"{onde}: cada etapa deve ser um bloco com 'chave' e 'nome'.")
        chave = str(_exigir(item, "chave", onde))
        if chave in chaves:
            raise ErroConfig(f"{onde}: a chave '{chave}' se repete.")
        chaves.add(chave)
        alvo = item.get("dataset")
        if alvo is not None and str(alvo) not in datasets:
            raise ErroConfig(
                f"{onde}: aponta para o dataset '{alvo}', que não está declarado. "
                f"Declarados: {', '.join(datasets) or '(nenhum)'}."
            )
        etapas.append(
            Etapa(
                chave=chave,
                nome=str(_exigir(item, "nome", onde)),
                resumo=str(item.get("resumo", "")).strip(),
                pasta=_resolver(item.get("pasta", f"data/raw/{chave}")),
                dataset=str(alvo) if alvo is not None else None,
                ordem=i,
            )
        )

    # Todo dataset precisa pertencer a uma etapa declarada, e a ligação tem de
    # valer nos dois sentidos: sem isso, um dataset sairia do funil em silêncio.
    for nome, ds in datasets.items():
        if ds.etapa not in chaves:
            raise ErroConfig(
                f"datasets > {nome} > etapa: '{ds.etapa}' não está em etapas. "
                f"Declaradas: {', '.join(sorted(chaves))}."
            )
        etapa = next(e for e in etapas if e.chave == ds.etapa)
        if etapa.dataset != nome:
            raise ErroConfig(
                f"datasets > {nome} diz pertencer à etapa '{ds.etapa}', mas essa etapa "
                f"aponta para {etapa.dataset or '(nenhum dataset)'}."
            )
    return tuple(etapas)


def _como_iso(valor: Any) -> str:
    """AAAA-MM-DD, venha o valor como date do YAML ou como texto."""
    if valor is None:
        return ""
    return str(valor)[:10]


NIVEIS_GEOGRAFICOS = {"estado", "municipio"}


def _ler_geografia(bruto: Any, datasets: dict[str, Dataset]) -> Geografia | None:
    """Bloco opcional: sem ele o painel simplesmente não desenha o mapa."""
    if bruto is None:
        return None
    if not isinstance(bruto, dict):
        raise ErroConfig("geografia: deve ser um bloco com 'coluna' e 'nivel'.")

    nivel = str(_exigir(bruto, "nivel", "geografia"))
    if nivel not in NIVEIS_GEOGRAFICOS:
        raise ErroConfig(
            f"geografia > nivel: '{nivel}' desconhecido. "
            f"Use um de: {', '.join(sorted(NIVEIS_GEOGRAFICOS))}."
        )

    coluna = str(_exigir(bruto, "coluna", "geografia"))
    # Apontar para uma coluna que não existe deixaria o mapa mudo sem nenhum
    # aviso — o painel não tem como distinguir "coluna errada" de "sem dado".
    if not any(ds.coluna(coluna) for ds in datasets.values()):
        onde = ", ".join(sorted(datasets)) or "(nenhum)"
        raise ErroConfig(
            f"geografia > coluna: '{coluna}' não está declarada em nenhum dataset ({onde})."
        )

    return Geografia(
        coluna=coluna,
        nivel=nivel,
        destaque=str(bruto.get("destaque", "")),
        territorio=_ler_territorio(bruto.get("territorio")),
    )


def _ler_territorio(bruto: Any) -> Territorio | None:
    """Bloco opcional: sem ele o painel não desenha o mapa do território."""
    if bruto is None:
        return None
    if not isinstance(bruto, dict):
        raise ErroConfig("geografia > territorio: deve ser um bloco de configuração.")

    malha = str(_exigir(bruto, "malha", "geografia > territorio"))
    if malha not in NIVEIS_GEOGRAFICOS:
        raise ErroConfig(
            f"geografia > territorio > malha: '{malha}' desconhecida. "
            f"Use uma de: {', '.join(sorted(NIVEIS_GEOGRAFICOS))}."
        )

    limite = _exigir(bruto, "limite_populacao", "geografia > territorio")
    try:
        limite = int(limite)
    except (TypeError, ValueError) as erro:
        raise ErroConfig(
            f"geografia > territorio > limite_populacao: '{limite}' não é um número."
        ) from erro
    if limite <= 0:
        raise ErroConfig("geografia > territorio > limite_populacao: deve ser maior que zero.")

    return Territorio(malha=malha, limite_populacao=limite, rotulo=str(bruto.get("rotulo", "")))


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
    etapas = _ler_etapas(_exigir(bruto, "etapas", str(caminho.name)), datasets)

    edital_bruto = bruto.get("edital") or {}
    edital = Edital(
        nome=str(edital_bruto.get("nome", "")),
        periodo_inscricoes=str(edital_bruto.get("periodo_inscricoes", "")),
        duracao_parceria=str(edital_bruto.get("duracao_parceria", "")),
        territorio=str(edital_bruto.get("territorio", "")),
        inicio_inscricoes=_como_iso(edital_bruto.get("inicio_inscricoes")),
        fim_inscricoes=_como_iso(edital_bruto.get("fim_inscricoes")),
    )

    geografia = _ler_geografia(bruto.get("geografia"), datasets)

    return Config(
        versao=int(bruto.get("versao", 1)),
        edital=edital,
        geografia=geografia,
        etapas=etapas,
        fonte=fonte,
        publicacao=publicacao,
        historico=historico,
        datasets=datasets,
        caminho=caminho,
    )
