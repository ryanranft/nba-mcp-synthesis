// NBA MCP Synthesis - Dashboard JavaScript

const API_BASE = '';
const REFRESH_INTERVAL = 2000; // 2 seconds

let lastUpdate = null;
let refreshTimer = null;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    console.log('Dashboard initialized');
    startAutoRefresh();
    fetchAllData();
});

// Auto-refresh
function startAutoRefresh() {
    refreshTimer = setInterval(fetchAllData, REFRESH_INTERVAL);
    console.log(`Auto-refresh started (every ${REFRESH_INTERVAL / 1000}s)`);
}

function stopAutoRefresh() {
    if (refreshTimer) {
        clearInterval(refreshTimer);
        refreshTimer = null;
        console.log('Auto-refresh stopped');
    }
}

// Fetch all data
async function fetchAllData() {
    try {
        await Promise.all([
            fetchStatus(),
            fetchPhases(),
            fetchCost(),
            fetchSystem()
        ]);
        updateLastUpdateTime();
    } catch (error) {
        console.error('Error fetching data:', error);
    }
}

// Fetch workflow status
async function fetchStatus() {
    try {
        const response = await fetch(`${API_BASE}/api/status`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = await response.json();
        updateStatus(data);
    } catch (error) {
        console.error('Failed to fetch status:', error);
    }
}

// Update status display
function updateStatus(data) {
    // Status indicator
    const indicator = document.getElementById('status-indicator');
    const statusText = document.getElementById('status-text');

    if (data.workflow_active) {
        indicator.className = 'status-indicator active';
        statusText.textContent = 'Active';
    } else {
        indicator.className = 'status-indicator inactive';
        statusText.textContent = 'Idle';
    }

    // Current phase
    document.getElementById('current-phase').textContent = data.current_phase || 'None';

    // Books progress
    const books = data.books || {};
    document.getElementById('books-processed').textContent =
        `${books.processed || 0} / ${books.total || 0}`;

    // Progress bar
    const progress = books.progress || 0;
    document.getElementById('progress-bar').style.width = `${progress}%`;
    document.getElementById('progress-percent').textContent = `${progress}%`;

    // Time
    document.getElementById('elapsed-time').textContent = data.elapsed || '0s';
    document.getElementById('time-remaining').textContent = data.time_remaining || 'Unknown';
}

// Fetch phases
async function fetchPhases() {
    try {
        const response = await fetch(`${API_BASE}/api/phases`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = await response.json();
        updatePhases(data);
    } catch (error) {
        console.error('Failed to fetch phases:', error);
        document.getElementById('phases-container').innerHTML =
            '<div class="loading">Failed to load phases</div>';
    }
}

// Update phases display
function updatePhases(phases) {
    const container = document.getElementById('phases-container');
    if (!phases || Object.keys(phases).length === 0) {
        container.innerHTML = '<div class="no-alerts">No phase data available</div>';
        return;
    }

    const phaseCards = Object.entries(phases).map(([phaseId, phaseData]) => {
        const statusClass = (phaseData.status || 'pending').toLowerCase().replace('_', '-');
        const duration = phaseData.duration ? formatDuration(phaseData.duration) : '-';

        return `
            <div class="phase-card ${statusClass}">
                <div class="phase-name">${phaseId.replace('_', ' ').toUpperCase()}</div>
                <div class="phase-status">${phaseData.status || 'Pending'}</div>
                <div class="phase-duration">⏱️ ${duration}</div>
            </div>
        `;
    }).join('');

    container.innerHTML = phaseCards;
}

// Fetch cost data
async function fetchCost() {
    try {
        const response = await fetch(`${API_BASE}/api/cost`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = await response.json();
        updateCost(data);
    } catch (error) {
        console.error('Failed to fetch cost:', error);
    }
}

// Update cost display
function updateCost(data) {
    const totalCost = data.total_cost || 0;
    const budget = data.budget || 400;
    const remaining = data.remaining || budget;

    document.getElementById('total-cost').textContent = `$${totalCost.toFixed(2)}`;
    document.getElementById('budget').textContent = `$${budget.toFixed(2)}`;
    document.getElementById('remaining-budget').textContent = `$${remaining.toFixed(2)}`;

    const budgetPercent = budget > 0 ? (totalCost / budget) * 100 : 0;
    document.getElementById('budget-bar').style.width = `${Math.min(budgetPercent, 100)}%`;
    document.getElementById('budget-percent').textContent = `${budgetPercent.toFixed(1)}%`;
}

// Fetch system metrics
async function fetchSystem() {
    try {
        const response = await fetch(`${API_BASE}/api/system`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = await response.json();
        updateSystem(data);
    } catch (error) {
        console.error('Failed to fetch system metrics:', error);
    }
}

// Update system display
function updateSystem(data) {
    // API Quotas
    const apiQuotas = data.api_quotas || {};

    if (apiQuotas.gemini) {
        const gemini = apiQuotas.gemini;
        document.getElementById('gemini-quota').textContent =
            `${formatNumber(gemini.used)} / ${formatNumber(gemini.limit)}`;
        document.getElementById('gemini-status').className =
            `status-badge ${getQuotaStatus(gemini.usage_percent)}`;
    }

    if (apiQuotas.claude) {
        const claude = apiQuotas.claude;
        document.getElementById('claude-quota').textContent =
            `${formatNumber(claude.used)} / ${formatNumber(claude.limit)}`;
        document.getElementById('claude-status').className =
            `status-badge ${getQuotaStatus(claude.usage_percent)}`;
    }

    // Disk
    const disk = data.disk || {};
    if (disk.free_gb !== undefined) {
        document.getElementById('disk-space').textContent =
            `${disk.free_gb.toFixed(1)} GB free`;
        document.getElementById('disk-status').className =
            `status-badge ${getThresholdStatus(disk.usage_percent)}`;
    }

    // Memory
    const memory = data.memory || {};
    if (memory.available_gb !== undefined) {
        document.getElementById('memory-usage').textContent =
            `${memory.available_gb.toFixed(1)} GB available`;
        document.getElementById('memory-status').className =
            `status-badge ${getThresholdStatus(memory.usage_percent)}`;
    }

    // Cache
    if (disk.cache_gb !== undefined) {
        document.getElementById('cache-size').textContent =
            `${disk.cache_gb.toFixed(1)} GB`;
    }

    // Alerts
    updateAlerts(data.alerts || []);
}

// Update alerts display
function updateAlerts(alerts) {
    const container = document.getElementById('alerts-container');

    if (alerts.length === 0) {
        container.innerHTML = '<div class="no-alerts">No alerts</div>';
        return;
    }

    const alertItems = alerts.map(alert => {
        const levelClass = alert.level || 'info';
        const time = alert.timestamp ? new Date(alert.timestamp).toLocaleTimeString() : '-';

        return `
            <div class="alert-item ${levelClass}">
                <div class="alert-time">${time}</div>
                <div class="alert-message">${alert.message}</div>
            </div>
        `;
    }).join('');

    container.innerHTML = alertItems;
}

// Utility functions
function getQuotaStatus(usage) {
    if (usage >= 0.95) return 'critical';
    if (usage >= 0.80) return 'warning';
    return 'ok';
}

function getThresholdStatus(usage) {
    if (usage >= 0.95) return 'critical';
    if (usage >= 0.80) return 'warning';
    return 'ok';
}

function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

function formatDuration(seconds) {
    if (seconds < 60) {
        return `${Math.floor(seconds)}s`;
    } else if (seconds < 3600) {
        const minutes = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${minutes}m ${secs}s`;
    } else {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        return `${hours}h ${minutes}m`;
    }
}

function updateLastUpdateTime() {
    const now = new Date();
    document.getElementById('last-update').textContent = now.toLocaleTimeString();
    lastUpdate = now;
}

// Handle visibility change (pause when tab hidden)
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        stopAutoRefresh();
    } else {
        startAutoRefresh();
        fetchAllData(); // Immediate refresh when tab becomes visible
    }
});

// Handle errors
window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
});




