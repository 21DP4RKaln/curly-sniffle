// Основной JavaScript файл

// Глобальные переменные
let ws = null;
let isConnected = false;

// Инициализация при загрузке страницы  
document.addEventListener('DOMContentLoaded', function() {
    initializeWebSocket();
    setupEventListeners();
    startPeriodicUpdates();
});

// Настройка WebSocket для реального времени
function initializeWebSocket() {
    if (!window.WebSocket) {
        console.log('WebSocket не поддерживается браузером');
        return;
    }
    
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    
    try {
        ws = new WebSocket(wsUrl);
        
        ws.onopen = function() {
            console.log('WebSocket подключен');
            isConnected = true;
            showConnectionStatus('connected');
        };
        
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            handleRealtimeUpdate(data);
        };
        
        ws.onclose = function() {
            console.log('WebSocket отключен');
            isConnected = false;
            showConnectionStatus('disconnected');
            
            // Переподключение через 5 секунд
            setTimeout(initializeWebSocket, 5000);
        };
        
        ws.onerror = function(error) {
            console.error('Ошибка WebSocket:', error);
            showConnectionStatus('error');
        };
    } catch (error) {
        console.error('Ошибка создания WebSocket:', error);
    }
}

// Обработка обновлений в реальном времени
function handleRealtimeUpdate(data) {
    switch(data.type) {
        case 'trade_update':
            updateTradeInTable(data.data);
            updateStatistics(data.statistics);
            break;
        case 'ai_prediction':
            showAIPredictionNotification(data.data);
            break;
        case 'user_activity':
            updateUserActivity(data.data);
            break;
        case 'system_alert':
            showSystemAlert(data.data);
            break;
        default:
            console.log('Неизвестный тип обновления:', data.type);
    }
}

// Показать статус подключения
function showConnectionStatus(status) {
    const statusElement = document.getElementById('connection-status');
    if (!statusElement) return;
    
    switch(status) {
        case 'connected':
            statusElement.innerHTML = '<i class="fas fa-circle text-success"></i> Подключено';
            break;
        case 'disconnected':
            statusElement.innerHTML = '<i class="fas fa-circle text-warning"></i> Переподключение...';
            break;
        case 'error':
            statusElement.innerHTML = '<i class="fas fa-circle text-danger"></i> Ошибка подключения';
            break;
    }
}

// Настройка обработчиков событий
function setupEventListeners() {
    // Обработка кликов по таблицам
    setupTableClickHandlers();
    
    // Обработка форм
    setupFormHandlers();
    
    // Обработка горячих клавиш
    setupKeyboardShortcuts();
}

function setupTableClickHandlers() {
    // Клик по строке таблицы пользователей
    document.addEventListener('click', function(e) {
        if (e.target.closest('tr[data-user-id]')) {
            const userId = e.target.closest('tr').getAttribute('data-user-id');
            if (userId) {
                showUserDetails(userId);
            }
        }
    });
}

function setupFormHandlers() {
    // Автоматическая отправка форм при изменении
    const autoSubmitSelects = document.querySelectorAll('.auto-submit');
    autoSubmitSelects.forEach(select => {
        select.addEventListener('change', function() {
            this.form.submit();
        });
    });
}

function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl+R - обновить данные
        if (e.ctrlKey && e.key === 'r') {
            e.preventDefault();
            refreshCurrentPage();
        }
        
        // Esc - закрыть модальные окна
        if (e.key === 'Escape') {
            closeAllModals();
        }
    });
}

// Периодические обновления
function startPeriodicUpdates() {
    // Обновление каждые 30 секунд
    setInterval(function() {
        if (document.visibilityState === 'visible') {
            updatePageData();
        }
    }, 30000);
    
    // Обновление статуса пользователей каждые 10 секунд
    setInterval(updateUserStatuses, 10000);
}

// Обновление данных текущей страницы
function refreshCurrentPage() {
    const currentPage = getCurrentPage();
    
    switch(currentPage) {
        case 'dashboard':
            if (typeof loadDashboardData === 'function') {
                loadDashboardData();
            }
            break;
        case 'users':
            if (typeof loadUsers === 'function') {
                loadUsers();
            }
            break;
        case 'ai-analytics':
            if (typeof loadAIData === 'function') {
                loadAIData();
            }
            break;
    }
    
    showRefreshNotification();
}

function getCurrentPage() {
    const path = window.location.pathname;
    if (path.includes('users')) return 'users';
    if (path.includes('ai-analytics')) return 'ai-analytics';
    return 'dashboard';
}

// Универсальные функции для работы с данными
function updatePageData() {
    fetch('/api/page-data?' + new URLSearchParams({
        page: getCurrentPage(),
        timestamp: Date.now()
    }))
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Обновляем данные без перезагрузки графиков
            updateStatisticsOnly(data.statistics);
            updateTablesOnly(data.tables);
        }
    })
    .catch(error => console.error('Ошибка обновления данных:', error));
}

