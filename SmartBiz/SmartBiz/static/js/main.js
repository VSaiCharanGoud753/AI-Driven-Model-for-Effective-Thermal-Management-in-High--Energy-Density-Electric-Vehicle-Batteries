/* ==========================================================================
   SmartBiz AI Enterprise Dashboard - Main Interactivity Script
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    initSidebarToggle();
    initDarkModeToggle();
    initGlobalSearch();
    initNotificationBell();
    initKeyboardShortcuts();
    initAutoDismissToasts();
});

/* 1. Sidebar Collapse / Expand Toggle */
function initSidebarToggle() {
    const toggleBtn = document.getElementById('sidebarToggle');
    const sidebar = document.querySelector('.sidebar');
    const mainContent = document.querySelector('.main-content');
    
    if (toggleBtn && sidebar && mainContent) {
        toggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
            mainContent.classList.toggle('expanded');
            
            // Trigger window resize so Chart.js canvases adapt gracefully
            setTimeout(() => {
                window.dispatchEvent(new Event('resize'));
            }, 350);
        });
    }
}

/* 2. Dark Mode / Light Mode Toggle with localStorage Persistence */
function initDarkModeToggle() {
    const darkModeBtn = document.getElementById('darkModeToggle');
    const body = document.body;
    
    // Check saved preference or OS default
    const savedTheme = localStorage.getItem('smartbiz_theme');
    if (savedTheme === 'dark' || (!savedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        body.classList.add('dark-mode');
        if (darkModeBtn) darkModeBtn.innerHTML = '<i class="fas fa-sun text-warning"></i>';
    } else {
        body.classList.remove('dark-mode');
        if (darkModeBtn) darkModeBtn.innerHTML = '<i class="fas fa-moon text-secondary"></i>';
    }
    
    if (darkModeBtn) {
        darkModeBtn.addEventListener('click', () => {
            body.classList.toggle('dark-mode');
            const isDark = body.classList.contains('dark-mode');
            
            localStorage.setItem('smartbiz_theme', isDark ? 'dark' : 'light');
            darkModeBtn.innerHTML = isDark ? '<i class="fas fa-sun text-warning"></i>' : '<i class="fas fa-moon text-secondary"></i>';
            
            // Sync with backend settings if logged in
            fetch('/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: `action=theme&dark_mode=${isDark}`
            }).catch(() => {});
            
            // Dynamically update Chart.js theme fonts and grid colors
            if (typeof updateChartsTheme === 'function') {
                updateChartsTheme(isDark);
            }
            
            showToast(`Switched to ${isDark ? 'Dark' : 'Light'} Mode`, 'info');
        });
    }
}

/* 3. Global Search Bar with Live AJAX Dropdown */
function initGlobalSearch() {
    const searchInput = document.getElementById('globalSearchInput');
    const searchDropdown = document.getElementById('globalSearchDropdown');
    let debounceTimer;
    
    if (searchInput && searchDropdown) {
        searchInput.addEventListener('input', (e) => {
            clearTimeout(debounceTimer);
            const query = e.target.value.trim();
            
            if (query.length < 2) {
                searchDropdown.style.display = 'none';
                return;
            }
            
            debounceTimer = setTimeout(() => {
                fetch(`/api/search?q=${encodeURIComponent(query)}`)
                    .then(res => res.json())
                    .then(data => {
                        if (data.status === 'success' && data.results.length > 0) {
                            let html = '<div class="p-2">';
                            data.results.forEach(item => {
                                html += `
                                    <a href="${item.url}" class="d-flex align-items-center gap-3 p-2 rounded text-decoration-none nav-link">
                                        <div class="kpi-icon mb-0" style="width:36px;height:36px;font-size:1rem;">
                                            <i class="fas ${item.icon}"></i>
                                        </div>
                                        <div>
                                            <div class="fw-bold text-primary">${item.title} <span class="badge bg-secondary ms-1" style="font-size:0.65rem;">${item.type}</span></div>
                                            <div class="text-muted" style="font-size:0.75rem;">${item.subtitle}</div>
                                        </div>
                                    </a>
                                `;
                            });
                            html += '</div>';
                            searchDropdown.innerHTML = html;
                            searchDropdown.style.display = 'block';
                        } else {
                            searchDropdown.innerHTML = '<div class="p-3 text-center text-muted">No matching products, customers, or invoices found.</div>';
                            searchDropdown.style.display = 'block';
                        }
                    }).catch(() => {
                        searchDropdown.style.display = 'none';
                    });
            }, 250);
        });
        
        // Hide dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!searchInput.contains(e.target) && !searchDropdown.contains(e.target)) {
                searchDropdown.style.display = 'none';
            }
        });
    }
}

