// ==================== 应用状态 ====================
const AppState = {
    currentPanel: 'lst',
    currentMode: 'like2',
    currentSingleMode: 'img',
    currentAo3Mode: 'work',
    isRunning: false,
    pollInterval: null
};

// ==================== 初始化 ====================
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initModeCards();
    initTauri();
    initContextMenu();
    initTooltips();
    loadConfig();
});

// ==================== 导航系统 ====================
function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const panelId = item.dataset.panel;
            switchPanel(panelId);
        });
    });
}

function switchPanel(panelId) {
    // 更新导航状态
    document.querySelectorAll('.nav-item').forEach(nav => {
        nav.classList.toggle('active', nav.dataset.panel === panelId);
    });
    
    // 切换面板
    document.querySelectorAll('.panel').forEach(panel => {
        panel.classList.remove('active');
    });
    document.getElementById(`panel-${panelId}`).classList.add('active');
    
    AppState.currentPanel = panelId;
}

// ==================== 模式卡片 ====================
function initModeCards() {
    // LST 模式
    document.querySelectorAll('[data-mode]').forEach(card => {
        card.addEventListener('click', () => {
            document.querySelectorAll('[data-mode]').forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
            AppState.currentMode = card.dataset.mode;
        });
    });

    // 单篇模式
    document.querySelectorAll('[data-single-mode]').forEach(card => {
        card.addEventListener('click', () => {
            document.querySelectorAll('[data-single-mode]').forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
            AppState.currentSingleMode = card.dataset.singleMode;
        });
    });

    // AO3 模式
    document.querySelectorAll('[data-ao3-mode]').forEach(card => {
        card.addEventListener('click', () => {
            document.querySelectorAll('[data-ao3-mode]').forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
            AppState.currentAo3Mode = card.dataset.ao3Mode;
        });
    });
}

// ==================== Tauri 集成 ====================
function initTauri() {
    // 检测 Tauri 环境 - 支持 Tauri 1.x 和 2.x
    const isTauri = window.__TAURI__ !== undefined || 
                    window.__TAURI_INTERNALS__ !== undefined ||
                    navigator.userAgent.includes('Tauri');
    
    console.log('Tauri 检测:', isTauri, window.__TAURI__);
    
    if (!isTauri) {
        // 非 Tauri 环境隐藏标题栏
        const titlebar = document.getElementById('titlebar');
        if (titlebar) titlebar.style.display = 'none';
        const container = document.querySelector('.app-container');
        if (container) container.style.paddingTop = '0';
        return;
    }

    console.log('🌊 Tauri 环境已检测');

    // 等待 Tauri API 加载完成
    const setupWindowControls = async () => {
        try {
            let appWindow;
            
            // Tauri 2.x API
            if (window.__TAURI__ && window.__TAURI__.window) {
                const { getCurrentWindow } = window.__TAURI__.window;
                appWindow = getCurrentWindow();
            } 
            // Tauri 1.x API
            else if (window.__TAURI__ && window.__TAURI__.window) {
                const { appWindow: aw } = window.__TAURI__.window;
                appWindow = aw;
            }
            // 尝试动态导入
            else {
                const { getCurrentWindow } = await import('@tauri-apps/api/window');
                appWindow = getCurrentWindow();
            }

            if (!appWindow) {
                console.error('无法获取 Tauri 窗口实例');
                return;
            }

            const btnMinimize = document.getElementById('btn-minimize');
            const btnMaximize = document.getElementById('btn-maximize');
            const btnClose = document.getElementById('btn-close');

            if (btnMinimize) {
                btnMinimize.onclick = () => {
                    console.log('最小化');
                    appWindow.minimize();
                };
            }
            
            if (btnMaximize) {
                btnMaximize.onclick = async () => {
                    console.log('最大化/还原');
                    if (await appWindow.isMaximized()) {
                        appWindow.unmaximize();
                    } else {
                        appWindow.maximize();
                    }
                };
            }
            
            if (btnClose) {
                btnClose.onclick = () => {
                    console.log('关闭');
                    appWindow.close();
                };
            }

            // 双击最大化
            const titlebarLeft = document.querySelector('.titlebar-left');
            if (titlebarLeft) {
                titlebarLeft.addEventListener('dblclick', async () => {
                    if (await appWindow.isMaximized()) {
                        appWindow.unmaximize();
                    } else {
                        appWindow.maximize();
                    }
                });
            }

            console.log('窗口控制按钮已绑定');
        } catch (e) {
            console.error('Tauri 窗口控制初始化失败:', e);
        }
    };

    // 延迟执行确保 API 加载完成
    if (document.readyState === 'complete') {
        setupWindowControls();
    } else {
        window.addEventListener('load', setupWindowControls);
    }
}

