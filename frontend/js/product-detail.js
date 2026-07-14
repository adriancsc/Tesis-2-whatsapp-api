/**
 * Product Detail Page JavaScript
 * Handles product detail display, cart management, and checkout flow
 */

const API_BASE_URL = window.location.hostname === 'localhost' ? 'http://localhost:8000/api' : `${window.location.origin}/api`;
let currentProduct = null;
let selectedVariant = null;

// ===== CARRITO (localStorage) =====
function getCart() {
    return JSON.parse(localStorage.getItem('gamarra_cart') || '[]');
}

function saveCart(cart) {
    localStorage.setItem('gamarra_cart', JSON.stringify(cart));
    updateCartBadge();
}

function updateCartBadge() {
    const cart = getCart();
    const total = cart.reduce((sum, item) => sum + item.quantity, 0);
    const badge = document.getElementById('cartBadge');
    if (badge) {
        badge.textContent = total;
        badge.style.display = total > 0 ? 'flex' : 'none';
    }
}

function addToCart() {
    if (!selectedVariant || selectedVariant.stock_total === 0) return;

    const quantity = parseInt(document.getElementById('quantityInput').value) || 1;
    const cart = getCart();

    const existingIndex = cart.findIndex(i => i.variant_sku === selectedVariant.sku);
    if (existingIndex >= 0) {
        const newQty = cart[existingIndex].quantity + quantity;
        cart[existingIndex].quantity = Math.min(newQty, selectedVariant.stock_total);
    } else {
        cart.push({
            product_sku: currentProduct.sku,
            variant_sku: selectedVariant.sku,
            name: currentProduct.name,
            size: selectedVariant.size,
            price: currentProduct.base_price,
            quantity: quantity,
            max_stock: selectedVariant.stock_total,
            emoji: getProductEmoji(currentProduct.category)
        });
    }

    saveCart(cart);
    showToast(`✅ ${currentProduct.name} (Talla ${selectedVariant.size}) agregado al carrito`);
}

function buyNow() {
    if (!selectedVariant || selectedVariant.stock_total === 0) return;
    addToCart();
    window.location.href = '/checkout';
}

function getProductEmoji(category) {
    const map = { 'Polos': '👕', 'Pantalones': '👖', 'Camisas': '👔', 'Accesorios': '🎩' };
    return map[category] || '📦';
}

function showToast(message) {
    let toast = document.getElementById('cartToast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'cartToast';
        toast.style.cssText = `
            position: fixed; bottom: 2rem; right: 2rem; z-index: 9999;
            background: #2C2C2C; color: white; padding: 1rem 1.5rem;
            border-radius: 8px; font-family: Poppins, sans-serif;
            font-size: 0.95rem; font-weight: 500;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            transform: translateY(100px); opacity: 0;
            transition: all 0.3s ease; max-width: 320px;
            display: flex; align-items: center; gap: 0.75rem;
        `;
        document.body.appendChild(toast);
    }
    toast.innerHTML = message + ' <a href="/checkout" style="color:#0099FF;margin-left:0.5rem;font-weight:700;">Ver carrito →</a>';
    toast.style.transform = 'translateY(0)';
    toast.style.opacity = '1';
    setTimeout(() => {
        toast.style.transform = 'translateY(100px)';
        toast.style.opacity = '0';
    }, 3500);
}

// ===== INICIALIZACIÓN =====
document.addEventListener('DOMContentLoaded', () => {
    console.log('📦 Product Detail Page initialized');

    // Get product SKU from URL
    const urlParams = new URLSearchParams(window.location.search);
    const sku = urlParams.get('sku');

    if (sku) {
        loadProduct(sku);
        setupStockSync();
    } else {
        showError('No se especificó un producto');
    }
});