/* 4. Notification Bell Dropdown & Read Handlers */
function initNotificationBell() {
    const bellBtn = document.getElementById('notificationBellBtn');
    const notifBadge = document.getElementById('notificationBadge');
    const notifList = document.getElementById('notificationList');
    const markAllBtn = document.getElementById('markAllReadBtn');
    
    if (bellBtn && notifList) {
        bellBtn.addEventListener('click', () => {
            fetch('/api/notifications')
                .then(res => res.json())
                .then(data => {
                    if (data.status === 'success') {
                        if (notifBadge) {
                            if (data.unread_count > 0) {
                                notifBadge.textContent = data.unread_count;
                                notifBadge.style.display = 'inline-block';
                            } else {
                                notifBadge.style.display = 'none';
                            }
                        }
                        
                        if (data.notifications.length > 0) {
                            let html = '';
                            data.notifications.forEach(n => {
                                const bgClass = n.is_read ? '' : 'bg-light bg-opacity-10 fw-500';
                                const iconColor = n.type === 'alert' || n.type === 'danger' ? 'text-danger' : n.type === 'warning' ? 'text-warning' : n.type === 'success' ? 'text-success' : 'text-primary';
                                html += `
                                    <a href="${n.link}" class="list-group-item list-group-item-action p-3 border-bottom ${bgClass}" onclick="markNotificationRead(${n.id})">
                                        <div class="d-flex align-items-start gap-2">
                                            <i class="fas fa-circle ${iconColor} mt-1" style="font-size:0.5rem;"></i>
                                            <div>
                                                <div class="fw-bold" style="font-size:0.85rem;">${n.title}</div>
                                                <div class="text-muted" style="font-size:0.75rem;">${n.message}</div>
                                                <small class="text-secondary" style="font-size:0.65rem;">${n.created_at}</small>
                                            </div>
                                        </div>
                                    </a>
                                `;
                            });
                            notifList.innerHTML = html;
                        } else {
                            notifList.innerHTML = '<div class="p-4 text-center text-muted">No notifications at this time.</div>';
                        }
                    }
                });
        });
        
        if (markAllBtn) {
            markAllBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                fetch('/api/notifications/read-all', { method: 'POST' })
                    .then(() => {
                        if (notifBadge) notifBadge.style.display = 'none';
                        showToast('All notifications marked as read', 'success');
                        bellBtn.click(); # refresh dropdown
                    });
            });
        }
    }
}

function markNotificationRead(id) {
    fetch(`/api/notifications/read/${id}`, { method: 'POST' });
}

/* 5. Keyboard Shortcuts (Ctrl+K for search, Ctrl+B for sidebar) */
function initKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Ctrl+K or Cmd+K focuses global search
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
            e.preventDefault();
            const searchInput = document.getElementById('globalSearchInput');
            if (searchInput) searchInput.focus();
        }
        // Ctrl+B toggles sidebar
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'b') {
            e.preventDefault();
            const toggleBtn = document.getElementById('sidebarToggle');
            if (toggleBtn) toggleBtn.click();
        }
    });
}

/* 6. Toast Notification Generator */
function showToast(message, type = 'info') {
    let container = document.getElementById('toastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    
    const icon = type === 'success' ? 'fa-check-circle text-success' :
                 type === 'error' ? 'fa-exclamation-circle text-danger' :
                 type === 'warning' ? 'fa-exclamation-triangle text-warning' : 'fa-info-circle text-primary';
                 
    const toast = document.createElement('div');
    toast.className = 'toast-message glass-card';
    toast.innerHTML = `
        <i class="fas ${icon} fs-5"></i>
        <div class="fw-500">${message}</div>
        <button type="button" class="btn-close ms-auto" onclick="this.parentElement.remove()"></button>
    `;
    
    container.appendChild(toast);
    setTimeout(() => {
        if (toast.parentElement) toast.remove();
    }, 4500);
}

function initAutoDismissToasts() {
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.classList.add('fade');
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });
}
