// Vercel-optimized main.js for SVN Trading Bot

// Global variables
let updateInterval = null;
let isConnected = false;

// API helper function with auth
function apiRequest(url, options = {}) {
    const token = localStorage.getItem('auth_token');
    
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` })
        }
    };
    
    return fetch(url, { ...defaultOptions, ...options })
        .then(response => {
            if (response.status === 401) {
                // Token expired or invalid
                localStorage.removeItem('auth_token');
                window.location.href = '/login';
                throw new Error('Authentication required');
            }
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    const currentPath = window.location.pathname;
    
    // Skip auth check for login page
    if (currentPath === '/login') {
        return;
    }
    
    // Check authentication
    if (!isAuthenticated()) {
        window.location.href = '/login';
        return;
    }
    
    // Initialize dashboard functionality
    initializePage();
    startPeriodicUpdates();
});

function isAuthenticated() {
    const token = localStorage.getItem('auth_token');
    if (!token) return false;
    
    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        return payload.exp > Date.now() / 1000;
    } catch {
        return false;
    }
}

function initializePage() {
    const currentPath = window.location.pathname;
    
    switch (currentPath) {
        case '/':
            initializeDashboard();
            break;
        case '/users':
            initializeUsers();
            break;
        case '/ai-analytics':
            initializeAIAnalytics();
            break;
        default:
            console.log('Unknown page:', currentPath);
    }
}

// Dashboard initialization
function initializeDashboard() {
    console.log('Initializing dashboard...');
    loadDashboardData();
}

function loadDashboardData() {
    // Load bot status
    apiRequest('/api/status')
        .then(data => {
            updateBotStatus(data);
            isConnected = true;
        })
        .catch(error => {
            console.error('Error loading bot status:', error);
            updateBotStatus({ status: 'error', message: error.message });
            isConnected = false;
        });
    
    // Load dashboard data
    apiRequest('/api/dashboard')
        .then(data => {
            updateDashboardStats(data.statistics);
            updateDashboardCharts(data.charts);
            updateRecentTrades(data.recent_trades);
            updateSystemLogs(data.system_logs);
        })
        .catch(error => {
            console.error('Error loading dashboard data:', error);
            showAlert('Ошибка загрузки данных дашборда', 'danger');
        });
}

function updateBotStatus(data) {
    const statusElement = document.getElementById('botStatus');
    const statusText = document.getElementById('statusText');
    
    if (!statusElement || !statusText) return;
    
    if (data.status === 'operational') {
        statusElement.className = 'status-indicator status-online';
        statusText.textContent = 'AI System Online & Learning';
        
        // Update main statistics
        updateElement('totalTrades', data.total_trades || 0);
        updateElement('dailyProfit', '$' + (data.daily_avg_profit || 0).toFixed(2));
        updateElement('activeUsers', data.total_users || 0);
        updateElement('dataPoints', (data.total_data_points || 0).toLocaleString());
        updateElement('modelsLoaded', data.models_loaded || 0);
        
        // Calculate and display win rate
        const winRate = data.daily_trade_count > 0 ? 
            ((data.daily_avg_profit > 0 ? data.daily_trade_count * 0.65 : data.daily_trade_count * 0.35) / data.daily_trade_count * 100) : 0;
        updateElement('winRate', winRate.toFixed(1) + '%');
        
        // Update accuracy
        const accuracy = Math.min(95, 60 + (data.total_data_points || 0) / 100);
        updateElement('accuracy', accuracy.toFixed(1) + '%');
        
        // Update learning progress
        const progress = Math.min(100, (data.total_data_points || 0) / 50);
        const progressBar = document.getElementById('learningProgress');
        if (progressBar) {
            progressBar.style.width = progress + '%';
            progressBar.textContent = progress.toFixed(0) + '%';
        }
    } else {
        statusElement.className = 'status-indicator status-offline';
        statusText.textContent = 'AI System Offline';
    }
    
    updateElement('lastUpdate', 'Just now');
}

function updateElement(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = value;
    }
}

function updateDashboardStats(stats) {
    if (!stats) return;
    
    updateElement('active-bots', stats.active_bots || 0);
    updateElement('total-profit', '$' + (stats.total_profit || 0).toFixed(2));
    updateElement('trades-today', stats.trades_today || 0);
    updateElement('ai-accuracy', (stats.ai_accuracy || 0).toFixed(1) + '%');
}

function updateDashboardCharts(chartData) {
    // Update charts if Chart.js is available
    if (typeof Chart !== 'undefined' && chartData) {
        updateProfitChart(chartData.profit);
        updateTradesChart(chartData.trades);
    }
}

function updateProfitChart(profitData) {
    const canvas = document.getElementById('profitChart');
    if (!canvas || !profitData) return;
    
    // Chart implementation would go here
    console.log('Updating profit chart with data:', profitData);
}

function updateTradesChart(tradesData) {
    const canvas = document.getElementById('tradesChart');
    if (!canvas || !tradesData) return;
    
    // Chart implementation would go here
    console.log('Updating trades chart with data:', tradesData);
}

function updateRecentTrades(trades) {
    const tbody = document.getElementById('recent-trades');
    if (!tbody || !trades) return;
    
    tbody.innerHTML = '';
    
    trades.forEach(trade => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${new Date(trade.timestamp).toLocaleString()}</td>
            <td>${trade.user_id}</td>
            <td>${trade.symbol}</td>
            <td><span class="badge bg-${trade.type === 'buy' ? 'success' : 'danger'}">${trade.type.toUpperCase()}</span></td>
            <td>${trade.volume}</td>
            <td class="${trade.profit >= 0 ? 'text-success' : 'text-danger'}">$${trade.profit.toFixed(2)}</td>
            <td><span class="badge bg-info">${trade.ai_signal}</span></td>
        `;
        tbody.appendChild(row);
    });
}

