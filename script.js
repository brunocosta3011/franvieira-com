/* ============================================================
   script.js — Script global do site Fran Vieira
   Importar em todas as páginas antes do </body>:
   <script src="/script.js" defer></script>
   ============================================================ */

/* ------------------------------------------------------------
   Scroll Reveal — IntersectionObserver
   Observa elementos com .reveal e .reveal-left e adiciona
   .visible quando entram na viewport (threshold: 12%).
   ------------------------------------------------------------ */
document.addEventListener('DOMContentLoaded', function () {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(el => {
      if (el.isIntersecting) {
        el.target.classList.add('visible');
      }
    });
  }, { threshold: 0.12 });

  document.querySelectorAll('.reveal, .reveal-left').forEach(el => observer.observe(el));

  /* ----------------------------------------------------------
     Cursor Personalizado — Desktop / hover apenas
     Cria um ponto de 12px que segue o mouse com ~80ms de lag
     usando interpolação linear (lerp) via requestAnimationFrame.
     ---------------------------------------------------------- */
  const isDesktopHover =
    window.matchMedia('(hover: hover) and (min-width: 768px)').matches;

  if (isDesktopHover) {
    const dot = document.createElement('div');
    dot.className = 'cursor-dot';
    document.body.appendChild(dot);

    let tx = window.innerWidth / 2;
    let ty = window.innerHeight / 2;
    let cx = tx;
    let cy = ty;
    const LERP = 0.5; // fator de interpolação ≈ 17ms de lag (responsivo)

    document.addEventListener('mousemove', (e) => {
      tx = e.clientX;
      ty = e.clientY;
    });

    // Oculta cursor nativo apenas após o primeiro movimento
    document.addEventListener('mousemove', function hideCursor() {
      document.documentElement.style.cursor = 'none';
      document.removeEventListener('mousemove', hideCursor);
    }, { once: true });

    (function animateCursor() {
      cx += (tx - cx) * LERP;
      cy += (ty - cy) * LERP;
      dot.style.left = cx + 'px';
      dot.style.top = cy + 'px';
      requestAnimationFrame(animateCursor);
    })();
  }
});