// ==================== 配置管理 ====================
async function loadConfig() {
    try {
        const res = await fetch('/api/config');
        const data = await res.json();
        const loginKeyEl = document.getElementById('loginKey');
        if (loginKeyEl) loginKeyEl.value = data.login_key;
        updateAuthStatus(data.has_auth);
    } catch (e) {
        console.error('加载配置失败:', e);
    }
}

window.saveConfig = async function() {
    const loginKey = document.getElementById('loginKey').value;
    const loginAuth = document.getElementById('loginAuth').value;

    try {
        const res = await fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ login_key: loginKey, login_auth: loginAuth })
        });
        const data = await res.json();
        if (data.success) {
            showNotification('配置保存成功！', 'success');
            loadConfig();
        }
    } catch (e) {
        showNotification('保存失败: ' + e.message, 'error');
    }
};

function updateAuthStatus(hasAuth) {
    const el = document.getElementById('authStatus');
    if (!el) return;
    
    if (hasAuth) {
        el.textContent = '已配置 ✓';
        el.classList.add('success');
        el.classList.remove('error');
    } else {
        el.textContent = '未配置';
        el.classList.add('error');
        el.classList.remove('success');
    }
}

// ==================== 任务控制 ====================
window.startLstTask = async function() {
    const url = document.getElementById('lstUrl').value.trim();
    if (!url) return showNotification('请输入链接地址', 'error');

    await startTask('like_share_tag', {
        url,
        mode: AppState.currentMode,
        save_mode: {
            article: document.getElementById('saveArticle').checked ? 1 : 0,
            text: document.getElementById('saveText').checked ? 1 : 0,
            'long article': document.getElementById('saveLong').checked ? 1 : 0,
            img: document.getElementById('saveImg').checked ? 1 : 0
        },
        start_time: document.getElementById('startTime').value,
        export_pdf: document.getElementById('lstExportPdf').checked
    });
};

window.startAuthorImgTask = async function() {
    const url = document.getElementById('authorImgUrl').value.trim();
    if (!url) return showNotification('请输入作者主页链接', 'error');

    await startTask('author_img', {
        author_url: url,
        start_time: document.getElementById('imgStartTime').value,
        end_time: document.getElementById('imgEndTime').value
    });
};

window.startAuthorTxtTask = async function() {
    const url = document.getElementById('authorTxtUrl').value.trim();
    if (!url) return showNotification('请输入作者主页链接', 'error');
    await startTask('author_txt', { author_url: url });
};

window.startSingleTask = async function() {
    const urls = document.getElementById('singleUrls').value
        .split('\n').map(u => u.trim()).filter(u => u);
    if (!urls.length) return showNotification('请输入至少一个链接', 'error');

    const type = AppState.currentSingleMode === 'img' ? 'single_img' : 'single_txt';
    await startTask(type, { urls });
};

window.startAo3Task = async function() {
    const urls = document.getElementById('ao3Urls').value
        .split('\n').map(u => u.trim()).filter(u => u);
    if (!urls.length) return showNotification('请输入至少一个 AO3 链接', 'error');

    await startTask('ao3', {
        urls,
        mode: AppState.currentAo3Mode,
        download_chapters: document.getElementById('ao3DownloadChapters').checked,
        save_metadata: document.getElementById('ao3SaveMetadata').checked,
        export_pdf: document.getElementById('ao3ExportPdf').checked,
        max_pages: parseInt(document.getElementById('ao3MaxPages').value) || 5
    });
};

async function startTask(type, params) {
    try {
        const res = await fetch('/api/task/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type, params })
        });
        const data = await res.json();

        if (data.success) {
            AppState.isRunning = true;
            updateRunningState(true);
            showProgress(true);
            startPolling();
            showNotification('任务已启动', 'success');
        } else {
            showNotification(data.message, 'error');
        }
    } catch (e) {
        showNotification('启动失败: ' + e.message, 'error');
    }
}

// ==================== 进度追踪 ====================
function showProgress(show) {
    const section = document.getElementById('progressSection');
    if (section) section.classList.toggle('active', show);
}

function updateRunningState(running) {
    const dot = document.getElementById('statusDot');
    const label = document.getElementById('statusLabel');
    
    if (dot && label) {
        if (running) {
            dot.classList.add('running');
            label.textContent = '运行中';
        } else {
            dot.classList.remove('running');
            label.textContent = '就绪';
        }
    }
}

