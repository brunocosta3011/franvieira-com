/* ============================================================
   script.js — JavaScript específico da página Secagem Profissional
   Carregar APÓS o global.js:
   <script src="../global.js" defer></script>
   <script src="./script.js" defer></script>
   ============================================================ */

/* ------------------------------------------------------------
   FAQ ACCORDION — abre/fecha perguntas com acessibilidade
   ------------------------------------------------------------ */
function initFaq() {
    document.querySelectorAll('.faq-question').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var item = btn.closest('.faq-item');
            var isOpen = item.classList.contains('open');

            // Fecha todos
            document.querySelectorAll('.faq-item').forEach(function (el) {
                el.classList.remove('open');
                el.querySelector('.faq-question').setAttribute('aria-expanded', 'false');
            });

            // Abre o clicado se estava fechado
            if (!isOpen) {
                item.classList.add('open');
                btn.setAttribute('aria-expanded', 'true');
            }
        });
    });
}

document.addEventListener('DOMContentLoaded', initFaq);
