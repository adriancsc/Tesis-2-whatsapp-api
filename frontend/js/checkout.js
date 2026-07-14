/**
 * Checkout Page JavaScript
 * Maneja el carrito, el formulario de datos y la pasarela Izipay simulada.
 * Al confirmar pago, dispara el webhook REAL al Sistema Multiagente (MAS).
 */

const API_BASE_URL = window.location.hostname === 'localhost' ? 'http://localhost:8000/api' : `${window.location.origin}/api`;
let paymentMethod = 'card';

// ===== INICIALIZACIÓN =====
document.addEventListener('DOMContentLoaded', () => {
    console.log('💳 Checkout initialized');
    renderCart();
    renderSummary();
});

// ===== LEER CARRITO =====
function getCart() {
    return JSON.parse(localStorage.getItem('gamarra_cart') || '[]');
}

// ===== RENDERIZAR ITEMS DEL CARRITO =====
function renderCart() {
    const cart = getCart();
    const listEl = document.getElementById('cartItemsList');
    const emptyEl = document.getElementById('cartEmpty');

    if (cart.length === 0) {
        listEl.style.display = 'none';
        emptyEl.style.display = 'block';
        return;
    }

    listEl.innerHTML = cart.map((item, idx) => `
        <div class="cart-item">
            <div class="cart-item-emoji">${item.emoji || '📦'}</div>
            <div class="cart-item-info">
                <div class="cart-item-name">${item.name}</div>
                <div class="cart-item-meta">Talla: ${item.size} · SKU: ${item.variant_sku}</div>
                <div class="cart-item-qty">
                    <button onclick="changeQty(${idx}, -1)">−</button>
                    <span>${item.quantity}</span>
                    <button onclick="changeQty(${idx}, 1)">+</button>
                    <button class="btn-remove" onclick="removeItem(${idx})">🗑️</button>
                </div>
            </div>
            <div class="cart-item-price">S/ ${(item.price * item.quantity).toFixed(2)}</div>
        </div>
    `).join('');
}

function changeQty(idx, delta) {
    const cart = getCart();
    cart[idx].quantity = Math.max(1, Math.min(cart[idx].quantity + delta, cart[idx].max_stock));
    localStorage.setItem('gamarra_cart', JSON.stringify(cart));
    renderCart();
    renderSummary();
}

function removeItem(idx) {
    const cart = getCart();
    cart.splice(idx, 1);
    localStorage.setItem('gamarra_cart', JSON.stringify(cart));
    renderCart();
    renderSummary();
}

// ===== RENDERIZAR RESUMEN DE PRECIOS =====
function renderSummary() {
    const cart = getCart();
    const subtotal = cart.reduce((sum, item) => sum + item.price * item.quantity, 0);
    const shipping = cart.length > 0 ? 10.00 : 0;
    const total = subtotal + shipping;

    document.getElementById('summaryLines').innerHTML = `
        <div class="summary-line">
            <span>Subtotal (${cart.reduce((s, i) => s + i.quantity, 0)} productos)</span>
            <span>S/ ${subtotal.toFixed(2)}</span>
        </div>
        <div class="summary-line">
            <span>Envío estimado</span>
            <span>S/ ${shipping.toFixed(2)}</span>
        </div>
    `;

    document.getElementById('summaryTotal').textContent = `S/ ${total.toFixed(2)}`;
    document.getElementById('btnPayTotal').textContent = `S/ ${total.toFixed(2)}`;
    document.getElementById('yapeAmount').textContent = `S/ ${total.toFixed(2)}`;
}

// ===== MÉTODO DE PAGO =====
function selectPaymentMethod(method) {
    paymentMethod = method;
    document.querySelectorAll('.payment-method').forEach(el => el.classList.remove('active'));
    document.getElementById(method === 'card' ? 'methodCard' : 'methodYape').classList.add('active');
    document.getElementById('cardForm').style.display = method === 'card' ? 'block' : 'none';
    document.getElementById('yapeForm').style.display = method === 'yape' ? 'block' : 'none';
}

// ===== FORMATEAR NÚMERO DE TARJETA =====
function formatCardNumber(input) {
    let value = input.value.replace(/\D/g, '').slice(0, 16);
    input.value = value.replace(/(.{4})/g, '$1 ').trim();
}

function formatExpiry(input) {
    let value = input.value.replace(/\D/g, '').slice(0, 4);
    if (value.length >= 3) value = value.slice(0, 2) + '/' + value.slice(2);
    input.value = value;
}