// Обновление статусов пользователей
function updateUserStatuses() {
    fetch('/api/user-statuses')
    .then(response => response.json())
    .then(data => {
        data.users.forEach(user => {
            updateUserStatusInTable(user.id, user.status);
        });
    })
    .catch(error => console.error('Ошибка обновления статусов:', error));
}

// Утилиты для работы с уведомлениями
function showNotification(message, type = 'info', duration = 3000) {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Автоматическое скрытие
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, duration);
}

function showRefreshNotification() {
    showNotification('<i class="fas fa-sync-alt me-2"></i>Данные обновлены', 'success', 2000);
}

function showAIPredictionNotification(data) {
    const icon = data.signal === 'BUY' ? 'fa-arrow-up text-success' :
                 data.signal === 'SELL' ? 'fa-arrow-down text-danger' : 'fa-minus text-warning';
    
    showNotification(
        `<i class="fas ${icon} me-2"></i>ИИ сигнал: ${data.signal} (${data.confidence.toFixed(1)}%)`,
        data.signal === 'BUY' ? 'success' : data.signal === 'SELL' ? 'danger' : 'warning',
        5000
    );
}

function showSystemAlert(data) {
    showNotification(
        `<i class="fas fa-exclamation-triangle me-2"></i>${data.message}`,
        data.level === 'error' ? 'danger' : 'warning',
        data.level === 'error' ? 10000 : 5000
    );
}

// Утилиты для работы с таблицами
function updateTradeInTable(trade) {
    const tableBody = document.getElementById('recent-trades');
    if (!tableBody) return;
    
    const row = createTradeRow(trade);
    
    // Добавляем в начало таблицы
    if (tableBody.children.length === 0) {
        tableBody.appendChild(row);
    } else {
        tableBody.insertBefore(row, tableBody.firstChild);
    }
    
    // Ограничиваем количество строк
    while (tableBody.children.length > 50) {
        tableBody.removeChild(tableBody.lastChild);
    }
    
    // Анимация новой строки
    row.style.backgroundColor = '#d4edda';
    setTimeout(() => {
        row.style.backgroundColor = '';
    }, 2000);
}

function createTradeRow(trade) {
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
    return row;
}

function updateUserStatusInTable(userId, status) {
    const userRow = document.querySelector(`tr[data-user-id="${userId}"]`);
    if (!userRow) return;
    
    const statusCell = userRow.querySelector('.user-status');
    if (statusCell) {
        const isActive = status === 'active';
        statusCell.innerHTML = `
            <span class="badge bg-${isActive ? 'success' : 'secondary'}">
                ${isActive ? 'Онлайн' : 'Офлайн'}
            </span>
        `;
    }
}

// Утилиты для работы с модальными окнами
function closeAllModals() {
    const modals = document.querySelectorAll('.modal.show');
    modals.forEach(modal => {
        const bsModal = bootstrap.Modal.getInstance(modal);
        if (bsModal) {
            bsModal.hide();
        }
    });
}

// Утилиты для форматирования данных
function formatCurrency(amount, currency = 'USD') {
    return new Intl.NumberFormat('ru-RU', {
        style: 'currency',
        currency: currency
    }).format(amount);
}

function formatPercentage(value) {
    return (value * 100).toFixed(2) + '%';
}

function formatNumber(number) {
    return new Intl.NumberFormat('ru-RU').format(number);
}

function formatDateTime(dateString) {
    return new Date(dateString).toLocaleString('ru-RU');
}

// Утилиты для работы с графиками
function updateChartData(chart, newData) {
    if (!chart || !newData) return;
    
    chart.data.labels = newData.labels || chart.data.labels;
    
    if (newData.datasets) {
        newData.datasets.forEach((dataset, index) => {
            if (chart.data.datasets[index]) {
                chart.data.datasets[index].data = dataset.data;
            }
        });
    }
    
    chart.update('none'); // Без анимации для плавности
}

// Обработка ошибок
function handleApiError(error, userMessage = 'Произошла ошибка') {
    console.error('API Error:', error);
    
    if (error.response) {
        // Ошибка от сервера
        showNotification(
            `${userMessage}: ${error.response.status} - ${error.response.statusText}`,
            'danger',
            5000
        );
    } else if (error.request) {
        // Ошибка сети
        showNotification(
            'Ошибка сети. Проверьте подключение к интернету.',
            'warning',
            5000
        );
    } else {
        // Другие ошибки
        showNotification(userMessage, 'danger', 5000);
    }
}

// Экспорт функций для использования в других скриптах
window.TradingBot = {
    showNotification,
    formatCurrency,
    formatPercentage,
    formatNumber,
    formatDateTime,
    updateChartData,
    handleApiError,
    refreshCurrentPage
};
