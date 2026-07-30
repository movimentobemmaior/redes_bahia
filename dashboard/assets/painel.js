/* Página de estado da base.
 *
 * Lê apenas data/published/manifest.json — nunca os dados em si. É essa a
 * razão de o manifesto existir: dá para dizer se a base pode ser confiada
 * sem carregar uma linha sequer.
 */

const CAMINHO_MANIFESTO = "../data/published/manifest.json";

const TEXTO_STATUS = {
  aprovado: "Validação aprovada — nenhum problema encontrado",
  com_avisos: "Publicada com avisos — confira a lista abaixo",
  reprovado: "Reprovada — esta base não deveria estar publicada",
};

const fmtInteiro = new Intl.NumberFormat("pt-BR");

function formatarData(iso) {
  if (!iso) return "—";
  const [ano, mes, dia] = iso.slice(0, 10).split("-");
  return `${dia}/${mes}/${ano}`;
}

function diasDesde(iso) {
  const alvo = new Date(`${iso.slice(0, 10)}T00:00:00`);
  const hoje = new Date();
  hoje.setHours(0, 0, 0, 0);
  return Math.round((hoje - alvo) / 86400000);
}

function idadeEmTexto(iso) {
  const dias = diasDesde(iso);
  if (dias <= 0) return "atualizada hoje";
  if (dias === 1) return "atualizada ontem";
  return `atualizada há ${dias} dias`;
}

function elemento(tag, classe, texto) {
  const el = document.createElement(tag);
  if (classe) el.className = classe;
  if (texto !== undefined) el.textContent = texto;
  return el;
}

function preencherDestaque(m) {
  document.getElementById("data-atualizacao").textContent = formatarData(m.data_execucao);

  const origem = document.getElementById("origem");
  origem.textContent =
    `${idadeEmTexto(m.data_execucao)} · origem: ${m.fonte.arquivo}`;

  const selo = document.getElementById("selo-validacao");
  const status = m.validacao.status;
  selo.dataset.status = status;
  const detalhe = `${m.validacao.erros} erro(s), ${m.validacao.avisos} aviso(s)`;
  selo.querySelector(".selo-texto").textContent =
    `${TEXTO_STATUS[status] ?? status} (${detalhe})`;

  document.getElementById("procedencia").textContent =
    `Gerada em ${m.gerado_em} pelo pipeline ${m.versao_pipeline}, ` +
    `contrato versão ${m.versao_contrato}. SHA-256 da planilha: ${m.fonte.hash_sha256}.`;
}

function preencherCartoes(m) {
  const destino = document.getElementById("cartoes");
  for (const ds of m.datasets) {
    const cartao = elemento("article", "cartao");
    cartao.append(elemento("h3", null, ds.nome));

    const valor = elemento("p", "valor", fmtInteiro.format(ds.n_linhas));
    valor.append(elemento("span", "unidade", "linhas"));
    cartao.append(valor);

    cartao.append(
      elemento("p", "descricao", ds.descricao || `Aba “${ds.aba}” da planilha.`)
    );
    cartao.append(
      elemento(
        "p",
        "retido",
        `${ds.n_colunas_publicadas} coluna(s) publicada(s)` +
          (ds.colunas_omitidas_por_sigilo.length
            ? ` · ${ds.colunas_omitidas_por_sigilo.length} retida(s) por sigilo`
            : "")
      )
    );
    destino.append(cartao);
  }
}

function preencherProblemas(m) {
  const problemas = m.validacao.problemas ?? [];
  const tabela = document.getElementById("tabela-problemas");
  const vazio = document.getElementById("sem-problemas");

  if (!problemas.length) {
    tabela.hidden = true;
    vazio.hidden = false;
    return;
  }

  const corpo = tabela.querySelector("tbody");
  const ordenados = [...problemas].sort(
    (a, b) => (b.gravidade === "erro") - (a.gravidade === "erro")
  );

  for (const p of ordenados) {
    const linha = document.createElement("tr");

    const celulaTag = document.createElement("td");
    const tag = elemento("span", "tag", p.gravidade);
    tag.dataset.gravidade = p.gravidade;
    celulaTag.append(tag);
    linha.append(celulaTag);

    linha.append(elemento("td", null, p.dataset));
    linha.append(elemento("td", null, p.coluna ?? "—"));
    linha.append(elemento("td", null, p.mensagem));
    linha.append(elemento("td", "num", p.linhas_afetadas ? fmtInteiro.format(p.linhas_afetadas) : "—"));
    linha.append(elemento("td", null, (p.exemplos ?? []).join(", ") || "—"));

    corpo.append(linha);
  }
}

function preencherArquivos(m) {
  const lista = document.getElementById("arquivos");
  for (const caminho of m.arquivos.publicados) {
    const item = document.createElement("li");
    const link = document.createElement("a");
    link.href = `../${caminho}`;
    link.textContent = caminho.split("/").pop();
    item.append(link);
    lista.append(item);
  }
}

function configurarTema() {
  const botao = document.getElementById("alternar-tema");
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
    // Sem escolha salva, quem manda é o sistema — mas o rótulo do botão
    // precisa refletir isso, senão ele oferece "Modo escuro" já no escuro.
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
    const resposta = await fetch(CAMINHO_MANIFESTO, { cache: "no-store" });
    if (!resposta.ok) throw new Error(`HTTP ${resposta.status} ao buscar o manifesto`);
    const manifesto = await resposta.json();

    preencherDestaque(manifesto);
    preencherCartoes(manifesto);
    preencherProblemas(manifesto);
    preencherArquivos(manifesto);

    document.getElementById("carregando").hidden = true;
    document.getElementById("painel").hidden = false;
  } catch (erro) {
    document.getElementById("carregando").hidden = true;
    document.getElementById("erro").hidden = false;
    document.getElementById("erro-detalhe").textContent = String(erro);
  }
}

iniciar();
