/* Mapa coroplético em SVG puro.
 *
 * Mesma disciplina do resto do painel (graficos.js): sem biblioteca, sem rede,
 * sem build. Um mapa de contagem por unidade territorial não precisa de tiles
 * nem de projeção geodésica — precisa de um contorno, uma escala e um rótulo.
 *
 * Duas regras de acessibilidade valem aqui com força maior que nos gráficos de
 * barra, porque mapa é o formato mais fácil de comunicar só por cor:
 *
 * - a unidade com dado recebe rótulo escrito com o número, não só o tom;
 * - a tabela equivalente vem sempre junto, e não como opção escondida.
 *
 * A malha é um GeoJSON simplificado gerado por scripts/gerar_malhas.py. Cada
 * feição carrega `chave` (UF ou código IBGE) e `nome`.
 */

import { fmt } from "./graficos.js";

const NS = "http://www.w3.org/2000/svg";

// Rampa sequencial dos tokens (design/tokens/tokens.css), sem o primeiro passo.
// `--seq-100` fica perto demais da superfície: uma unidade com uma resposta
// saía indistinguível das dezenas sem nenhuma, que é justamente a diferença
// que o mapa existe para mostrar. O passo mais claro fica reservado ao vazio.
const RAMPA = ["var(--seq-250)", "var(--seq-400)", "var(--seq-550)", "var(--seq-700)"];

function el(tag, attrs = {}, texto) {
  const node = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v !== undefined && v !== null) node.setAttribute(k, String(v));
  }
  if (texto !== undefined) node.textContent = texto;
  return node;
}

/** Compara nomes de lugar ignorando acento, caixa e espaço sobrando.
 *
 *  O formulário devolve "Bahia" e a malha guarda "BA" e "Bahia"; a planilha de
 *  município vai devolver "Feira de Santana" e a malha guarda o código IBGE e o
 *  nome. Casar pelos dois lados evita depender de qual deles a planilha usa. */