// ===== CARGAR PRODUCTO =====
async function loadProduct(sku) {
    const container = document.getElementById('productDetailContainer');

    try {
        // Fetch product from API
        const response = await fetch(`${API_BASE_URL}/products/${sku}`);

        if (!response.ok) {
            throw new Error(`Producto no encontrado: ${sku}`);
        }

        currentProduct = await response.json();

        console.log('✅ Product loaded:', currentProduct);

        // Seleccionar la primera variante con stock por defecto
        selectedVariant = currentProduct.variants.find(v => v.stock_total > 0) || currentProduct.variants[0];

        // Update page title
        document.getElementById('pageTitle').textContent = `${currentProduct.name} | Gamarra Store`;

        // Update breadcrumb
        document.getElementById('breadcrumbCategory').textContent = currentProduct.category || 'Productos';
        document.getElementById('breadcrumbProduct').textContent = currentProduct.name;

        // Render product detail
        renderProductDetail(currentProduct);

    } catch (error) {
        console.error('❌ Error loading product:', error);
        showError(error.message);
    }
}

// ===== RENDERIZAR DETALLE DEL PRODUCTO =====
function renderProductDetail(product) {
    const container = document.getElementById('productDetailContainer');

    const stockTotal = product.total_stock || 0;
    const hasStock = stockTotal > 0;
    const discount = 0; // Sin descuento por defecto

    // Emoji por categoría
    const categoryEmoji = {
        'Polos': '👕',
        'Pantalones': '👖',
        'Camisas': '👔',
        'Accesorios': '🎩'
    };
    const emoji = categoryEmoji[product.category] || '📦';

    // Determinar si hay imagen real
    const hasImage = product.image_url && (product.image_url.includes('.png') || product.image_url.includes('http'));

    // Renderizar selector de tallas con stock
    const sizesHTML = product.variants.map(variant => {
        const disabled = variant.stock_total === 0 ? 'disabled' : '';
        const active = selectedVariant && selectedVariant.sku === variant.sku ? 'active' : '';
        const stockText = variant.stock_total > 0
            ? `(${variant.stock_total})`
            : '(Agotado)';

        return `
            <div class="size-option ${active} ${disabled}" 
                 data-variant-id="${variant.id}"
                 data-size="${variant.size}"
                 data-stock="${variant.stock_total}"
                 data-sku="${variant.sku}"
                 onclick="selectSize('${variant.size}', ${variant.stock_total}, '${variant.sku}')">
                ${variant.size}
                <span class="size-stock">${stockText}</span>
            </div>
        `;
    }).join('');

    // Contenido de la imagen principal
    const mainImageContent = hasImage
        ? `<img src="${product.image_url}" alt="${product.name}" class="main-product-image" style="width: 100%; height: 100%; object-fit: contain;">`
        : `<div class="main-image-placeholder">${emoji}</div>`;

    container.innerHTML = `
        <div class="product-detail-grid">
            <!-- Image Gallery -->
            <div class="product-gallery">
                <div class="main-image-container">
                    ${mainImageContent}
                    <button class="image-nav-btn prev">‹</button>
                    <button class="image-nav-btn next">›</button>
                </div>
                <div class="thumbnail-gallery">
                    <div class="thumbnail active">
                        ${hasImage
            ? `<img src="${product.image_url}" alt="${product.name}" class="thumbnail-image" style="width: 100%; height: 100%; object-fit: cover;">`
            : `<div class="thumbnail-placeholder">${emoji}</div>`
        }
                    </div>
                    <div class="thumbnail">
                        <div class="thumbnail-placeholder">${emoji}</div>
                    </div>
                    <div class="thumbnail">
                        <div class="thumbnail-placeholder">${emoji}</div>
                    </div>
                    <div class="thumbnail">
                        <div class="thumbnail-placeholder">${emoji}</div>
                    </div>
                </div>
            </div>

            <!-- Product Info -->
            <div class="product-info-section">
                <div class="product-brand">GAMARRA STORE</div>
                <h1 class="product-title">${product.name}</h1>
                
                <div class="product-rating">
                    <div class="stars">★★★★★</div>
                    <span class="rating-count">5 (40)</span>
                </div>
                
                <!-- Stock Availability (Arriba del precio) -->
                <div class="stock-availability">
                    <div class="stock-label">Disponibilidad:</div>
                    <div class="stock-info">
                        <span class="stock-badge-large ${stockTotal === 0 ? 'out-of-stock' : stockTotal < 10 ? 'low-stock' : ''}" id="stockBadge">
                            ${stockTotal > 0 ? '✅ En stock' : '❌ Agotado'}
                        </span>
                        <span class="stock-detail" id="stockDetail">
                            ${stockTotal > 0 ? `${stockTotal} unidades disponibles en total` : ''}
                        </span>
                    </div>
                </div>
                
                <!-- Pricing -->
                <div class="product-pricing">
                    <div class="current-price">
                        S/ ${product.base_price.toFixed(2)}
                        ${discount > 0 ? `<span class="discount-badge">-${discount}%</span>` : ''}
                    </div>
                    
                    <div class="delivery-info">
                        <div class="delivery-option">
                            📅 Llega mañana
                        </div>
                        <div class="delivery-option">
                            🔄 Retira mañana
                        </div>
                    </div>
                </div>
                
                <!-- Options -->
                <div class="product-options">
                    ${product.color ? `
                    <div class="option-group">
                        <div class="option-label">Color: <span id="selectedColor">${product.color}</span></div>
                        <div class="color-options">
                            <div class="color-option active" data-color="${product.color}">
                                <div class="thumbnail-placeholder">${emoji}</div>
                            </div>
                        </div>
                    </div>
                    ` : ''}
                    
                    <div class="option-group">
                        <div class="option-label">Talla: <span id="selectedSize">${selectedVariant ? selectedVariant.size : ''}</span></div>
                        <div class="size-options" id="sizeOptions">
                            ${sizesHTML}
                        </div>
                    </div>
                    
                    <div class="option-group">
                        <div class="option-label">Cantidad:</div>
                        <div class="quantity-selector">
                            <div class="quantity-controls">
                                <button class="quantity-btn" id="btnDecrease">−</button>
                                <input type="number" class="quantity-input" id="quantityInput" value="1" min="1" max="${selectedVariant ? selectedVariant.stock_total : 0}">
                                <button class="quantity-btn" id="btnIncrease">+</button>
                            </div>
                            <span class="max-quantity" id="maxQuantity">Máximo ${selectedVariant ? selectedVariant.stock_total : 0} unidades</span>
                        </div>
                    </div>
                </div>
                
                <!-- Actions -->
                <div class="product-actions">
                    <button class="btn-add-to-cart" ${!hasStock ? 'disabled' : ''} id="btnAddToCart" onclick="addToCart()">
                        ${hasStock ? '🛒 Agregar al carrito' : '❌ Agotado'}
                    </button>
                    <button class="btn-buy-now" ${!hasStock ? 'disabled' : ''} id="btnBuyNow" onclick="buyNow()">
                        ⚡ Comprar ahora
                    </button>
                    <div class="cmr-promo">
                        <div class="cmr-promo-title">💳 Pago 100% seguro con Izipay</div>
                        <div class="cmr-promo-text">Acepta tarjetas Visa, Mastercard y Yape</div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Specifications -->
        <div class="product-specifications">
            <h2 class="specifications-title">Especificaciones principales</h2>
            <ul class="specifications-list">
                <li class="specification-item">
                    <span class="spec-icon">✓</span>
                    <span class="spec-text">
                        <span class="spec-label">Material de vestuario:</span>
                        Algodón
                    </span>
                </li>
                <li class="specification-item">
                    <span class="spec-icon">✓</span>
                    <span class="spec-text">
                        <span class="spec-label">Fit prenda superior:</span>
                        Regular fit
                    </span>
                </li>
                <li class="specification-item">
                    <span class="spec-icon">✓</span>
                    <span class="spec-text">
                        <span class="spec-label">SKU Base:</span>
                        ${product.sku}
                    </span>
                </li>
                <li class="specification-item">
                    <span class="spec-icon">✓</span>
                    <span class="spec-text">
                        <span class="spec-label">Stock total:</span>
                        ${stockTotal} unidades
                    </span>
                </li>
                ${product.description ? `
                <li class="specification-item">
                    <span class="spec-icon">✓</span>
                    <span class="spec-text">
                        <span class="spec-label">Descripción:</span>
                        ${product.description}
                    </span>
                </li>
                ` : ''}
            </ul>
        </div>
    `;

    // Setup event listeners
    setupQuantityControls();
    updateCartBadge();
}

