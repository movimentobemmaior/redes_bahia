/* Painel Redes Bahia — credenciamento.
 *
 * Lê data/published/: o manifesto (metadados, semântica das colunas, resultado
 * da validação) e credenciamento.json (as linhas). Nunca toca em data/raw/ ou
 * data/processed/.
 *
 * Regra de negócio importante mora no MANIFESTO, não aqui: qual valor de cada
 * critério torna a organização inelegível (`exclui_quando`). Parte dos
 * critérios do edital tem sentido invertido — "Sim" exclui —, e codificar isso
 * no painel seria a forma mais fácil de publicar um gráfico ao contrário.
 */

import { barrasHorizontais, barraSegmentada, fmt, linhaTempo, tabelaEquivalente } from "./graficos.js";
import { mapaCoropletico, normalizar } from "./mapa.js";

const BASE = "../data/published";

// Qual malha desenhar em cada nível declarado no contrato (`geografia.nivel`).
// Trocar o nível no contrato troca o mapa; nada aqui precisa mudar.
const MALHAS = {
  estado: { arquivo: "geo/brasil-estados.json", unidade: "organizações", maxRotulos: 8 },
  municipio: { arquivo: "geo/bahia-municipios.json", unidade: "organizações", maxRotulos: 12 },
};

/** Plural sem o "(s)" entre parênteses, que é gíria de formulário. */
function plural(n, singular, plural_) {
  return `${fmt.format(n)} ${n === 1 ? singular : plural_}`;
}

const estado = {
  manifesto: null,
  linhas: [],
  criterios: [],
  malha: null,
  filtros: { estado: "", resultado: "", representa: "" },
};

// --- utilidades ---------------------------------------------------------------

const $ = (sel) => document.querySelector(sel);

function formatarData(iso) {
  if (!iso) return "—";
  const [ano, mes, dia] = String(iso).slice(0, 10).split("-");
  return `${dia}/${mes}/${ano}`;
}

function idadeEmTexto(iso) {
  const alvo = new Date(`${String(iso).slice(0, 10)}T00:00:00`);
  const hoje = new Date();
  hoje.setHours(0, 0, 0, 0);
  const dias = Math.round((hoje - alvo) / 86400000);
  if (dias <= 0) return "atualizada hoje";
  if (dias === 1) return "atualizada ontem";
  return `atualizada há ${dias} dias`;
}

function contar(linhas, campo) {
  const mapa = new Map();
  for (const l of linhas) {
    const chave = l[campo] ?? "(não informado)";
    mapa.set(chave, (mapa.get(chave) || 0) + 1);
  }
  return [...mapa.entries()]
    .map(([rotulo, valor]) => ({ rotulo, valor }))
    .sort((a, b) => b.valor - a.valor);
}

/** Normaliza o valor de um critério para comparar com `exclui_quando`.
 *  Colunas booleanas chegam como true/false no JSON; categóricas, como texto. */
function comoTexto(valor) {
  if (valor === true) return "Sim";
  if (valor === false) return "Não";
  return valor == null ? null : String(valor);
}

function aprovada(linha) {
  return String(linha.status_credenciamento || "").toLowerCase().startsWith("aprovado");
}

/** Requisitos que a linha deixou de atender, segundo o contrato. */
function naoAtendidos(linha) {
  return estado.criterios.filter((c) => comoTexto(linha[c.nome]) === c.exclui_quando);
}

function aplicarFiltros(linhas) {
  const { estado: uf, resultado, representa } = estado.filtros;
  return linhas.filter(
    (l) =>
      (!uf || l.estado === uf) &&
      (!resultado || l.status_credenciamento === resultado) &&
      (!representa || l.representa === representa)
  );
}

// --- blocos da tela -----------------------------------------------------------

