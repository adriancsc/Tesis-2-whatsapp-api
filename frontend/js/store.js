/**
 * Gamarra Store Frontend JavaScript
 * Maneja la carga y visualización de productos
 */

const API_BASE_URL = window.location.hostname === 'localhost' ? 'http://localhost:8000/api' : `${window.location.origin}/api`;
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
    const basePath = window.location.pathname.includes('/static/') ? '/static/' : '/';
    window.location.href = `${basePath}product-detail.html?sku=${sku}`;
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


// ===== CONEXION SSE PARA STOCK EN TIEMPO REAL =====
function setupStockSync() {
    const evtSource = new EventSource(API_BASE_URL + '/stream/stock');
    
    evtSource.onmessage = function(event) {
        console.log('Sincronizacion de stock recibida:', event.data);
        try {
            const data = JSON.parse(event.data);
            
            // Actualizar allProducts en memoria
            allProducts.forEach(p => {
                const variant = p.variants.find(v => v.sku === data.variant_sku);
                if (variant) {
                    variant.stock_total = data.new_stock;
                    // Recalcular total_stock del producto padre
                    p.total_stock = p.variants.reduce((acc, curr) => acc + curr.stock_total, 0);
                }
            });
            
            // Volver a renderizar si es necesario
            filterProducts(currentCategory);
        } catch (error) {
            console.error('Error procesando evento SSE:', error);
        }
    };
    
    evtSource.onerror = function() {
        console.warn('Conexion de sincronizacion de stock perdida. Reconectando...');
    };
}
