# ADR 0006 — Porta de entrada no painel

- **Data:** 2026-07-30
- **Situação:** aceita
- **Contexto de:** [ADR 0005](0005-painel-publico-no-github-pages.md), que segue valendo

## Contexto

O painel está no ar em endereço público (ADR 0005). A coordenação pediu uma
tela de usuário e senha antes do painel: o link circula por mensagem e acaba
onde não foi convidado, e uma página que abre direto não deixa claro que aquilo
tem dono.

A hospedagem é o GitHub Pages, que serve arquivo estático. **Não há servidor
para conferir credencial.**

## Decisão

Entra uma tela de entrada em `dashboard/index.html`, e o painel passa para
`dashboard/painel.html`. Quem não entrou é mandado de volta antes de a página
aparecer. A sessão dura 12 horas e fica no `localStorage` do navegador.

**Isto é uma cortina, não uma fechadura.** A distinção não é detalhe de
implementação, é o que define o que pode e o que não pode passar por aqui:

- a conferência roda no navegador de quem está do outro lado — quem abrir o
  código-fonte vê como passar;
- `data/published/*.json` continua acessível por URL direta, sem passar pela
  porta: é de lá que o painel lê;
- o repositório é público, então os mesmos arquivos estão no GitHub.

A senha não fica escrita em texto puro: guardamos o SHA-256 de `usuario:senha`.
Num repositório público, a senha legível seria indexada por buscador junto com o
resto do código. O hash não impede quem quiser burlar — impede que a senha
escape por leitura casual.

## Consequências

**O que muda.** O link deixa de abrir sozinho. Quem recebe sem credencial vê
uma tela institucional e um pedido para falar com a coordenação.

**O que não muda, e é o que importa.** A regra de sigilo continua sendo a de
sempre, definida em `docs/06-governanca-e-lgpd.md` e cobrada por
`scripts/checar_publicacao.py`: **dado que não pode vazar não sai de
`data/processed/`.** A porta não é motivo para relaxar isso. Se algum dia for
preciso publicar coluna de identificação, a decisão é de hospedagem, não de
tela — e é outro ADR.

**Custo.** Duas páginas em vez de uma no pacote do site, o que já cobrou o seu
preço: a versão contra cache passou a valer para todas as páginas, e não só
para a inicial (`scripts/montar_site.py`). Há teste para isso.

## Alternativas consideradas

**Hospedagem com autenticação de verdade** (Cloudflare Access, Netlify Identity,
Vercel). Resolve de fato: ninguém vê painel nem dados sem credencial. Fica
registrado como o caminho a seguir se um dia o painel precisar mostrar dado
sigiloso. Não foi feito agora porque muda a infraestrutura, sai do GitHub Pages
e provavelmente custa — decisão maior do que o problema pedia.

**Repositório privado com Pages.** Fecha o caminho mais fácil de burlar, que é
ler o código no GitHub. Exige plano pago para o Pages continuar servindo.

**Nada.** Era o estado anterior. A coordenação pediu explicitamente a mudança.

## Como trocar a credencial

```bash
python -c "import hashlib;print(hashlib.sha256(b'usuario:senha').hexdigest())"
```

e substituir `CREDENCIAL` em `dashboard/assets/acesso.js`.