function montarCabecalho() {
  const m = estado.manifesto;
  const fontes = Object.values(m.fontes ?? {}).map((f) => f.arquivo);
  $("#data-atualizacao").textContent = formatarData(m.data_execucao);
  $("#origem").textContent =
    `${idadeEmTexto(m.data_execucao)} · ${fontes.length === 1 ? "origem" : "origens"}: ` +
    (fontes.join(", ") || "—");

  const edital = m.edital ?? {};
  $("#ficha-inscricoes").textContent = edital.periodo_inscricoes || "—";
  $("#ficha-duracao").textContent = edital.duracao_parceria || "—";
  $("#ficha-territorio").textContent = edital.territorio || "—";

  // O selo diz uma coisa só. Quando está tudo certo, "base validada" basta —
  // repetir "nenhum problema, 0 erros, 0 avisos" ocupa a barra inteira para
  // não acrescentar nada. Quando há o que ver, o número é a informação, e o
  // detalhe fica onde ele já mora, na seção de qualidade.
  const { status, erros, avisos } = m.validacao;
  const selo = $("#selo-validacao");
  selo.dataset.status = status;

  let texto;
  if (erros) {
    texto = plural(erros, "erro na validação", "erros na validação");
  } else if (avisos) {
    texto = plural(avisos, "aviso na validação", "avisos na validação");
  } else {
    texto = "Base validada";
  }
  selo.querySelector(".selo-texto").textContent = texto;
  selo.title =
    status === "aprovado"
      ? "A base passou em todas as regras do contrato de dados."
      : "Abra a seção Qualidade da base para ver o que foi apontado.";
  $("#selo-detalhe").hidden = !(erros || avisos);

  const hashes = Object.entries(m.fontes ?? {})
    .map(([nome, f]) => `${nome}: ${f.hash_sha256.slice(0, 12)}…`)
    .join(" · ");
  $("#procedencia").textContent =
    `Gerada em ${m.gerado_em} pelo pipeline ${m.versao_pipeline}, contrato versão ` +
    `${m.versao_contrato}. SHA-256 das planilhas — ${hashes || "nenhuma"}.`;
}

/** O funil do edital: a leitura de visão geral, antes de qualquer detalhe.
 *
 *  Mostra as cinco etapas sempre, inclusive as que ainda não receberam
 *  planilha. Uma etapa escondida enquanto não tem dado dá a impressão de que o
 *  edital termina onde os dados terminam, que é o contrário do que um painel
 *  de acompanhamento precisa comunicar. */
function montarFunil() {
  const lista = $("#funil-etapas");
  lista.replaceChildren();

  const etapas = estado.manifesto.etapas ?? [];
  let anterior = null;

  for (const etapa of etapas) {
    const item = document.createElement("li");
    item.className = "etapa";
    item.dataset.estado = etapa.estado;

    const ordem = document.createElement("p");
    ordem.className = "etapa-ordem";
    ordem.textContent = `Etapa ${etapa.ordem}`;

    const nome = document.createElement("p");
    nome.className = "etapa-nome";
    nome.textContent = etapa.nome;

    item.append(ordem, nome);

    if (etapa.estado === "com_dados") {
      const valor = document.createElement("p");
      valor.className = "etapa-valor";
      valor.textContent = fmt.format(etapa.n_linhas);
      const unidade = document.createElement("p");
      unidade.className = "etapa-unidade";
      unidade.textContent = etapa.n_linhas === 1 ? "organização" : "organizações";
      item.append(valor, unidade);

      // Taxa de passagem em relação à etapa anterior com dados: é o número que
      // orienta decisão, mais que o total isolado de cada etapa.
      if (anterior && anterior.n_linhas > 0) {
        const taxa = document.createElement("p");
        taxa.className = "etapa-taxa";
        const pct = Math.round((etapa.n_linhas / anterior.n_linhas) * 100);
        taxa.textContent = `${pct}% de ${anterior.nome}`;
        item.append(taxa);
      }
      anterior = etapa;
    } else {
      const espera = document.createElement("p");
      espera.className = "etapa-espera";
      espera.textContent =
        etapa.estado === "aguardando"
          ? "aguardando a planilha da etapa"
          : "ainda sem dados";
      item.append(espera);
    }

    item.title = etapa.resumo || etapa.nome;
    lista.append(item);
  }
}

