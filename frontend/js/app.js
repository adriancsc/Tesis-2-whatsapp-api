/**
 * Dashboard JavaScript - Sistema MAS-CIS
 * Maneja la lógica del dashboard y actualizaciones en tiempo real
 */

const API_BASE_URL = window.location.hostname === 'localhost' ? 'http://localhost:8000' : window.location.origin;
let refreshInterval = null;

// ==================== Inicialización ====================
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Dashboard MAS-CIS iniciado');

    // Cargar datos iniciales
    loadDashboardData();

    // Configurar auto-refresh cada 5 segundos
    refreshInterval = setInterval(loadDashboardData, 5000);

    // Event listeners
    document.getElementById('btnRefresh').addEventListener('click', () => {
        loadDashboardData();
        showNotification('Datos actualizados', 'success');
    });
});

// ==================== Cargar Datos del Dashboard ====================
async function loadDashboardData() {
    try {
        // Verificar estado del sistema
        await checkSystemHealth();

        // Cargar estadísticas
        await loadStats();

        // Cargar estado de agentes
        await loadAgents();

        // Cargar inventario
        await loadInventory();

    } catch (error) {
        console.error('Error cargando datos:', error);
        updateSystemStatus('error', 'Error de conexión');
    }
}

// ==================== Health Check ====================
async function checkSystemHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();

        if (data.status === 'healthy') {
            updateSystemStatus('online', 'Sistema Activo');
        } else {
            updateSystemStatus('warning', 'Sistema con problemas');
        }
    } catch (error) {
        updateSystemStatus('error', 'Desconectado');
        throw error;
    }
}

// ==================== Cargar Estadísticas ====================
async function loadStats() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/dashboard/stats`);
        const stats = await response.json();

        // Actualizar tarjetas de estadísticas con animación
        animateValue('totalProducts', stats.total_products);
        animateValue('totalStock', stats.total_stock);
        animateValue('lowStock', stats.low_stock_products);
        animateValue('transactionsToday', stats.transactions_today);

    } catch (error) {
        console.error('Error cargando estadísticas:', error);
    }
}

// ==================== Cargar Agentes ====================
async function loadAgents() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/dashboard/agents`);
        const agents = await response.json();

        const agentsGrid = document.getElementById('agentsGrid');
        agentsGrid.innerHTML = '';

        agents.forEach(agent => {
            const agentCard = createAgentCard(agent);
            agentsGrid.appendChild(agentCard);
        });

    } catch (error) {
        console.error('Error cargando agentes:', error);
    }
}

// ==================== Cargar Inventario ====================
async function loadInventory() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/dashboard/inventory?limit=50`);
        const inventory = await response.json();

        const tableBody = document.getElementById('inventoryTableBody');
        tableBody.innerHTML = '';

        inventory.forEach(item => {
            const row = createInventoryRow(item);
            tableBody.appendChild(row);
        });

    } catch (error) {
        console.error('Error cargando inventario:', error);
    }
}

// ==================== Crear Card de Agente ====================
function createAgentCard(agent) {
    const card = document.createElement('div');
    card.className = 'agent-card';

    const agentTypeEmoji = agent.agent_type === 'store' ? '🏪' : '🔄';
    const agentTypeName = agent.agent_type === 'store' ? 'Agente de Tienda' : 'Agente Coordinador';

    const lastActivity = new Date(agent.last_activity);
    const timeAgo = getTimeAgo(lastActivity);

    card.innerHTML = `
        <div class="agent-header">
            <div class="agent-name">${agentTypeEmoji} ${agentTypeName}</div>
            <div class="agent-status ${agent.status}">${agent.status}</div>
        </div>
        <div class="agent-info">
            <div>ID: <strong>${agent.agent_id}</strong></div>
            <div>Última actividad: <strong>${timeAgo}</strong></div>
        </div>
    `;

    return card;
}

// ==================== Crear Fila de Inventario ====================
function createInventoryRow(item) {
    const row = document.createElement('tr');

    const stockClass = getStockClass(item.stock_total);
    const lastUpdated = new Date(item.last_updated);
    const timeAgo = getTimeAgo(lastUpdated);

    row.innerHTML = `
        <td><strong>${item.sku}</strong></td>
        <td>${item.name}</td>
        <td>${item.category || '-'}</td>
        <td>S/ ${item.price.toFixed(2)}</td>
        <td>${item.stock_physical}</td>
        <td>${item.stock_virtual}</td>
        <td><span class="stock-badge ${stockClass}">${item.stock_total}</span></td>
        <td>${timeAgo}</td>
    `;

    return row;
}

// ==================== Utilidades ====================
function updateSystemStatus(status, text) {
    const indicator = document.getElementById('systemStatus');
    const dot = indicator.querySelector('.status-dot');
    const statusText = indicator.querySelector('.status-text');

    // Remover clases anteriores
    dot.className = 'status-dot';

    // Aplicar nueva clase según el estado
    if (status === 'online') {
        dot.style.background = 'var(--success)';
    } else if (status === 'warning') {
        dot.style.background = 'var(--warning)';
    } else if (status === 'error') {
        dot.style.background = 'var(--error)';
    }

    statusText.textContent = text;
}

function getStockClass(stock) {
    if (stock >= 10) return 'stock-high';
    if (stock >= 5) return 'stock-medium';
    return 'stock-low';
}

function getTimeAgo(date) {
    const seconds = Math.floor((new Date() - date) / 1000);

    if (seconds < 60) return 'Hace un momento';
    if (seconds < 3600) return `Hace ${Math.floor(seconds / 60)} min`;
    if (seconds < 86400) return `Hace ${Math.floor(seconds / 3600)} hrs`;
    return `Hace ${Math.floor(seconds / 86400)} días`;
}

function animateValue(elementId, endValue) {
    const element = document.getElementById(elementId);
    const startValue = parseInt(element.textContent) || 0;
    const duration = 500;
    const startTime = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);

        const currentValue = Math.floor(startValue + (endValue - startValue) * progress);
        element.textContent = currentValue;

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    requestAnimationFrame(update);
}

function showNotification(message, type = 'info') {
    console.log(`[${type.toUpperCase()}] ${message}`);
    // Aquí podrías agregar un sistema de notificaciones toast
}

// ==================== Cleanup ====================
window.addEventListener('beforeunload', () => {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
});
