/* Porta de entrada do painel.
 *
 * LEIA ANTES DE CONFIAR NISTO. Isto é uma cortina, não uma fechadura.
 *
 * O painel é uma página estática: não há servidor para conferir credencial, e
 * tudo o que este arquivo faz roda no navegador de quem está do outro lado.
 * Em outras palavras:
 *
 *   - quem abrir o código-fonte da página vê como passar;
 *   - `data/published/*.json` continua acessível por URL direta, sem passar
 *     por aqui — é de lá que o painel lê;
 *   - o repositório é público, então os mesmos dados estão no GitHub.
 *
 * Serve para o que foi pedido: evitar que o link caia em quem não deveria
 * abrir por acaso, e deixar claro a quem chega que o painel tem dono. Não
 * serve para proteger dado sigiloso — e é por isso que dado sigiloso não sai
 * de `data/processed/` (docs/06-governanca-e-lgpd.md, ADR 0006).
 *
 * A senha não fica escrita aqui em texto puro. Guardamos o SHA-256 de
 * "usuario:senha": num repositório público, a senha legível seria indexada por
 * buscador junto com o resto do código. O hash não impede quem quiser burlar,
 * mas impede que a senha vaze por leitura casual do repositório.
 *
 * Para trocar a credencial:
 *   python -c "import hashlib;print(hashlib.sha256(b'usuario:senha').hexdigest())"
 * e substitua CREDENCIAL abaixo.
 */

// SHA-256 de "mbm:<senha do comitê>".
const CREDENCIAL = "ea0b21c47284443e6ceece8482a492b766e745864258a56d122372886a54d05c";

const CHAVE = "redes-bahia-acesso";

// Meio dia de validade: cobre uma jornada de trabalho sem obrigar a entrar de
// novo a cada aba, e não deixa uma máquina compartilhada aberta para sempre.
const VALIDADE_HORAS = 12;

async function resumo(texto) {
  const bytes = new TextEncoder().encode(texto);
  const digerido = await crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(digerido)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

/** Confere usuário e senha. O usuário é comparado sem caixa nem espaço em volta:
 *  errar "MBM" por "mbm" não é tentativa de invasão, é teclado. */
export async function conferir(usuario, senha) {
  return (await resumo(`${String(usuario).trim().toLowerCase()}:${senha}`)) === CREDENCIAL;
}

export function liberar() {
  localStorage.setItem(CHAVE, String(Date.now() + VALIDADE_HORAS * 3600_000));
}

export function liberado() {
  const ate = Number(localStorage.getItem(CHAVE));
  if (!ate || Date.now() > ate) {
    localStorage.removeItem(CHAVE);
    return false;
  }
  return true;
}

export function sair() {
  localStorage.removeItem(CHAVE);
}