/** Ordena as seções por etapa e cria as que ainda não têm tela própria. */
function montarSecoesEtapas() {
  const container = $("#etapas");
  const existentes = new Map(
    [...container.querySelectorAll("[data-etapa]")].map((el) => [el.dataset.etapa, el])
  );

  for (const etapa of estado.manifesto.etapas ?? []) {
    let secao = existentes.get(etapa.chave);
    if (!secao) {
      secao = document.createElement("section");
      secao.className = "secao-etapa";
      secao.dataset.etapa = etapa.chave;
      secao.innerHTML = `
        <header class="secao-etapa-cabecalho">
          <span class="secao-etapa-numero"></span>
          <h2></h2>
        </header>
        <p class="secao-etapa-resumo"></p>
        <div class="aguardando"></div>`;
      const espera = secao.querySelector(".aguardando");
      const linha1 = document.createElement("p");
      linha1.textContent =
        etapa.estado === "aguardando"
          ? "O contrato desta etapa já está definido; falta a planilha do dia."
          : "Esta etapa ainda não tem planilha nem contrato de dados.";
      const linha2 = document.createElement("p");
      linha2.append(document.createTextNode("Solte o arquivo .xlsx em "));
      const codigo = document.createElement("code");
      codigo.textContent = `${etapa.pasta}/`;
      linha2.append(codigo, document.createTextNode(" para que os números apareçam aqui."));
      espera.append(linha1, linha2);
    }
    secao.querySelector(".secao-etapa-numero").textContent = `Etapa ${etapa.ordem}`;
    secao.querySelector(".secao-etapa-cabecalho h2").textContent = etapa.nome;
    secao.querySelector(".secao-etapa-resumo").textContent = etapa.resumo || "";
    container.append(secao); // append reordena o que já existe
  }
}

function montarFiltros() {
  const campos = [
    ["#filtro-estado", "estado", "Todos os estados"],
    ["#filtro-resultado", "status_credenciamento", "Todos os resultados"],
    ["#filtro-representa", "representa", "Todas as naturezas"],
  ];
  const chaves = { "#filtro-estado": "estado", "#filtro-resultado": "resultado", "#filtro-representa": "representa" };

  for (const [sel, campo, rotuloVazio] of campos) {
    const select = $(sel);
    const valores = [...new Set(estado.linhas.map((l) => l[campo]).filter(Boolean))].sort();
    select.replaceChildren();
    select.append(new Option(rotuloVazio, ""));
    valores.forEach((v) => select.append(new Option(v, v)));
    select.addEventListener("change", () => {
      estado.filtros[chaves[sel]] = select.value;
      desenhar();
    });
  }

  $("#limpar-filtros").addEventListener("click", () => {
    estado.filtros = { estado: "", resultado: "", representa: "" };
    campos.forEach(([sel]) => ($(sel).value = ""));
    desenhar();
  });
}

function montarIndicadores(linhas) {
  const total = linhas.length;
  const aprovadas = linhas.filter(aprovada).length;
  const naoAprovadas = total - aprovadas;
  // Não aprovada cujas respostas atendem a todos os requisitos: o motivo está
  // fora das colunas do formulário. É anomalia a investigar, não ruído — por
  // isso ocupa um dos quatro números do topo.
  const semMotivo = linhas.filter((l) => !aprovada(l) && naoAtendidos(l).length === 0).length;

  const tiles = [
    ["#kpi-total", total, "respostas ao formulário"],
    ["#kpi-aprovadas", aprovadas, "aprovadas automaticamente"],
    ["#kpi-reprovadas", naoAprovadas, "não aprovadas"],
    ["#kpi-semmotivo", semMotivo, semMotivo === 1
      ? "não aprovada sem requisito não atendido"
      : "não aprovadas sem requisito não atendido"],
  ];
  for (const [sel, valor, rotulo] of tiles) {
    $(`${sel} .valor`).textContent = fmt.format(valor);
    $(`${sel} .rotulo-kpi`).textContent = rotulo;
  }
  $("#kpi-semmotivo").classList.toggle("kpi-alerta", semMotivo > 0);

  barraSegmentada(
    $("#grafico-resultado"),
    [
      { rotulo: "Aprovadas automaticamente", valor: aprovadas, cor: "var(--serie-1)" },
      { rotulo: "Não aprovadas", valor: naoAprovadas, cor: "var(--serie-2)" },
    ],
    // Mais alta que o padrão: ao lado de um gráfico de linha de 220px, uma
    // barra de 40px lê como rodapé em vez de como a outra metade da linha.
    { rotulo: "Resultado do credenciamento", altura: 56 }
  );

  // A barra mostra a proporção; a nota diz o número. Sem ela, a taxa de
  // aprovação — que é o que se leva para a reunião — teria de ser calculada de
  // cabeça a partir de dois cartões.
  $("#nota-resultado").textContent = total
    ? `${Math.round((aprovadas / total) * 100)}% de aprovação automática ` +
      `(${fmt.format(aprovadas)} de ${fmt.format(total)}).`
    : "Nenhuma organização no recorte atual.";
}