function startPolling() {
    if (AppState.pollInterval) clearInterval(AppState.pollInterval);
    
    AppState.pollInterval = setInterval(async () => {
        try {
            const res = await fetch('/api/task/status');
            const data = await res.json();

            // 更新进度
            const progressFill = document.getElementById('progressFill');
            const progressPercent = document.getElementById('progressPercent');
            const progressMessage = document.getElementById('progressMessage');

            if (progressFill) progressFill.style.width = data.progress + '%';
            if (progressPercent) progressPercent.textContent = data.progress + '%';
            if (progressMessage) progressMessage.textContent = data.message;

            // 更新日志
            const logContent = document.getElementById('logContent');
            if (logContent) {
                logContent.innerHTML = data.logs.map(log => 
                    `<div class="log-line">${escapeHtml(log)}</div>`
                ).join('');
                logContent.scrollTop = logContent.scrollHeight;
            }

            // 检查完成
            if (!data.running && data.progress >= 100) {
                clearInterval(AppState.pollInterval);
                AppState.isRunning = false;
                updateRunningState(false);
                showNotification('任务完成！', 'success');
            }
        } catch (e) {
            console.error('状态获取失败:', e);
        }
    }, 500);
}

// ==================== 工具函数 ====================
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showNotification(message, type = 'info') {
    // 创建一个临时的 toast 通知
    const toast = document.createElement('div');
    toast.style.position = 'fixed';
    toast.style.bottom = '20px';
    toast.style.left = '50%';
    toast.style.transform = 'translateX(-50%)';
    toast.style.padding = '12px 24px';
    toast.style.borderRadius = '8px';
    toast.style.background = type === 'error' ? '#b00020' : '#00bcd4';
    toast.style.color = 'white';
    toast.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
    toast.style.zIndex = '10001';
    toast.style.fontSize = '14px';
    toast.style.fontWeight = '500';
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
    toast.textContent = message;

    document.body.appendChild(toast);

    // 动画显示
    requestAnimationFrame(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateX(-50%) translateY(-10px)';
    });

    // 3秒后移除
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(-50%) translateY(0)';
        setTimeout(() => document.body.removeChild(toast), 300);
    }, 3000);
}

// ==================== 自定义右键菜单 ====================
let contextMenu = null;

function initContextMenu() {
    // 创建菜单元素
    contextMenu = document.createElement('div');
    contextMenu.className = 'context-menu';
    contextMenu.innerHTML = `
        <div class="context-menu-item" data-action="copy">
            <span class="context-menu-item-icon">📋</span>
            <span class="context-menu-item-text">复制</span>
            <span class="context-menu-item-shortcut">Ctrl+C</span>
        </div>
        <div class="context-menu-item" data-action="paste">
            <span class="context-menu-item-icon">📄</span>
            <span class="context-menu-item-text">粘贴</span>
            <span class="context-menu-item-shortcut">Ctrl+V</span>
        </div>
        <div class="context-menu-item" data-action="cut">
            <span class="context-menu-item-icon">✂️</span>
            <span class="context-menu-item-text">剪切</span>
            <span class="context-menu-item-shortcut">Ctrl+X</span>
        </div>
        <div class="context-menu-divider"></div>
        <div class="context-menu-item" data-action="selectall">
            <span class="context-menu-item-icon">📝</span>
            <span class="context-menu-item-text">全选</span>
            <span class="context-menu-item-shortcut">Ctrl+A</span>
        </div>
        <div class="context-menu-divider"></div>
        <div class="context-menu-item" data-action="refresh">
            <span class="context-menu-item-icon">🔄</span>
            <span class="context-menu-item-text">刷新页面</span>
            <span class="context-menu-item-shortcut">F5</span>
        </div>
        <div class="context-menu-item" data-action="devtools">
            <span class="context-menu-item-icon">🛠️</span>
            <span class="context-menu-item-text">开发者工具</span>
            <span class="context-menu-item-shortcut">F12</span>
        </div>
    `;
    document.body.appendChild(contextMenu);

    // 禁用默认右键菜单
    document.addEventListener('contextmenu', (e) => {
        e.preventDefault();
        showContextMenu(e.clientX, e.clientY, e.target);
    });

    // 点击其他地方关闭菜单
    document.addEventListener('click', () => hideContextMenu());
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') hideContextMenu();
    });

    // 菜单项点击事件
    contextMenu.querySelectorAll('.context-menu-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.stopPropagation();
            const action = item.dataset.action;
            executeContextAction(action);
            hideContextMenu();
        });
    });
}

function showContextMenu(x, y, target) {
    // 更新菜单项状态
    updateContextMenuItems(target);

    // 显示菜单
    contextMenu.classList.add('show');

    // 计算位置，防止超出屏幕
    const menuRect = contextMenu.getBoundingClientRect();
    const windowWidth = window.innerWidth;
    const windowHeight = window.innerHeight;

    let posX = x;
    let posY = y;

    if (x + menuRect.width > windowWidth) {
        posX = windowWidth - menuRect.width - 10;
    }
    if (y + menuRect.height > windowHeight) {
        posY = windowHeight - menuRect.height - 10;
    }

    contextMenu.style.left = posX + 'px';
    contextMenu.style.top = posY + 'px';
}