export function normalizar(valor) {
  return String(valor ?? "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .trim()
    .toLowerCase();
}

function extremos(features) {
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
  for (const f of features) {
    for (const anel of aneis(f.geometry)) {
      for (const [x, y] of anel) {
        if (x < minX) minX = x;
        if (x > maxX) maxX = x;
        if (y < minY) minY = y;
        if (y > maxY) maxY = y;
      }
    }
  }
  return { minX, maxX, minY, maxY };
}

function aneis(geometria) {
  return geometria.type === "MultiPolygon"
    ? geometria.coordinates.flat()
    : geometria.coordinates;
}

/** O anel de maior área — na prática, a parte continental da unidade. */
function maiorAnel(geometria) {
  let maior = null;
  let maiorArea = -1;
  for (const anel of aneis(geometria)) {
    const a = Math.abs(areaAssinada(anel));
    if (a > maiorArea) {
      maiorArea = a;
      maior = anel;
    }
  }
  return maior;
}

/** Ponto representativo da feição: centroide do maior anel.
 *
 *  Centroide da feição inteira cairia no mar em estados com muitas ilhas, e
 *  fora do território em unidades côncavas. O maior anel é o continente. */
function ancora(geometria) {
  return centroide(maiorAnel(geometria));
}

function areaAssinada(anel) {
  let soma = 0;
  for (let i = 0, j = anel.length - 1; i < anel.length; j = i++) {
    soma += anel[j][0] * anel[i][1] - anel[i][0] * anel[j][1];
  }
  return soma / 2;
}

function centroide(anel) {
  const area = areaAssinada(anel);
  if (!area) return anel[0];
  let x = 0;
  let y = 0;
  for (let i = 0, j = anel.length - 1; i < anel.length; j = i++) {
    const f = anel[j][0] * anel[i][1] - anel[i][0] * anel[j][1];
    x += (anel[j][0] + anel[i][0]) * f;
    y += (anel[j][1] + anel[i][1]) * f;
  }
  return [x / (6 * area), y / (6 * area)];
}

/** Faixas de classe por intervalo igual sobre o máximo.
 *
 *  Quantil seria melhor com muitas unidades, mas aqui a maioria das unidades
 *  tem zero: o quantil colocaria quase tudo na mesma faixa e apagaria a única
 *  diferença que interessa. Com intervalo igual, uma unidade com uma resposta
 *  já se separa do vazio. */
function faixas(maximo) {
  const passos = Math.min(RAMPA.length, Math.max(maximo, 1));
  const largura = maximo / passos;
  return Array.from({ length: passos }, (_, i) => ({
    de: i === 0 ? 1 : Math.floor(i * largura) + 1,
    ate: Math.round((i + 1) * largura),
    cor: RAMPA[RAMPA.length - passos + i],
  }));
}

function faixaDe(valor, escala) {
  if (!valor) return null;
  return escala.find((f) => valor >= f.de && valor <= f.ate) ?? escala[escala.length - 1];
}

/** Enquadramento: o que interessa, com folga, e não a malha inteira.
 *
 *  Desenhar o Brasil todo para mostrar duas unidades do Nordeste gasta meia
 *  tela de território vazio e encolhe justamente a parte que tem dado. O
 *  recorte acompanha os dados: se amanhã chegar uma resposta do Amazonas, o
 *  quadro se abre sozinho. As unidades de fora continuam desenhadas — o SVG as
 *  corta na borda, o que dá o contorno vizinho e a sensação de continuidade.
 *
 *  A folga é proporcional ao próprio recorte, com um piso em graus: sem o piso,
 *  uma única unidade pequena viria colada nas bordas. */
function recorte(features, valores, destaque) {
  const relevantes = features.filter((f) => {
    const chave = normalizar(f.properties.chave);
    const nome = normalizar(f.properties.nome);
    if (destaque && normalizar(destaque) === chave) return true;
    return Boolean(valores.get(chave) ?? valores.get(nome));
  });

  // Só o anel principal de cada unidade entra no enquadramento. Pernambuco
  // carrega Fernando de Noronha, 400 km mar adentro: incluir a ilha no cálculo
  // dobraria o quadro para mostrar um ponto do tamanho de um pixel.
  const caixa = extremos(
    (relevantes.length ? relevantes : features).map((f) => ({
      geometry: { type: "Polygon", coordinates: [maiorAnel(f.geometry)] },
    }))
  );
  const folgaX = Math.max((caixa.maxX - caixa.minX) * 0.18, 1.2);
  const folgaY = Math.max((caixa.maxY - caixa.minY) * 0.18, 1.2);
  const total = extremos(features);

  return {
    minX: Math.max(caixa.minX - folgaX, total.minX),
    maxX: Math.min(caixa.maxX + folgaX, total.maxX),
    minY: Math.max(caixa.minY - folgaY, total.minY),
    maxY: Math.min(caixa.maxY + folgaY, total.maxY),
  };
}

/**
 * Desenha o mapa.
 *
 * @param destino  elemento que recebe o SVG
 * @param malha    GeoJSON já carregado
 * @param valores  Map de chave normalizada -> número
 * @param opcoes   { rotulo, destaque, unidade, maxRotulos }
 */
export function mapaCoropletico(destino, malha, valores, opcoes = {}) {
  const { rotulo = "Mapa", destaque = "", unidade = "organizações", maxRotulos = 8 } = opcoes;

  destino.replaceChildren();
  const features = malha?.features ?? [];
  if (!features.length) {
    const p = document.createElement("p");
    p.className = "sem-dado";
    p.textContent = "A malha do mapa não pôde ser carregada.";
    destino.append(p);
    return;
  }

  const largura = Math.max(Math.floor(destino.getBoundingClientRect().width) || 640, 280);
  const { minX, maxX, minY, maxY } = recorte(features, valores, destaque);

  // Equirretangular com correção de cosseno na latitude média: numa faixa de
  // 40° o erro de forma é pequeno e a leitura é a de um mapa, não a de um
  // retângulo esticado. Mercator não traria nada aqui e distorceria a área.
  const fatorX = Math.cos(((minY + maxY) / 2) * (Math.PI / 180));
  const larguraGeo = (maxX - minX) * fatorX;
  const alturaGeo = maxY - minY;
  const margem = 12;
  const escalaMapa = (largura - margem * 2) / larguraGeo;
  const altura = Math.round(alturaGeo * escalaMapa) + margem * 2;

  const px = (lon) => margem + (lon - minX) * fatorX * escalaMapa;
  const py = (lat) => margem + (maxY - lat) * escalaMapa;

  const caminho = (geometria) =>
    aneis(geometria)
      .map((anel) => anel.map(([x, y], i) => `${i ? "L" : "M"}${px(x).toFixed(1)},${py(y).toFixed(1)}`).join("") + "Z")
      .join("");

  const maximo = Math.max(0, ...valores.values());
  const escala = faixas(maximo);

  const svg = el("svg", {
    viewBox: `0 0 ${largura} ${altura}`,
    width: "100%",
    height: altura,
    role: "img",
    "aria-label": rotulo,
    preserveAspectRatio: "xMidYMid meet",
  });
  svg.classList.add("mapa");

  const comDado = [];

  for (const f of features) {
    const chave = normalizar(f.properties.chave);
    const nome = f.properties.nome ?? f.properties.chave;
    const valor = valores.get(chave) ?? valores.get(normalizar(nome)) ?? 0;
    const faixa = faixaDe(valor, escala);

    const forma = el("path", {
      d: caminho(f.geometry),
      class: valor ? "area-mapa area-com-dado" : "area-mapa",
      // Unidade sem resposta usa a cor da grade, não a da superfície: precisa
      // ficar visível como contexto — o vizinho existe, só não tem ninguém —
      // sem nunca chegar perto do primeiro passo da rampa.
      fill: faixa ? faixa.cor : "var(--grade)",
    });
    forma.append(el("title", {}, `${nome}: ${fmt.format(valor)} ${valor === 1 ? unidade.replace(/s$/, "") : unidade}`));
    svg.append(forma);

    if (valor) comDado.push({ nome, valor, ponto: ancora(f.geometry) });
    if (destaque && normalizar(destaque) === chave) {
      svg.append(
        el("path", { d: caminho(f.geometry), class: "area-destaque", fill: "none" })
      );
    }
  }

  // Rótulo escrito nas unidades com dado — é o que impede o mapa de comunicar
  // só por cor. Acima de `maxRotulos` a tela vira sopa de letras: aí ficam os
  // maiores, e o resto continua no <title> e na tabela.
  comDado
    .sort((a, b) => b.valor - a.valor)
    .slice(0, maxRotulos)
    .forEach(({ nome, valor, ponto }) => {
      const [lon, lat] = ponto;
      // O rótulo é desenhado com halo da cor da superfície (paint-order no CSS)
      // em vez de trocar de cor conforme o tom do preenchimento: assim ele
      // continua legível sobre qualquer passo da rampa e nos dois modos, sem o
      // painel ter que saber qual passo é escuro em qual tema.
      const grupo = el("g", { class: "rotulo-mapa" });
      grupo.append(
        el("text", { x: px(lon), y: py(lat) - 3, "text-anchor": "middle", class: "rotulo-mapa-valor" },
          fmt.format(valor))
      );
      grupo.append(
        el("text", { x: px(lon), y: py(lat) + 11, "text-anchor": "middle", class: "rotulo-mapa-nome" }, nome)
      );
      svg.append(grupo);
    });

  destino.append(svg);
  destino.append(legenda(escala, maximo, unidade));
}

function legenda(escala, maximo, unidade) {
  const caixa = document.createElement("div");
  caixa.className = "legenda-mapa";
  if (!maximo) {
    caixa.textContent = "Nenhuma organização no recorte atual.";
    return caixa;
  }

  const passos = document.createElement("div");
  passos.className = "legenda-mapa-passos";
  for (const f of escala) {
    const item = document.createElement("span");
    item.className = "legenda-mapa-passo";
    const cor = document.createElement("i");
    cor.style.background = f.cor;
    item.append(cor, document.createTextNode(f.de === f.ate ? String(f.de) : `${f.de}–${f.ate}`));
    passos.append(item);
  }
  const texto = document.createElement("span");
  texto.className = "legenda-mapa-titulo";
  texto.textContent = unidade;
  caixa.append(texto, passos);
  return caixa;
}
