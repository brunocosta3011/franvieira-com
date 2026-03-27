/* ============================================================
   script.js — JavaScript específico da página Comunidade do Aplique
   Carregar APÓS o global.js:
   <script src="../global.js" defer></script>
   <script src="./script.js" defer></script>
   ============================================================ */

/* ------------------------------------------------------------
   FLOATING BANNER — só no mobile, aparece após 5 segundos
   ------------------------------------------------------------ */
function initFloatingBanner() {
    if (window.innerWidth >= 768) return;

    setTimeout(function () {
        var banner = document.getElementById('floating-banner');
        if (banner) banner.style.display = 'block';
    }, 5000);

    var closeBtn = document.getElementById('close-banner');
    if (closeBtn) {
        closeBtn.addEventListener('click', function () {
            var banner = document.getElementById('floating-banner');
            if (banner) banner.style.display = 'none';
        });
    }
}

document.addEventListener('DOMContentLoaded', initFloatingBanner);