/** O gráfico central: qual requisito está barrando quem.
 *
 *  Conta, para cada critério, quantas organizações responderam o valor que o
 *  contrato marca como excludente. Uma organização pode falhar em mais de um
 *  critério — por isso a soma das barras é maior que o total de não aprovadas,
 *  e o texto abaixo do gráfico diz isso. */
function montarCriterios(linhas) {
  const escopo = $("#escopo-criterios").value;
  const base = escopo === "reprovadas" ? linhas.filter((l) => !aprovada(l)) : linhas;

  const dados = estado.criterios
    .map((c) => ({
      rotulo: c.rotulo,
      valor: base.filter((l) => comoTexto(l[c.nome]) === c.exclui_quando).length,
    }))
    .filter((d) => d.valor > 0)
    .sort((a, b) => b.valor - a.valor);

  barrasHorizontais($("#grafico-criterios"), dados, {
    rotulo: "Critérios não atendidos",
    cor: "var(--serie-2)",
    // Requisito de edital é frase, não palavra: com a calha estreita, todos
    // terminavam em reticências e o gráfico deixava de dizer qual é qual.
    larguraRotulo: 380,
    total: base.length,
  });

  $("#nota-criterios").textContent = base.length
    ? `Entre ${fmt.format(base.length)} ${escopo === "reprovadas" ? "não aprovadas" : "respostas"}. ` +
      "Uma organização pode deixar de atender a mais de um requisito, então a soma das barras é " +
      "maior que o total."
    : "Nenhuma organização no filtro atual.";

  $("#tabela-criterios").replaceChildren(
    tabelaEquivalente(dados, ["Requisito não atendido", "Organizações"])
  );
}

function montarNatureza(linhas) {
  const porNatureza = contar(linhas, "representa");
  barrasHorizontais($("#grafico-natureza"), porNatureza, {
    rotulo: "Natureza jurídica",
    larguraRotulo: 280,
    total: linhas.length,
  });
}

/** O mapa: de onde vêm as organizações, sobre a malha declarada no contrato.
 *
 *  Enquanto o formulário só perguntar o estado, a leitura possível é "quantas
 *  vêm de fora do território do edital" — que já é decisão, porque sede fora da
 *  Bahia é critério de exclusão. Quando a coluna de município chegar, muda o
 *  `geografia.nivel` do contrato e o mesmo bloco passa a desenhar municípios. */
function montarTerritorio(linhas) {
  const geo = estado.manifesto.geografia;
  const bloco = $("#mapa-territorio").closest(".bloco");
  if (!geo || !estado.malha) {
    bloco.hidden = true;
    return;
  }
  bloco.hidden = false;

  const contagem = contar(linhas, geo.coluna).filter((d) => d.rotulo !== "(não informado)");
  const valores = new Map(contagem.map((d) => [normalizar(d.rotulo), d.valor]));

  mapaCoropletico($("#mapa-territorio"), estado.malha, valores, {
    rotulo: "Organizações por unidade territorial",
    destaque: geo.destaque,
    unidade: MALHAS[geo.nivel]?.unidade ?? "organizações",
    maxRotulos: MALHAS[geo.nivel]?.maxRotulos ?? 8,
  });

  $("#tabela-territorio").replaceChildren(
    tabelaEquivalente(contagem, [geo.nivel === "municipio" ? "Município" : "Estado", "Organizações"])
  );

  // Quem está fora do território do edital. O nome da unidade destacada sai da
  // própria malha, para a frase não depender de uma sigla escrita à mão aqui.
  // A frase diz "território do edital" e põe o nome entre parênteses de
  // propósito: "fora de Bahia" e "fora do Ceará" pedem artigos diferentes, e
  // não há como acertar a crase de um nome que vem de um arquivo.
  const alvo = (estado.malha.features ?? []).find(
    (f) => normalizar(f.properties.chave) === normalizar(geo.destaque)
  );
  const dentro = new Set([normalizar(geo.destaque), normalizar(alvo?.properties.nome)]);
  const fora = contagem.filter((d) => !dentro.has(normalizar(d.rotulo)));
  const nFora = fora.reduce((s, d) => s + d.valor, 0);
  const territorio =
    estado.manifesto.edital?.territorio || alvo?.properties.nome || geo.destaque;

  // Recorte vazio precisa dizer que está vazio: "todas declararam sede no
  // território" com zero respostas é verdadeiro por vacuidade e lido como
  // afirmação sobre a base.
  const total = contagem.reduce((s, d) => s + d.valor, 0);
  $("#nota-territorio").textContent = !total
    ? "Nenhuma organização no recorte atual."
    : nFora
      ? `${plural(nFora, "organização declarou sede fora", "organizações declararam sede fora")} ` +
        `do território do edital — ${fora.map((d) => d.rotulo).join(", ")}. ` +
        "Sede fora do território é critério de exclusão."
      : `Todas as ${plural(total, "resposta", "respostas")} do recorte ` +
        `declararam sede no território do edital (${territorio}).`;
}

