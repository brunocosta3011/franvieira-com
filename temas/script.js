/**
 * temas/script.js 
 * Lógica de busca, similaridade e integração com WhatsApp + Carrossel
 */

document.addEventListener('DOMContentLoaded', async () => {
    const themesGrid = document.getElementById('themes-grid');
    const searchInput = document.getElementById('theme-search');
    const suggestionEl = document.getElementById('search-suggestion');
    const emptyState = document.getElementById('empty-state');
    const btnConfirm = document.getElementById('btn-confirm');
    const btnCustom = document.getElementById('btn-custom');

    // Elementos do Modal
    const galleryModal = document.getElementById('gallery-modal');
    const carouselMediaContainer = document.getElementById('carousel-media-container');
    const modalThumbnails = document.getElementById('modal-thumbnails');
    const modalTitle = document.getElementById('modal-title');
    const closeGallery = document.getElementById('close-gallery');
    const btnConfirmModal = document.getElementById('btn-confirm-modal');
    const btnCustomModal = document.getElementById('btn-custom-modal');
    const prevBtn = document.getElementById('prev-media');
    const nextBtn = document.getElementById('next-media');
    const modalOverlay = galleryModal.querySelector('.modal-overlay');

    let allThemes = [];
    let selectedTheme = null;
    let fuse = null;
    let currentMediaIndex = 0;
    let currentThemeMedia = [];

    // 1. Carregar Dados
    try {
        // Adicionamos um timestamp para evitar cache e garantimos que o fetch seja relativo ao diretório atual
        const response = await fetch('themes.json?t=' + Date.now());
        if (!response.ok) throw new Error('Falha ao carregar themes.json (Status: ' + response.status + ')');
        
        allThemes = await response.json();
        
        if (typeof Fuse !== 'undefined') {
            fuse = new Fuse(allThemes, {
                keys: ['tema', 'tags', 'categoria'],
                threshold: 0.4,
                includeScore: true
            });
        }

        const params = new URLSearchParams(window.location.search);
        const query = params.get('q') || params.get('search');
        
        if (query) {
            searchInput.value = query;
            performSearch(query);
        } else {
            renderThemes(allThemes);
        }

    } catch (error) {
        console.error("Erro fatal:", error);
        themesGrid.innerHTML = `<div class="error-msg"><p>⚠️ Erro ao carregar catálogo.</p><small>${error.message}</small></div>`;
    }

    /**
     * Função auxiliar para construir caminhos seguros (URL encoded)
     * Resolve problemas com espaços, acentos e parênteses nos arquivos do WhatsApp.
     */
    function getSafePath(relativePath) {
        if (!relativePath || relativePath === 'fran-avatar.jpg' || relativePath === 'placeholder.jpg') return '../fran-avatar.jpg';
        
        let cleanPath = relativePath;

        // Codifica partes para evitar erros com espaços e acentos no Linux (servidor de produção)
        const parts = cleanPath.split('/').map(part => {
            if (part === '..') return '..';
            return encodeURIComponent(part);
        });
        
        return parts.join('/');
    }

    // 2. Renderização
    function renderThemes(themes, isSearch = false) {
        themesGrid.innerHTML = '';
        if (themes.length === 0) {
            themesGrid.style.display = 'none';
            emptyState.classList.remove('hidden');
            return;
        }

        themesGrid.style.display = 'grid';
        emptyState.classList.add('hidden');
        const fragment = document.createDocumentFragment();
        
        themes.forEach((theme) => {
            const item = theme.item || theme;
            const card = document.createElement('div');
            card.className = 'theme-card'; 
            
            // Ajustamos o caminho para a raiz e codificamos de forma segura
            const isVideo = /\.(mp4|webm|mov)$/i.test(item.imagem);
            const imgPath = getSafePath(item.imagem);
            
            let mediaHtml = isVideo ? 
                `<div class="video-placeholder"><span>${item.tema}</span></div>` :
                `<img src="${imgPath}" alt="${item.tema}" onerror="this.parentElement.style.display='none';">`;

            card.innerHTML = `
                <div class="selection-badge">✓</div>
                <div class="card-img-wrapper">
                    ${mediaHtml}
                </div>
                <div class="card-content">
                    <span class="card-tag">${item.categoria}</span>
                    <h3>${item.tema}</h3>
                </div>
            `;

            card.addEventListener('click', () => {
                selectTheme(item, card);
                openGallery(item);
            });

            fragment.appendChild(card);
            card.classList.add('is-visible');
        });
        themesGrid.appendChild(fragment);
    }

    function selectTheme(item, card) {
        document.querySelectorAll('.theme-card').forEach(c => c.classList.remove('selected'));
        selectedTheme = item;
        if (card) card.classList.add('selected');
    }

    // 3. Galeria (Carousel Modal)
    function openGallery(item) {
        modalTitle.textContent = item.tema;
        currentThemeMedia = item.galeria || [item.imagem];
        currentMediaIndex = 0;
        
        // Esconder setas se houver apenas 1 mídia
        const showNav = currentThemeMedia.length > 1;
        prevBtn.style.display = showNav ? 'flex' : 'none';
        nextBtn.style.display = showNav ? 'flex' : 'none';
        modalThumbnails.style.display = showNav ? 'flex' : 'none';

        renderThumbnails();
        updateCarousel();

        galleryModal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }

    function renderThumbnails() {
        modalThumbnails.innerHTML = '';
        currentThemeMedia.forEach((path, idx) => {
            const thumb = document.createElement('div');
            thumb.className = `thumb-item ${idx === 0 ? 'active' : ''}`;
            const isVideo = /\.(mp4|webm|mov)$/i.test(path);
            
            // Codificamos o caminho para a miniatura de forma segura
            const fullPath = getSafePath(path);
            
            // Para vídeo mostramos um ícone de Play
            thumb.innerHTML = isVideo ? 
                `<div class="video-thumb-icon"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg></div>` : 
                `<img src="${fullPath}" alt="thumb">`;
            
            thumb.addEventListener('click', () => {
                currentMediaIndex = idx;
                updateCarousel();
            });
            modalThumbnails.appendChild(thumb);
        });
    }

    function updateCarousel() {
        carouselMediaContainer.innerHTML = '';
        const path = currentThemeMedia[currentMediaIndex];
        const isVideo = /\.(mp4|webm|mov)$/i.test(path);
        const fullPath = getSafePath(path);

        if (isVideo) {
            carouselMediaContainer.innerHTML = `<video src="${fullPath}" controls autoplay muted loop></video>`;
        } else {
            carouselMediaContainer.innerHTML = `<img src="${fullPath}" alt="media">`;
        }

        document.querySelectorAll('.thumb-item').forEach((t, i) => {
            t.classList.toggle('active', i === currentMediaIndex);
            if (i === currentMediaIndex) t.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
        });
    }

    function navigate(dir) {
        if (currentThemeMedia.length <= 1) return;
        currentMediaIndex = (currentMediaIndex + dir + currentThemeMedia.length) % currentThemeMedia.length;
        updateCarousel();
    }

    prevBtn.addEventListener('click', () => navigate(-1));
    nextBtn.addEventListener('click', () => navigate(1));

    document.addEventListener('keydown', (e) => {
        if (galleryModal.classList.contains('hidden')) return;
        if (e.key === 'ArrowLeft') navigate(-1);
        if (e.key === 'ArrowRight') navigate(1);
        if (e.key === 'Escape') closeModal();
    });

    function closeModal() {
        galleryModal.classList.add('hidden');
        carouselMediaContainer.innerHTML = ''; 
        document.body.style.overflow = '';
    }

    closeGallery.addEventListener('click', closeModal);
    modalOverlay.addEventListener('click', closeModal);
    btnConfirmModal.addEventListener('click', () => {
        closeModal();
        openWhatsApp('confirm');
    });
    btnCustomModal.addEventListener('click', () => {
        closeModal();
        openWhatsApp('custom');
    });

    // 4. Busca
    function performSearch(query) {
        if (!query || !fuse) {
            suggestionEl.textContent = '';
            renderThemes(allThemes);
            return;
        }

        const results = fuse.search(query);
        if (results.length > 0) {
            const bestMatch = results[0];
            if (bestMatch.score > 0.1 && bestMatch.item.tema.toLowerCase() !== query.toLowerCase()) {
                suggestionEl.innerHTML = `Resultados para: <strong>${bestMatch.item.tema}</strong>`;
            } else {
                suggestionEl.textContent = '';
            }
        } else {
            suggestionEl.textContent = 'Nada encontrado.';
        }
        renderThemes(results);
    }

    searchInput.addEventListener('input', (e) => performSearch(e.target.value.trim()));

    // 5. WhatsApp
    function openWhatsApp(actionType) {
        const phoneNumber = "553498077504";
        const themeName = selectedTheme ? selectedTheme.tema : (searchInput.value || "um tema personalizado");
        let message = "";

        if (actionType === 'confirm') {
            message = `Fran! Vi as fotos no site e escolhi o tema *${themeName}*! Podemos seguir!`;
        } else {
            message = `Oi Fran! Gostei do tema *${themeName}*, mas queria algo personalizado nesse estilo. Você faz?`;
        }
        
        const fullUrl = `https://wa.me/${phoneNumber}?text=${encodeURIComponent(message)}`;
        
        // No mobile, redirecionar via location.href é muito mais estável para abrir o app
        if (/Android|iPhone|iPad|iPod/i.test(navigator.userAgent)) {
            window.location.href = fullUrl;
        } else {
            window.open(fullUrl, '_blank');
        }
    }

    btnConfirm.addEventListener('click', () => openWhatsApp('confirm'));
    btnCustom.addEventListener('click', () => openWhatsApp('custom'));
});