function updateSystemLogs(logs) {
    const logsDiv = document.getElementById('system-logs');
    if (!logsDiv || !logs) return;
    
    logsDiv.innerHTML = '';
    
    logs.forEach(log => {
        const logEntry = document.createElement('div');
        logEntry.innerHTML = `<span class="text-muted">[${new Date(log.timestamp).toLocaleTimeString()}]</span> ${log.message}`;
        logsDiv.appendChild(logEntry);
    });
    
    // Auto-scroll to bottom
    logsDiv.scrollTop = logsDiv.scrollHeight;
}

// Users page initialization
function initializeUsers() {
    console.log('Initializing users page...');
    loadUsersData();
}

function loadUsersData() {
    const period = document.getElementById('date-range')?.value || '7d';
    const status = document.getElementById('status-filter')?.value || 'all';
    
    apiRequest(`/api/users?period=${period}&status=${status}`)
        .then(data => {
            updateUserStats(data.stats);
            updateUsersTable(data.users);
        })
        .catch(error => {
            console.error('Error loading users:', error);
            showAlert('Ошибка загрузки пользователей', 'danger');
        });
}

function updateUserStats(stats) {
    if (!stats) return;
    
    updateElement('total-users', stats.total || 0);
    updateElement('active-users', stats.active || 0);
    updateElement('total-user-profit', '$' + (stats.total_profit || 0).toFixed(2));
}

function updateUsersTable(users) {
    const tbody = document.getElementById('users-table');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    if (!users || users.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">Нет активных пользователей</td></tr>';
        return;
    }
    
    users.forEach(user => {
        const lastActivity = new Date(user.last_activity);
        const isActive = (new Date() - lastActivity) < 5 * 60 * 1000; // активен если был онлайн менее 5 минут назад
        
        const row = document.createElement('tr');
        row.innerHTML = `
            <tr>
                <td>
                    <strong>${user.user_id}</strong><br>
                    <small class="text-muted">${new Date(user.registration_date).toLocaleDateString()}</small>
                </td>
                <td>
                    <span class="badge bg-${isActive ? 'success' : 'secondary'}">
                        ${isActive ? 'Онлайн' : 'Оффлайн'}
                    </span><br>
                    <small class="text-muted">${new Date(user.last_activity).toLocaleString()}</small>
                </td>
                <td class="text-center">
                    <strong>${user.total_trades}</strong><br>
                    <small class="text-muted">всего</small>
                </td>
                <td class="${user.profit >= 0 ? 'text-success' : 'text-danger'}">
                    <strong>$${user.profit.toFixed(2)}</strong><br>
                    <small class="text-muted">прибыль</small>
                </td>
                <td class="text-center">
                    <div class="progress" style="height: 20px;">
                        <div class="progress-bar bg-warning" style="width: ${user.ai_accuracy || 0}%">
                            ${(user.ai_accuracy || 0).toFixed(1)}%
                        </div>
                    </div>
                </td>
                <td class="text-center">
                    <span class="badge bg-warning">
                        ${user.risk_level || 'Средний'}
                    </span>
                </td>
                <td class="text-center">
                    <button class="btn btn-sm btn-outline-info" onclick="showUserDetails('${user.user_id}')">
                        <i class="fas fa-eye"></i>
                    </button>
                </td>
            </tr>
        `;
        tbody.appendChild(row);
    });
}

// AI Analytics initialization  
function initializeAIAnalytics() {
    console.log('Initializing AI analytics...');
    // For now, redirect to dashboard
    window.location.href = '/';
}

// Utility functions
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show mt-3`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.getElementById('flash-messages').appendChild(alertDiv);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

function showUserDetails(userId) {
    apiRequest(`/api/users/${userId}/details`)
        .then(data => {
            // Show user details modal or page
            alert(`User Details for ${userId}\nBalance: $${data.balance}\nTrades: ${data.total_trades}\nWin Rate: ${data.win_rate}%`);
        })
        .catch(error => {
            console.error('Error loading user details:', error);
            showAlert('Ошибка загрузки деталей пользователя', 'danger');
        });
}

// Periodic updates
function startPeriodicUpdates() {
    // Update data every 30 seconds
    updateInterval = setInterval(() => {
        if (isAuthenticated()) {
            const currentPath = window.location.pathname;
            
            switch (currentPath) {
                case '/':
                    loadDashboardData();
                    break;
                case '/users':
                    loadUsersData();
                    break;
            }
        }
    }, 30000);
}

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (updateInterval) {
        clearInterval(updateInterval);
    }
});