function hideContextMenu() {
    if (contextMenu) {
        contextMenu.classList.remove('show');
    }
}

function updateContextMenuItems(target) {
    const hasSelection = window.getSelection().toString().length > 0;
    const isEditable = target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable;

    // 复制 - 有选中内容时可用
    const copyItem = contextMenu.querySelector('[data-action="copy"]');
    if (copyItem) {
        copyItem.classList.toggle('disabled', !hasSelection);
    }

    // 剪切 - 有选中内容且可编辑时可用
    const cutItem = contextMenu.querySelector('[data-action="cut"]');
    if (cutItem) {
        cutItem.classList.toggle('disabled', !hasSelection || !isEditable);
    }

    // 粘贴 - 可编辑时可用
    const pasteItem = contextMenu.querySelector('[data-action="paste"]');
    if (pasteItem) {
        pasteItem.classList.toggle('disabled', !isEditable);
    }
}

async function executeContextAction(action) {
    switch (action) {
        case 'copy':
            try {
                const selection = window.getSelection().toString();
                if (selection) {
                    await navigator.clipboard.writeText(selection);
                    showNotification('已复制到剪贴板', 'success');
                }
            } catch (e) {
                document.execCommand('copy');
            }
            break;

        case 'paste':
            try {
                const text = await navigator.clipboard.readText();
                const activeEl = document.activeElement;
                if (activeEl.tagName === 'INPUT' || activeEl.tagName === 'TEXTAREA') {
                    const start = activeEl.selectionStart;
                    const end = activeEl.selectionEnd;
                    activeEl.value = activeEl.value.slice(0, start) + text + activeEl.value.slice(end);
                    activeEl.selectionStart = activeEl.selectionEnd = start + text.length;
                }
            } catch (e) {
                document.execCommand('paste');
            }
            break;

        case 'cut':
            try {
                const selection = window.getSelection().toString();
                if (selection) {
                    await navigator.clipboard.writeText(selection);
                    document.execCommand('delete');
                    showNotification('已剪切到剪贴板', 'success');
                }
            } catch (e) {
                document.execCommand('cut');
            }
            break;

        case 'selectall':
            const activeEl = document.activeElement;
            if (activeEl.tagName === 'INPUT' || activeEl.tagName === 'TEXTAREA') {
                activeEl.select();
            } else {
                document.execCommand('selectAll');
            }
            break;

        case 'refresh':
            window.location.reload();
            break;

        case 'devtools':
            // 在 Tauri 中可以通过 API 打开开发者工具
            if (window.__TAURI__) {
                showNotification('按 F12 打开开发者工具', 'info');
            } else {
                showNotification('按 F12 打开开发者工具', 'info');
            }
            break;
    }
}

// ==================== 工具提示 ====================
let tooltipEl = null;

function initTooltips() {
    // 创建工具提示元素
    tooltipEl = document.createElement('div');
    tooltipEl.className = 'tooltip';
    document.body.appendChild(tooltipEl);

    // 为所有带 title 属性的元素添加自定义工具提示
    document.querySelectorAll('[title]').forEach(el => {
        const title = el.getAttribute('title');
        el.removeAttribute('title');
        el.dataset.tooltip = title;

        el.addEventListener('mouseenter', showTooltip);
        el.addEventListener('mouseleave', hideTooltip);
        el.addEventListener('mousemove', moveTooltip);
    });
}

function showTooltip(e) {
    const text = e.target.dataset.tooltip;
    if (!text) return;

    tooltipEl.textContent = text;
    tooltipEl.classList.add('show', 'top');

    positionTooltip(e);
}

function hideTooltip() {
    tooltipEl.classList.remove('show');
}

function moveTooltip(e) {
    positionTooltip(e);
}

function positionTooltip(e) {
    const x = e.clientX;
    const y = e.clientY;
    const rect = tooltipEl.getBoundingClientRect();

    let posX = x - rect.width / 2;
    let posY = y - rect.height - 12;

    // 边界检测
    if (posX < 10) posX = 10;
    if (posX + rect.width > window.innerWidth - 10) {
        posX = window.innerWidth - rect.width - 10;
    }
    if (posY < 10) {
        posY = y + 20;
        tooltipEl.classList.remove('top');
        tooltipEl.classList.add('bottom');
    }

    tooltipEl.style.left = posX + 'px';
    tooltipEl.style.top = posY + 'px';
}