// ===== CONTROLES DE CANTIDAD =====
function setupQuantityControls() {
    const btnDecrease = document.getElementById('btnDecrease');
    const btnIncrease = document.getElementById('btnIncrease');
    const quantityInput = document.getElementById('quantityInput');

    if (btnDecrease) {
        btnDecrease.addEventListener('click', () => {
            const currentValue = parseInt(quantityInput.value);
            if (currentValue > 1) {
                quantityInput.value = currentValue - 1;
            }
        });
    }

    if (btnIncrease) {
        btnIncrease.addEventListener('click', () => {
            const currentValue = parseInt(quantityInput.value);
            const maxValue = parseInt(quantityInput.max);
            if (currentValue < maxValue) {
                quantityInput.value = currentValue + 1;
            }
        });
    }
}

// ===== SELECTOR DE TALLA =====
function selectSize(size, stock, variantSku) {
    // Remove active class from all size options
    const sizeOptions = document.querySelectorAll('.size-option');
    sizeOptions.forEach(option => option.classList.remove('active'));

    // Add active class to selected size
    const selectedOption = document.querySelector(`[data-sku="${variantSku}"]`);
    if (selectedOption) {
        selectedOption.classList.add('active');
    }

    // Update selected variant
    selectedVariant = currentProduct.variants.find(v => v.sku === variantSku);

    // Update selected size display
    const selectedSizeDisplay = document.getElementById('selectedSize');
    if (selectedSizeDisplay) {
        selectedSizeDisplay.textContent = size;
    }

    // Update quantity controls
    const quantityInput = document.getElementById('quantityInput');
    const maxQuantity = document.getElementById('maxQuantity');
    const btnAddToCart = document.getElementById('btnAddToCart');

    if (quantityInput) {
        quantityInput.max = stock;
        quantityInput.value = Math.min(parseInt(quantityInput.value), stock);
    }

    if (maxQuantity) {
        maxQuantity.textContent = `Máximo ${stock} unidades`;
    }

    // Update stock display
    const stockBadge = document.getElementById('stockBadge');
    const stockDetail = document.getElementById('stockDetail');

    if (stockBadge) {
        stockBadge.className = `stock-badge-large ${stock === 0 ? 'out-of-stock' : stock < 5 ? 'low-stock' : ''}`;
        stockBadge.textContent = stock > 0 ? '✅ En stock' : '❌ Agotado';
    }

    if (stockDetail) {
        stockDetail.textContent = stock > 0
            ? `${stock} unidades disponibles (Talla ${size})`
            : 'Sin stock para esta talla';
    }

    // Update add to cart button
    if (btnAddToCart) {
        if (stock > 0) {
            btnAddToCart.disabled = false;
            btnAddToCart.textContent = 'Agregar al carrito';
        } else {
            btnAddToCart.disabled = true;
            btnAddToCart.textContent = 'Agotado';
        }
    }

    console.log(`✅ Talla seleccionada: ${size} (Stock: ${stock}, SKU: ${variantSku})`);
}

