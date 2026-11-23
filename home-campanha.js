/* home-campanha.js — campanha "Esquenta Black Friday" da home (index.html).
   TEMPORÁRIO: remover depois de 27/11/2026 (ver docs/plans/2026-11-12-esquenta-black-friday.md, T-07).

   Adiciona a classe "modo-campanha" em <html> enquanto a campanha estiver valendo.
   O CSS (home.css, bloco "Campanha") esconde Destaque/Curso/Mentoria e mostra o cartão da campanha.
   Sem JavaScript a home aparece no modo normal.

   Preview/validação:  ?modo=campanha  força a campanha;  ?modo=normal  força a home normal. */

/* Fim exclusivo da campanha: 28/11 00:00 em Brasília = 27/11 23:59:59 incluso (estendida em 23/11, de 23/11 para 27/11). */
var CAMPANHA_ATE = '2026-11-28T00:00:00-03:00';

function campanhaAtiva(agora, busca) {
    if (/[?&]modo=campanha(&|$)/.test(busca)) return true;
    if (/[?&]modo=normal(&|$)/.test(busca)) return false;
    return agora.getTime() < new Date(CAMPANHA_ATE).getTime();
}

if (typeof document !== 'undefined' && campanhaAtiva(new Date(), window.location.search)) {
    document.documentElement.classList.add('modo-campanha');
}

if (typeof module !== 'undefined') module.exports = { campanhaAtiva: campanhaAtiva };