function comoData(iso) {
  return new Date(`${String(iso).slice(0, 10)}T00:00:00`);
}

function diasEntre(de, ate) {
  return Math.round((comoData(ate) - comoData(de)) / 86400000);
}

/** Dias corridos até uma data ISO. Negativo quando ela já passou. */
function diasAte(iso) {
  const hoje = new Date();
  hoje.setHours(0, 0, 0, 0);
  return Math.round((comoData(iso) - hoje) / 86400000);
}

/** Quanto falta para fechar as inscrições. Não depende de filtro: é do edital.
 *
 *  Fica ao lado do gráfico de ritmo porque é lá que a informação decide algo —
 *  ritmo caindo com muito prazo pela frente pede divulgação; ritmo caindo na
 *  véspera é só o fim natural da janela. */
function montarPrazo() {
  const fim = estado.manifesto.edital?.fim_inscricoes;
  const cartao = $("#prazo-inscricoes");
  if (!fim) {
    cartao.hidden = true;
    return;
  }
  const dias = diasAte(fim);
  const valor = cartao.querySelector(".cartao-prazo-valor");
  const rotulo = cartao.querySelector(".cartao-prazo-rotulo");

  if (dias > 0) {
    valor.textContent = fmt.format(dias);
    rotulo.textContent = `${dias === 1 ? "dia" : "dias"} até ${formatarData(fim)}, fim das inscrições`;
  } else if (dias === 0) {
    valor.textContent = "Hoje";
    rotulo.textContent = "último dia de inscrições";
  } else {
    valor.textContent = "Encerrado";
    rotulo.textContent = `inscrições fechadas em ${formatarData(fim)}`;
  }
  cartao.dataset.situacao = dias < 0 ? "encerrado" : dias <= 3 ? "reta-final" : "aberto";
  cartao.hidden = false;
}

function montarEvolucao(linhas) {
  const porDia = new Map();
  for (const l of linhas) {
    if (!l.data_resposta) continue;
    const dia = String(l.data_resposta).slice(0, 10);
    porDia.set(dia, (porDia.get(dia) || 0) + 1);
  }
  const dias = [...porDia.entries()].sort(([a], [b]) => a.localeCompare(b));
  const pontos = dias.map(([dia, valor]) => ({ rotulo: formatarData(dia), valor }));

  linhaTempo($("#grafico-evolucao"), pontos, { rotulo: "Respostas por dia" });

  const total = dias.reduce((s, [, v]) => s + v, 0);
  if (!dias.length) {
    $("#nota-ritmo").textContent = "Nenhuma resposta no recorte atual.";
    return;
  }
  // Média sobre o intervalo corrido entre a primeira e a última resposta, e não
  // sobre o número de dias com movimento: dia sem resposta é informação sobre o
  // ritmo, e descartá-lo infla a média justamente quando o fluxo está secando.
  const primeiro = dias[0][0];
  const ultimo = dias[dias.length - 1][0];
  const media = total / Math.max(1, diasEntre(primeiro, ultimo) + 1);
  $("#nota-ritmo").textContent =
    `${plural(total, "resposta", "respostas")} entre ${formatarData(primeiro)} e ` +
    `${formatarData(ultimo)} — média de ` +
    `${media.toLocaleString("pt-BR", { maximumFractionDigits: 1 })} por dia.`;
}

