/* Guarda do painel: roda antes de qualquer outra coisa em painel.html.
 *
 * O `<html>` chega com a classe `trancado`, que esconde o conteúdo pelo CSS.
 * Sem isso o painel apareceria por um instante antes do redirecionamento — o
 * bastante para ler os números, o que anularia a razão de existir da porta.
 *
 * Este arquivo é carregado no <head>, antes de painel.js: módulos executam na
 * ordem em que aparecem, então a decisão de mostrar ou mandar embora acontece
 * antes de o painel começar a buscar dados.
 */

import { liberado } from "./acesso.js";

if (liberado()) {
  document.documentElement.classList.remove("trancado");
} else {
  // replace e não href: quem foi barrado não deve voltar ao painel apertando
  // "voltar" — voltaria para uma tela que o porteiro esconde, e pareceria erro.
  location.replace("./");
}
