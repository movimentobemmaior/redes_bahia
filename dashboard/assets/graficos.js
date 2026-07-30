/* Primitivas de gráfico em SVG puro.
 *
 * Sem biblioteca externa: o painel precisa abrir em qualquer máquina, sem
 * build e sem rede. São poucas formas — barras horizontais, barra segmentada
 * e linha no tempo —, e escrevê-las à mão custa menos que carregar 300 KB de
 * biblioteca para usar 5% dela.
 *
 * Regras que valem para todas (docs/05-identidade-visual.md):
 * - um eixo só;
 * - marca fina, ponta arredondada de 4px, 2px de respiro entre preenchimentos;
 * - grade e eixo recessivos; o dado é a coisa mais escura da tela;
 * - texto em tinta, nunca na cor da série;
 * - nada comunicado só por cor: sempre rótulo junto;
 * - tudo que tem hover também tem <title>, para leitor de tela e para toque.
 */

const NS = "http://www.w3.org/2000/svg";

export const fmt = new Intl.NumberFormat("pt-BR");

function el(tag, attrs = {}, texto) {
  const node = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v !== undefined && v !== null) node.setAttribute(k, String(v));
  }
  if (texto !== undefined) node.textContent = texto;
  return node;
}

function titulo(node, texto) {
  node.append(el("title", {}, texto));
  return node;
}

/** Largura real do contêiner, em pixels de CSS.
 *
 *  Sem isto, o SVG é desenhado num viewBox fixo de 900 e o navegador o encolhe
 *  para caber — encolhendo o texto junto. Num cartão de 330px, um rótulo de
 *  13px vira 5px e fica ilegível. Medindo o contêiner, 1 unidade do SVG é 1
 *  pixel e o texto sai no tamanho pedido. */
function larguraDe(destino, minimo = 320) {
  return Math.max(Math.floor(destino.getBoundingClientRect().width) || 900, minimo);
}

/** Mede texto de verdade, em vez de estimar por número de caracteres.
 *
 *  Estimar por média falha justamente nos rótulos longos, que são os que
 *  precisam ser cortados: uma linha cheia de "m" e "ç" passa da calha e vaza
 *  pela borda esquerda do gráfico. O canvas resolve isso com precisão e sem
 *  tocar no DOM. */
const _regua = document.createElement("canvas").getContext("2d");
let _fonteRegua = "";

function medir(texto, fonte) {
  if (_fonteRegua !== fonte) {
    _regua.font = fonte;
    _fonteRegua = fonte;
  }
  return _regua.measureText(texto).width;
}

/** Corta o rótulo que não cabe na calha reservada, preservando o texto
 *  completo no <title> (tooltip e leitor de tela). Rótulo cortado é melhor
 *  que rótulo saindo pela borda do gráfico. */
function encurtar(texto, larguraDisponivel, fonte) {
  if (medir(texto, fonte) <= larguraDisponivel) return texto;
  let corte = texto.length;
  while (corte > 1 && medir(`${texto.slice(0, corte).trimEnd()}…`, fonte) > larguraDisponivel) {
    corte -= 1;
  }
  return `${texto.slice(0, corte).trimEnd()}…`;
}

/** Fonte efetiva dos rótulos, lida do CSS para a medição bater com o desenho. */
function fonteDosRotulos(destino) {
  const estilo = getComputedStyle(destino);
  return `13px ${estilo.fontFamily || "sans-serif"}`;
}

function svgBase(largura, altura, rotulo) {
  const svg = el("svg", {
    viewBox: `0 0 ${largura} ${altura}`,
    width: "100%",
    height: altura,
    role: "img",
    "aria-label": rotulo,
    preserveAspectRatio: "xMinYMin meet",
  });
  svg.classList.add("grafico");
  return svg;
}

/** Barras horizontais, uma série. A forma certa para ranking de categorias
 *  com rótulos longos — que é o caso de quase tudo neste painel. */
export function barrasHorizontais(destino, dados, opcoes = {}) {
  const {
    alturaBarra = 22,
    espacamento = 12,
    cor = "var(--serie-1)",
    sufixo = "",
    total = null,
  } = opcoes;

  destino.replaceChildren();
  if (!dados.length) {
    destino.append(vazio("Nenhum dado para o filtro atual."));
    return;
  }

  const largura = larguraDe(destino);
  // A calha de rótulos acompanha a largura disponível, com teto: passando de
  // 40% da área, sobra pouco espaço para a barra e o gráfico deixa de comparar.
  const larguraRotulo = Math.min(opcoes.larguraRotulo ?? 260, Math.floor(largura * 0.4));
  const fonte = fonteDosRotulos(destino);
  const margemDireita = 56;
  const altura = dados.length * (alturaBarra + espacamento) + espacamento;
  const maximo = Math.max(...dados.map((d) => d.valor), 1);
  const escala = (largura - larguraRotulo - margemDireita) / maximo;

  const svg = svgBase(largura, altura, opcoes.rotulo || "Gráfico de barras");

  dados.forEach((d, i) => {
    const y = espacamento + i * (alturaBarra + espacamento);
    const comprimento = Math.max(d.valor * escala, d.valor > 0 ? 3 : 0);
    const parte = total ? ` · ${Math.round((d.valor / total) * 100)}% de ${fmt.format(total)}` : "";

    const grupo = el("g", { class: "barra" });
    grupo.append(
      el("text", {
        x: larguraRotulo - 12,
        y: y + alturaBarra / 2,
        "text-anchor": "end",
        "dominant-baseline": "central",
        class: "rotulo-categoria",
      }, encurtar(d.rotulo, larguraRotulo - 12, fonte))
    );
    grupo.append(
      el("rect", {
        x: larguraRotulo,
        y,
        width: comprimento,
        height: alturaBarra,
        rx: 4,
        fill: d.cor || cor,
      })
    );
    grupo.append(
      el("text", {
        x: larguraRotulo + comprimento + 10,
        y: y + alturaBarra / 2,
        "dominant-baseline": "central",
        class: "valor-barra",
      }, `${fmt.format(d.valor)}${sufixo}`)
    );
    titulo(grupo, `${d.rotulo}: ${fmt.format(d.valor)}${sufixo}${parte}`);
    svg.append(grupo);
  });

  destino.append(svg);
}