function montarTabela(linhas) {
  const corpo = $("#tabela-organizacoes tbody");
  corpo.replaceChildren();

  const ordenadas = [...linhas].sort((a, b) =>
    String(a.organizacao || "").localeCompare(String(b.organizacao || ""), "pt-BR")
  );

  for (const l of ordenadas) {
    const tr = document.createElement("tr");
    const ok = aprovada(l);
    const faltas = naoAtendidos(l).map((c) => c.rotulo);

    const celulas = [
      l.organizacao ?? "—",
      l.estado ?? "—",
      l.representa ?? "—",
      formatarData(l.data_resposta),
    ];
    celulas.forEach((texto) => {
      const td = document.createElement("td");
      td.textContent = texto;
      tr.append(td);
    });

    const tdStatus = document.createElement("td");
    const tag = document.createElement("span");
    tag.className = "tag";
    tag.dataset.resultado = ok ? "aprovada" : "reprovada";
    tag.textContent = l.status_credenciamento ?? "—";
    tdStatus.append(tag);
    tr.append(tdStatus);

    const tdMotivo = document.createElement("td");
    tdMotivo.className = "motivo";
    if (faltas.length) {
      tdMotivo.textContent = faltas.join("; ");
    } else if (!ok) {
      tdMotivo.textContent = "nenhum — motivo fora das colunas do formulário";
      tdMotivo.classList.add("motivo-ausente");
    } else {
      tdMotivo.textContent = "—";
    }
    tr.append(tdMotivo);

    corpo.append(tr);
  }

  $("#contagem-tabela").textContent =
    `${fmt.format(ordenadas.length)} de ${fmt.format(estado.linhas.length)} organizações`;
}

function montarQualidade() {
  const ds = estado.manifesto.datasets[0];
  const lista = $("#qualidade");
  lista.replaceChildren();

  const incompletas = ds.colunas
    .filter((c) => c.publicada && c.preenchimento < 1)
    .sort((a, b) => a.preenchimento - b.preenchimento);

  if (!incompletas.length) {
    const li = document.createElement("li");
    li.textContent = "Todas as colunas publicadas estão 100% preenchidas.";
    lista.append(li);
  } else {
    for (const c of incompletas) {
      const li = document.createElement("li");
      li.innerHTML = `<code>${c.nome}</code> — ${Math.round(c.preenchimento * 100)}% preenchida`;
      lista.append(li);
    }
  }

  const omitidas = ds.colunas_omitidas_por_sigilo;
  $("#sigilo").textContent = omitidas.length
    ? `${plural(omitidas.length, "coluna retida", "colunas retidas")} por sigilo e ` +
      `fora desta publicação: ${omitidas.join(", ")}.`
    : "Nenhuma coluna retida por sigilo.";

  const problemas = estado.manifesto.validacao.problemas ?? [];
  const tabela = $("#tabela-problemas");
  const vazio = $("#sem-problemas");
  if (!problemas.length) {
    tabela.hidden = true;
    vazio.hidden = false;
    return;
  }
  const corpo = tabela.querySelector("tbody");
  corpo.replaceChildren();
  for (const p of [...problemas].sort((a, b) => (b.gravidade === "erro") - (a.gravidade === "erro"))) {
    const tr = document.createElement("tr");
    const tdTag = document.createElement("td");
    const tag = document.createElement("span");
    tag.className = "tag";
    tag.dataset.gravidade = p.gravidade;
    tag.textContent = p.gravidade;
    tdTag.append(tag);
    tr.append(tdTag);
    [p.coluna ?? "—", p.mensagem, p.linhas_afetadas || "—", (p.exemplos ?? []).join(", ") || "—"].forEach(
      (texto, i) => {
        const td = document.createElement("td");
        td.textContent = texto;
        if (i === 2) td.className = "num";
        tr.append(td);
      }
    );
    corpo.append(tr);
  }
}

function desenhar() {
  const linhas = aplicarFiltros(estado.linhas);
  const filtrando = Object.values(estado.filtros).some(Boolean);
  $("#aviso-filtro").hidden = !filtrando;

  montarIndicadores(linhas);
  montarEvolucao(linhas);
  montarCriterios(linhas);
  montarTerritorio(linhas);
  montarNatureza(linhas);
  montarTabela(linhas);
}

/** Busca a malha do nível declarado no contrato.
 *
 *  Falha aqui não derruba o painel: o mapa é um bloco entre outros, e uma
 *  malha ausente não pode apagar os números. O bloco simplesmente não aparece.
 */
async function carregarMalha(geografia) {
  const escolha = MALHAS[geografia?.nivel];
  if (!escolha) return null;
  try {
    // Resolvido contra o módulo, não contra a página: a malha mora ao lado
    // deste arquivo, e um caminho relativo à página quebraria se o painel
    // passasse a ser servido de outra pasta.
    const resposta = await fetch(new URL(escolha.arquivo, import.meta.url));
    return resposta.ok ? await resposta.json() : null;
  } catch {
    return null;
  }
}

