/* ============================================================
   global.js — JavaScript compartilhado · Site Fran Vieira
   Carregue em todas as páginas antes do </body>:
   <script src="../global.js" defer></script>
   ============================================================ */

/* ------------------------------------------------------------
   1. SCROLL REVEAL — IntersectionObserver para .reveal e .reveal-left
   ------------------------------------------------------------ */
function initScrollReveal() {
    var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
            if (entry.isIntersecting) entry.target.classList.add('visible');
        });
    }, { threshold: 0.12 });

    document.querySelectorAll('.reveal, .reveal-left').forEach(function (el) {
        observer.observe(el);
    });
}

/* ------------------------------------------------------------
   2. CONTADOR ANIMADO — elementos com [data-target]
   Usado na secção de Prova Social da comunidade-aplique.
   ------------------------------------------------------------ */
function initCounters() {
    var counters = document.querySelectorAll('[data-target]');
    if (!counters.length) return;

    var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
            if (!entry.isIntersecting) return;

            var el = entry.target;
            var target = parseInt(el.dataset.target, 10);
            var suffix = el.dataset.suffix || '';
            var dur = 1800;
            var step = Math.ceil(target / (dur / 16));
            var current = 0;

            var timer = setInterval(function () {
                current = Math.min(current + step, target);
                el.textContent = current + suffix;
                if (current >= target) clearInterval(timer);
            }, 16);

            observer.unobserve(el);
        });
    }, { threshold: 0.5 });

    counters.forEach(function (el) { observer.observe(el); });
}

/* ------------------------------------------------------------
   3. ANO NO FOOTER — preenche o elemento com id="ano-footer"
   ------------------------------------------------------------ */
function initFooterYear() {
    var el = document.getElementById('ano-footer');
    if (el) el.textContent = new Date().getFullYear();
}

/* ------------------------------------------------------------
   4. INICIALIZAÇÃO DO AOS — só se a biblioteca estiver presente
   ------------------------------------------------------------ */
function initAOS() {
    if (typeof AOS !== 'undefined') {
        AOS.init({ once: true, duration: 700, easing: 'ease-out-cubic' });
    }
}

/* ------------------------------------------------------------
   5. CHAMADA PRINCIPAL
   ------------------------------------------------------------ */
document.addEventListener('DOMContentLoaded', function () {
    initScrollReveal();
    initCounters();
    initFooterYear();
    initAOS();
});