/** Barra única dividida em partes. Usada para o resultado do credenciamento:
 *  duas categorias não justificam um gráfico inteiro, mas justificam ver a
 *  proporção de uma vez. */
export function barraSegmentada(destino, partes, opcoes = {}) {
  const { altura = 40 } = opcoes;
  destino.replaceChildren();

  const total = partes.reduce((s, p) => s + p.valor, 0);
  if (!total) {
    destino.append(vazio("Nenhum dado para o filtro atual."));
    return;
  }

  const largura = larguraDe(destino);
  const respiro = 2; // 2px de superfície entre preenchimentos vizinhos
  const svg = svgBase(largura, altura, opcoes.rotulo || "Composição");

  let x = 0;
  partes.forEach((p, i) => {
    const bruta = (p.valor / total) * largura;
    const w = Math.max(bruta - (i < partes.length - 1 ? respiro : 0), 0);
    const grupo = el("g");
    grupo.append(
      el("rect", { x, y: 0, width: w, height: altura, rx: 4, fill: p.cor })
    );
    if (w > 56) {
      grupo.append(
        el("text", {
          x: x + 12,
          y: altura / 2,
          "dominant-baseline": "central",
          class: "valor-em-barra",
        }, fmt.format(p.valor))
      );
    }
    titulo(grupo, `${p.rotulo}: ${fmt.format(p.valor)} de ${fmt.format(total)}`);
    svg.append(grupo);
    x += bruta;
  });

  destino.append(svg);
}

/** Linha no tempo. Um eixo, marcador em cada ponto, rótulo só nos extremos. */
export function linhaTempo(destino, pontos, opcoes = {}) {
  destino.replaceChildren();
  if (pontos.length < 2) {
    destino.append(
      vazio(
        pontos.length === 1
          ? "Só há um dia com respostas — a evolução aparece a partir do segundo."
          : "Nenhum dado para o filtro atual."
      )
    );
    return;
  }

  const largura = larguraDe(destino);
  const altura = 220;
  const margem = { topo: 20, direita: 24, baixo: 40, esquerda: 44 };
  const maximo = Math.max(...pontos.map((p) => p.valor), 1);
  const larguraUtil = largura - margem.esquerda - margem.direita;
  const alturaUtil = altura - margem.topo - margem.baixo;

  const x = (i) => margem.esquerda + (i / (pontos.length - 1)) * larguraUtil;
  const y = (v) => margem.topo + alturaUtil - (v / maximo) * alturaUtil;

  const svg = svgBase(largura, altura, opcoes.rotulo || "Série no tempo");

  // Grade horizontal recessiva, poucos níveis.
  const niveis = 4;
  for (let i = 0; i <= niveis; i++) {
    const valor = (maximo / niveis) * i;
    svg.append(
      el("line", {
        x1: margem.esquerda, x2: largura - margem.direita,
        y1: y(valor), y2: y(valor), class: "grade",
      })
    );
    svg.append(
      el("text", {
        x: margem.esquerda - 10, y: y(valor),
        "text-anchor": "end", "dominant-baseline": "central", class: "tick",
      }, fmt.format(Math.round(valor)))
    );
  }

  const d = pontos.map((p, i) => `${i ? "L" : "M"}${x(i)},${y(p.valor)}`).join(" ");
  svg.append(el("path", { d, class: "linha", fill: "none", stroke: "var(--serie-1)" }));

  pontos.forEach((p, i) => {
    const marca = el("circle", { cx: x(i), cy: y(p.valor), r: 5, fill: "var(--serie-1)", class: "marcador" });
    svg.append(titulo(marca, `${p.rotulo}: ${fmt.format(p.valor)}`));
  });

  // Rótulo só nos extremos: número em todo ponto polui.
  [0, pontos.length - 1].forEach((i) => {
    svg.append(
      el("text", {
        x: x(i), y: altura - 14,
        "text-anchor": i === 0 ? "start" : "end", class: "tick",
      }, pontos[i].rotulo)
    );
  });

  destino.append(svg);
}

function vazio(mensagem) {
  const p = document.createElement("p");
  p.className = "sem-dado";
  p.textContent = mensagem;
  return p;
}

/** Tabela equivalente a um gráfico — exigida pelas regras de acessibilidade. */
export function tabelaEquivalente(dados, cabecalhos = ["Categoria", "Total"]) {
  const tabela = document.createElement("table");
  const thead = document.createElement("thead");
  const trh = document.createElement("tr");
  cabecalhos.forEach((c, i) => {
    const th = document.createElement("th");
    th.scope = "col";
    th.textContent = c;
    if (i > 0) th.className = "num";
    trh.append(th);
  });
  thead.append(trh);
  const tbody = document.createElement("tbody");
  dados.forEach((d) => {
    const tr = document.createElement("tr");
    const td = document.createElement("td");
    td.textContent = d.rotulo;
    const tdv = document.createElement("td");
    tdv.className = "num";
    tdv.textContent = fmt.format(d.valor);
    tr.append(td, tdv);
    tbody.append(tr);
  });
  tabela.append(thead, tbody);
  return tabela;
}