// ===== GENERAR ORDER ID =====
function generateOrderId() {
    return `ORD-${Date.now()}-${Math.random().toString(36).substring(2, 7).toUpperCase()}`;
}

// ===== VALIDAR FORMULARIO =====
function validateForm() {
    const required = ['firstName', 'lastName', 'email', 'phone', 'address', 'district'];
    for (const id of required) {
        const el = document.getElementById(id);
        if (!el || !el.value.trim()) {
            el.style.borderColor = '#F44336';
            el.focus();
            return false;
        }
        el.style.borderColor = '';
    }

    const cart = getCart();
    if (cart.length === 0) {
        alert('Tu carrito está vacío.');
        return false;
    }

    if (paymentMethod === 'card') {
        const cardNum = document.getElementById('cardNumber').value.replace(/\s/g, '');
        if (cardNum.length < 15) {
            document.getElementById('cardNumber').style.borderColor = '#F44336';
            document.getElementById('cardNumber').focus();
            return false;
        }
    }

    return true;
}

// ===== MOSTRAR MODAL =====
function showModal() {
    document.getElementById('paymentModal').style.display = 'flex';
}

function closeModal() {
    document.getElementById('paymentModal').style.display = 'none';
    // Resetear pasos
    ['modalStep1','modalStep2','modalStep3','modalStep4','modalStepError'].forEach(id => {
        document.getElementById(id).style.display = 'none';
    });
    document.getElementById('modalStep1').style.display = 'block';
}

function showModalStep(stepId) {
    ['modalStep1','modalStep2','modalStep3','modalStep4','modalStepError'].forEach(id => {
        document.getElementById(id).style.display = 'none';
    });
    document.getElementById(stepId).style.display = 'block';
}

// ===== PROCESAR PAGO (CORAZÓN DEL SISTEMA) =====
async function procesarPago() {
    if (!validateForm()) return;

    const cart = getCart();
    if (cart.length === 0) return;

    showModal();

    // Paso 1: Conectando con Izipay (visual)
    showModalStep('modalStep1');
    await sleep(1500);

    // Paso 2: Autorizando (visual)
    showModalStep('modalStep2');
    await sleep(1800);

    // Paso 3: Notificar al MAS (acción REAL)
    showModalStep('modalStep3');

    const orderId = generateOrderId();
    const orderData = {
        order_id: orderId,
        variant_sku: cart[0].variant_sku, // Primer item del carrito
        quantity: cart[0].quantity,
        payment_status: 'approved',
        payment_method: paymentMethod === 'card' ? 'izipay_tarjeta' : 'izipay_yape',
        payment_transaction_id: `TXN-${Date.now()}`,
        customer: {
            name: `${document.getElementById('firstName').value} ${document.getElementById('lastName').value}`,
            email: document.getElementById('email').value,
            phone: document.getElementById('phone').value,
            address: `${document.getElementById('address').value}, ${document.getElementById('district').value}`
        },
        total_amount: cart.reduce((s, i) => s + i.price * i.quantity, 0) + 10
    };

    try {
        // ===== DISPARO REAL AL AGENTE DE SINCRONIZACIÓN MAS =====
        const response = await fetch(`${API_BASE_URL.replace('/api', '')}/webhook/ecommerce`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(orderData)
        });

        await sleep(1200);

        if (response.ok || response.status === 200 || response.status === 202) {
            // ¡Éxito! El MAS procesó la orden
            showModalStep('modalStep4');

            // Guardar orden en sessionStorage para la página de éxito
            sessionStorage.setItem('last_order', JSON.stringify({
                order_id: orderId,
                items: cart,
                customer_name: orderData.customer.name,
                total: orderData.total_amount,
                timestamp: new Date().toISOString()
            }));

            // Limpiar carrito
            localStorage.removeItem('gamarra_cart');

            await sleep(2000);
            window.location.href = `/order-success?order_id=${orderId}`;

        } else {
            // El MAS rechazó la orden (ej. stock agotado por concurrencia)
            const errorData = await response.json().catch(() => ({}));
            document.getElementById('modalErrorMsg').textContent =
                errorData.detail || 'Stock insuficiente. Otro cliente compró el mismo producto.';
            showModalStep('modalStepError');
        }

    } catch (networkError) {
        // Error de red (servidor caído)
        console.error('Error de red:', networkError);
        document.getElementById('modalErrorMsg').textContent =
            'No se pudo conectar con el servidor. Verifica que el sistema esté corriendo.';
        showModalStep('modalStepError');
    }
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}