function configurarTema() {
  const botao = $("#alternar-tema");
  const raiz = document.documentElement;
  const aplicar = (tema) => {
    raiz.dataset.tema = tema;
    const escuro = tema === "escuro";
    botao.textContent = escuro ? "Modo claro" : "Modo escuro";
    botao.setAttribute("aria-pressed", String(escuro));
  };

  const salvo = localStorage.getItem("tema-painel");
  if (salvo) {
    aplicar(salvo);
  } else {
    const escuro = matchMedia("(prefers-color-scheme: dark)").matches;
    botao.textContent = escuro ? "Modo claro" : "Modo escuro";
    botao.setAttribute("aria-pressed", String(escuro));
  }

  botao.addEventListener("click", () => {
    const preferenciaEscura = matchMedia("(prefers-color-scheme: dark)").matches;
    const atual = raiz.dataset.tema || (preferenciaEscura ? "escuro" : "claro");
    const novo = atual === "escuro" ? "claro" : "escuro";
    aplicar(novo);
    localStorage.setItem("tema-painel", novo);
  });
}

async function iniciar() {
  configurarTema();
  try {
    const [manifesto, linhas] = await Promise.all([
      fetch(`${BASE}/manifest.json`, { cache: "no-store" }).then(exigirOk),
      fetch(`${BASE}/credenciamento.json`, { cache: "no-store" }).then(exigirOk),
    ]);

    estado.manifesto = manifesto;
    estado.linhas = linhas;
    // A semântica de exclusão vem do contrato, via manifesto.
    estado.criterios = manifesto.datasets[0].colunas
      .filter((c) => c.publicada && c.exclui_quando)
      .map((c) => ({
        nome: c.nome,
        exclui_quando: c.exclui_quando,
        rotulo: c.descricao ? c.descricao.split(".")[0] : c.nome,
      }));

    estado.malha = await carregarMalha(manifesto.geografia);

    montarCabecalho();
    montarFunil();
    montarSecoesEtapas();
    montarFiltros();
    montarPrazo();
    montarQualidade();
    $("#escopo-criterios").addEventListener("change", () => montarCriterios(aplicarFiltros(estado.linhas)));

    // Mostrar antes de desenhar: os gráficos medem a largura do contêiner, e
    // contêiner escondido mede zero.
    $("#carregando").hidden = true;
    $("#painel").hidden = false;
    desenhar();

    // Redesenhar ao mudar a largura, pela mesma razão.
    let tempo;
    addEventListener("resize", () => {
      clearTimeout(tempo);
      tempo = setTimeout(desenhar, 150);
    });
  } catch (erro) {
    // Distinguir as duas falhas importa: "não há base" é estado normal do
    // primeiro dia; "a base veio e a tela quebrou" é defeito, e chamá-lo de
    // "base não publicada" manda quem lê procurar no lugar errado. Foi o que
    // aconteceu quando um JS em cache encontrou um manifesto novo.
    const semBase = erro instanceof RespostaFaltando;
    $("#carregando").hidden = true;
    $("#erro").hidden = false;
    $("#erro").dataset.tipo = semBase ? "sem-base" : "falha";
    $("#erro-titulo").textContent = semBase
      ? "A base ainda não foi publicada"
      : "A base foi publicada, mas o painel não conseguiu montar a tela";
    $("#erro-explicacao").textContent = semBase
      ? "Nenhuma planilha foi processada até agora, então não há dados para mostrar. " +
        "Assim que a primeira atualização rodar, esta página passa a exibir o painel."
      : "Os dados chegaram do servidor, então o problema está na página e não na base. " +
        "A causa mais comum é uma versão antiga do painel guardada em cache: " +
        "recarregue com Ctrl+F5 (ou Cmd+Shift+R).";
    $("#erro-detalhe").textContent = String(erro);
  }
}

/** Erro de busca dos dados, separado de qualquer outra falha de montagem. */
class RespostaFaltando extends Error {}

async function exigirOk(resposta) {
  if (!resposta.ok) {
    throw new RespostaFaltando(`HTTP ${resposta.status} ao buscar ${resposta.url}`);
  }
  return resposta.json();
}

iniciar();