// ===== MOSTRAR ERROR =====
function showError(message) {
    const container = document.getElementById('productDetailContainer');
    container.innerHTML = `
        <div class="empty-state">
            <div class="empty-icon">❌</div>
            <h3>Error al cargar el producto</h3>
            <p>${message}</p>
            <a href="/store" class="btn-back" style="margin-top: 1rem; display: inline-block;">
                ← Volver a la tienda
            </a>
        </div>
    `;
}

// ===== CONEXIÓN SSE PARA STOCK EN TIEMPO REAL =====
function setupStockSync() {
    const evtSource = new EventSource(API_BASE_URL + '/api/stream/stock');
    
    evtSource.onmessage = function(event) {
        console.log('🔄 Sincronización de stock recibida:', event.data);
        try {
            const data = JSON.parse(event.data);
            
            // Actualizar currentProduct en memoria
            if (currentProduct) {
                const variant = currentProduct.variants.find(v => v.sku === data.variant_sku);
                if (variant) {
                    variant.stock_total = data.new_stock;
                    // Si esta es la variante seleccionada, actualizar UI
                    if (selectedVariant && selectedVariant.sku === data.variant_sku) {
                        selectSize(data.variant_sku); // Re-render the details
                    }
                }
            }
        } catch (error) {
            console.error('Error procesando evento SSE:', error);
        }
    };
    
    evtSource.onerror = function() {
        console.warn('⚠️ Conexión de sincronización de stock perdida. Reconectando...');
    };
}

