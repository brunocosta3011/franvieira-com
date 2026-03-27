/* ============================================================
   script.js — JavaScript específico da página Linktree
   Carregar APÓS o global.js:
   <script src="../global.js" defer></script>
   <script src="./script.js" defer></script>
   ============================================================ */

/* ------------------------------------------------------------
   AOS INIT — configuração própria desta página (duration: 600)
   Sobrescreve o init padrão do global.js se necessário.
   ------------------------------------------------------------ */
document.addEventListener('DOMContentLoaded', function () {
    if (typeof AOS !== 'undefined') {
        AOS.init({ once: true, duration: 600 });
    }
});
