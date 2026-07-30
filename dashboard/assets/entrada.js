/* Tela de entrada: confere a credencial e abre o painel.
 *
 * Sobre a demora proposital no erro, ver o comentário em `errar()`.
 * Sobre o que esta porta protege (e o que não protege), ver acesso.js.
 */

import { conferir, liberado, liberar } from "./acesso.js";

const $ = (sel) => document.querySelector(sel);

// Quem já entrou não precisa entrar de novo: vai direto para o painel.
if (liberado()) location.replace("painel.html");

const formulario = $("#entrar");
const aviso = $("#aviso-entrada");
const botao = $("#botao-entrar");

/** Erra devagar, de propósito.
 *
 *  Resposta instantânea convida a tentar senha atrás de senha num laço. Um
 *  segundo não incomoda quem digitou errado uma vez e estraga a paciência de
 *  quem está chutando. (Isto atrasa a força bruta na tela; não substitui o que
 *  só um servidor faria — ver acesso.js.) */
async function errar(mensagem) {
  await new Promise((pronto) => setTimeout(pronto, 1000));
  aviso.textContent = mensagem;
  aviso.hidden = false;
  botao.disabled = false;
  botao.textContent = "Entrar";
  $("#senha").select();
}

formulario.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  aviso.hidden = true;
  botao.disabled = true;
  botao.textContent = "Conferindo…";

  const usuario = $("#usuario").value;
  const senha = $("#senha").value;

  if (!crypto?.subtle) {
    // A conferência usa SHA-256 do navegador, que só existe em contexto seguro.
    // Abrir o arquivo direto do disco (file://) cai aqui — e a mensagem precisa
    // dizer o que fazer, não só que não deu.
    await errar(
      "Esta página precisa ser aberta por um endereço https (ou localhost). " +
        "Aberta direto do arquivo, o navegador não deixa conferir a senha."
    );
    return;
  }

  try {
    if (await conferir(usuario, senha)) {
      liberar();
      location.replace("painel.html");
      return;
    }
  } catch (erro) {
    await errar(`Não foi possível conferir agora: ${erro}`);
    return;
  }

  await errar("Usuário ou senha não conferem.");
});
