/**
 * Gamarra Store Frontend JavaScript
 * Maneja la carga y visualización de productos
 */

const API_BASE_URL = 'http://localhost:8000/api';
let currentCategory = 'all';
let allProducts = [];

// ===== INICIALIZACIÓN =====
document.addEventListener('DOMContentLoaded', () => {
    console.log('🛍️ Gamarra Store initialized');

    setupEventListeners();
    loadProducts();
    setupStockSync();
});

// ===== EVENT LISTENERS =====
function setupEventListeners() {
    // Botón de refresh
    const btnRefresh = document.getElementById('btnRefreshStore');
    if (btnRefresh) {
        btnRefresh.addEventListener('click', () => {
            loadProducts();
        });
    }

    // Navegación por categorías
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();

            // Update active state
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');

            // Filter products
            const category = link.dataset.category;
            currentCategory = category;

            // Update breadcrumb
            const categoryName = category === 'all' ? 'Todos los productos' : category;
            document.getElementById('currentCategory').textContent = categoryName;

            filterProducts(category);
        });
    });

    // Search functionality
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const searchTerm = e.target.value.toLowerCase();
            searchProducts(searchTerm);
        });
    }
}

// ===== CARGAR PRODUCTOS =====
async function loadProducts() {
    const productsGrid = document.getElementById('productsGrid');
    const emptyState = document.getElementById('emptyState');

    try {
        // Mostrar loading
        productsGrid.innerHTML = `
            <div class="loading-state">
                <div class="spinner"></div>
                <p>Cargando productos...</p>
            </div>
        `;

        // Fetch products from API
        const response = await fetch(`${API_BASE_URL}/products`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        allProducts = data.products || [];

        console.log(`✅ Loaded ${allProducts.length} products`);

        // Actualizar contador
        updateProductsCount(allProducts.length);

        // Renderizar productos
        if (allProducts.length === 0) {
            productsGrid.innerHTML = '';
            emptyState.style.display = 'block';
        } else {
            emptyState.style.display = 'none';
            renderProducts(allProducts);
        }

    } catch (error) {
        console.error('❌ Error loading products:', error);
        productsGrid.innerHTML = `
            <div class="loading-state">
                <p style="color: var(--danger-red);">❌ Error al cargar productos</p>
                <p style="color: var(--text-light); font-size: 0.9rem;">
                    Asegúrate de que el servidor esté corriendo en ${API_BASE_URL}
                </p>
            </div>
        `;
    }
}

// ===== RENDERIZAR PRODUCTOS =====
function renderProducts(products) {
    const productsGrid = document.getElementById('productsGrid');

    if (products.length === 0) {
        productsGrid.innerHTML = `
            <div class="empty-state" style="grid-column: 1 / -1;">
                <div class="empty-icon">🔍</div>
                <h3>No se encontraron productos</h3>
                <p>Intenta con otra categoría o búsqueda</p>
            </div>
        `;
        return;
    }

    productsGrid.innerHTML = products.map(product => createProductCard(product)).join('');
}

// ===== CREAR TARJETA DE PRODUCTO =====
function createProductCard(product) {
    // Calcular stock total de todas las variantes
    const stockTotal = product.total_stock || 0;
    const stockClass = stockTotal === 0 ? 'out-of-stock' : stockTotal < 10 ? 'low-stock' : '';
    const stockText = stockTotal === 0 ? 'Agotado' : `${stockTotal} disponibles`;
    const badgeText = stockTotal > 0 ? 'DISPONIBLE' : 'AGOTADO';
    const badgeClass = stockTotal > 0 ? '' : 'out-of-stock';

    // Emoji por categoría como placeholder
    const categoryEmoji = {
        'Polos': '👕',
        'Pantalones': '👖',
        'Camisas': '👔',
        'Accesorios': '🎩'
    };

    const emoji = categoryEmoji[product.category] || '📦';

    // Determinar si hay imagen real
    const hasImage = product.image_url && (product.image_url.includes('.png') || product.image_url.includes('http'));

    // Obtener tallas disponibles (con stock > 0)
    const availableSizes = product.variants
        .filter(v => v.stock_total > 0)
        .map(v => v.size)
        .join(', ');

    return `
        <div class="product-card" data-category="${product.category}" onclick="goToProductDetail('${product.sku}')" style="cursor: pointer;">
            <div class="product-image-container">
                ${hasImage
            ? `<img src="${product.image_url}" alt="${product.name}">`
            : `<div class="product-image-placeholder">${emoji}</div>`
        }
                <div class="product-badge ${badgeClass}">${badgeText}</div>
            </div>
            <div class="product-info">
                <div class="product-category">${product.category || 'General'}</div>
                <h3 class="product-name">${product.name}</h3>
                <div class="product-details">
                    ${availableSizes ? `<span class="product-detail">📏 Tallas: ${availableSizes}</span>` : ''}
                    ${product.color ? `<span class="product-detail">🎨 ${product.color}</span>` : ''}
                    <span class="product-detail">SKU: ${product.sku}</span>
                </div>
                <div class="product-footer">
                    <div class="product-price-container">
                        <span class="product-price-label">Precio</span>
                        <div class="product-price">S/ ${product.base_price.toFixed(2)}</div>
                    </div>
                    <div class="product-stock">
                        <div class="stock-badge ${stockClass}">
                            ${stockTotal > 0 ? '✅' : '❌'} ${stockText}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// ===== NAVEGAR A DETALLE DEL PRODUCTO =====
function goToProductDetail(sku) {
    window.location.href = `/product-detail?sku=${sku}`;
}

// ===== FILTRAR PRODUCTOS =====
function filterProducts(category) {
    console.log(`🔍 Filtering by category: ${category}`);

    if (category === 'all') {
        renderProducts(allProducts);
        updateProductsCount(allProducts.length);
    } else {
        const filtered = allProducts.filter(p => p.category === category);
        renderProducts(filtered);
        updateProductsCount(filtered.length);
    }
}

// ===== BUSCAR PRODUCTOS =====
function searchProducts(searchTerm) {
    if (!searchTerm) {
        filterProducts(currentCategory);
        return;
    }

    const filtered = allProducts.filter(p => {
        const matchesSearch =
            p.name.toLowerCase().includes(searchTerm) ||
            p.sku.toLowerCase().includes(searchTerm) ||
            (p.category && p.category.toLowerCase().includes(searchTerm)) ||
            (p.color && p.color.toLowerCase().includes(searchTerm));

        const matchesCategory = currentCategory === 'all' || p.category === currentCategory;

        return matchesSearch && matchesCategory;
    });

    renderProducts(filtered);
    updateProductsCount(filtered.length);
}

// ===== ACTUALIZAR CONTADOR =====
function updateProductsCount(count) {
    const countElement = document.getElementById('productsCount');
    if (countElement) {
        countElement.textContent = count;
    }
}

 / /   = = = = =   C O N E X I � N   S S E   P A R A   S T O C K   E N   T I E M P O   R E A L   = = = = = 
 f u n c t i o n   s e t u p S t o c k S y n c ( )   { 
         c o n s t   e v t S o u r c e   =   n e w   E v e n t S o u r c e ( A P I _ B A S E _ U R L   +   ' / a p i / s t r e a m / s t o c k ' ) ; 
         
         e v t S o u r c e . o n m e s s a g e   =   f u n c t i o n ( e v e n t )   { 
                 c o n s o l e . l o g ( ' =��  S i n c r o n i z a c i � n   d e   s t o c k   r e c i b i d a : ' ,   e v e n t . d a t a ) ; 
                 t r y   { 
                         c o n s t   d a t a   =   J S O N . p a r s e ( e v e n t . d a t a ) ; 
                         
                         / /   A c t u a l i z a r   a l l P r o d u c t s   e n   m e m o r i a 
                         a l l P r o d u c t s . f o r E a c h ( p   = >   { 
                                 c o n s t   v a r i a n t   =   p . v a r i a n t s . f i n d ( v   = >   v . s k u   = = =   d a t a . v a r i a n t _ s k u ) ; 
                                 i f   ( v a r i a n t )   { 
                                         v a r i a n t . s t o c k _ t o t a l   =   d a t a . n e w _ s t o c k ; 
                                         / /   R e c a l c u l a r   t o t a l _ s t o c k   d e l   p r o d u c t o   p a d r e 
                                         p . t o t a l _ s t o c k   =   p . v a r i a n t s . r e d u c e ( ( a c c ,   c u r r )   = >   a c c   +   c u r r . s t o c k _ t o t a l ,   0 ) ; 
                                 } 
                         } ) ; 
                         
                         / /   V o l v e r   a   r e n d e r i z a r   s i   e s   n e c e s a r i o 
                         f i l t e r P r o d u c t s ( c u r r e n t C a t e g o r y ) ; 
                 }   c a t c h   ( e r r o r )   { 
                         c o n s o l e . e r r o r ( ' E r r o r   p r o c e s a n d o   e v e n t o   S S E : ' ,   e r r o r ) ; 
                 } 
         } ; 
         
         e v t S o u r c e . o n e r r o r   =   f u n c t i o n ( )   { 
                 c o n s o l e . w a r n ( ' �&�  C o n e x i � n   d e   s i n c r o n i z a c i � n   d e   s t o c k   p e r d i d a .   R e c o n e c t a n d o . . . ' ) ; 
         } ; 
 } 
  
 