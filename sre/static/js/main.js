// SRE Dashboard Client Logic

document.addEventListener('DOMContentLoaded', () => {
    // 1. Navigation & Routing
    const menuItems = {
        '#overview': document.getElementById('menu-overview'),
        '#ping-check': document.getElementById('menu-ping'),
        '#logs': document.getElementById('menu-logs'),
        '#stocks-company': document.getElementById('menu-stocks-company')
    };

    const sections = {
        '#overview': document.getElementById('overview'),
        '#ping-check': document.getElementById('ping-check'),
        '#logs': document.getElementById('logs'),
        '#stocks-company': document.getElementById('stocks-company')
    };

    function navigateToSection(hash) {
        const targetHash = hash || '#overview';
        
        // Hide all sections, remove active menu classes
        Object.keys(sections).forEach(key => {
            sections[key].classList.add('hidden');
            menuItems[key].classList.remove('active');
        });

        // Show selected section, add active class
        if (sections[targetHash]) {
            sections[targetHash].classList.remove('hidden');
            menuItems[targetHash].classList.add('active');
        }
    }

    // Navigation event listeners
    Object.keys(menuItems).forEach(hash => {
        menuItems[hash].addEventListener('click', (e) => {
            e.preventDefault();
            window.location.hash = hash;
            navigateToSection(hash);
        });
    });

    // Handle back/forward buttons and direct links
    window.addEventListener('hashchange', () => {
        navigateToSection(window.location.hash);
    });

    // Initial navigation
    navigateToSection(window.location.hash);

    // 2. Theme Management
    const themeBtn = document.getElementById('theme-toggle-btn');
    const toggleIcon = themeBtn.querySelector('.toggle-icon');

    // Load saved theme or default to dark
    const savedTheme = localStorage.getItem('sre-theme') || 'dark';
    if (savedTheme === 'light') {
        document.body.classList.remove('dark-theme');
        document.body.classList.add('light-theme');
        toggleIcon.textContent = '☀️';
    } else {
        document.body.classList.add('dark-theme');
        document.body.classList.remove('light-theme');
        toggleIcon.textContent = '🌙';
    }

    themeBtn.addEventListener('click', () => {
        if (document.body.classList.contains('dark-theme')) {
            document.body.classList.remove('dark-theme');
            document.body.classList.add('light-theme');
            toggleIcon.textContent = '☀️';
            localStorage.setItem('sre-theme', 'light');
        } else {
            document.body.classList.add('dark-theme');
            document.body.classList.remove('light-theme');
            toggleIcon.textContent = '🌙';
            localStorage.setItem('sre-theme', 'dark');
        }
    });

    // 3. System Metrics Polling & Chart drawing
    const metricsHistory = {
        cpu: [],
        latency: [],
        timestamps: []
    };
    const maxHistoryPoints = 30;

    // Elements
    const uptimeVal = document.getElementById('uptime-value');
    const cpuVal = document.getElementById('cpu-value');
    const cpuRadial = document.getElementById('cpu-radial-bar');
    const memoryVal = document.getElementById('memory-value');
    const memoryBar = document.getElementById('memory-bar');
    const diskVal = document.getElementById('disk-value');
    const diskBar = document.getElementById('disk-bar');
    const netInVal = document.getElementById('net-in-value');
    const netOutVal = document.getElementById('net-out-value');
    const latencyVal = document.getElementById('latency-value');

    // Chart Paths
    const cpuPath = document.getElementById('cpu-path');
    const latencyPath = document.getElementById('latency-path');

    function updateRadialProgress(element, percent) {
        // r = 40, Circumference = 2 * Math.PI * 40 = 251.2
        const circumference = 251.2;
        const offset = circumference - (percent / 100) * circumference;
        element.style.strokeDashoffset = offset;
    }

    function drawChart() {
        const width = 800;
        const height = 200;
        const count = metricsHistory.cpu.length;
        if (count < 2) return;

        let cpuD = '';
        let latencyD = '';

        for (let i = 0; i < count; i++) {
            const x = (i / (maxHistoryPoints - 1)) * width;
            
            // CPU: 0 - 100% -> 0 - 200px (higher values are near y=0, i.e., top)
            const cpuY = height - (metricsHistory.cpu[i] / 100) * (height - 20) - 10;
            
            // Latency: scale relative to max 120ms
            const rawLat = metricsHistory.latency[i];
            const latPercent = Math.min(100, (rawLat / 120) * 100);
            const latencyY = height - (latPercent / 100) * (height - 20) - 10;

            if (i === 0) {
                cpuD = `M ${x} ${cpuY}`;
                latencyD = `M ${x} ${latencyY}`;
            } else {
                cpuD += ` L ${x} ${cpuY}`;
                latencyD += ` L ${x} ${latencyY}`;
            }
        }

        cpuPath.setAttribute('d', cpuD);
        latencyPath.setAttribute('d', latencyD);
    }

    function pollMetrics() {
        fetch('/api/metrics')
            .then(res => res.json())
            .then(data => {
                // Update UI text values
                uptimeVal.textContent = data.uptime;
                cpuVal.textContent = `${data.cpu}%`;
                memoryVal.textContent = `${data.memory}%`;
                diskVal.textContent = `${data.disk}%`;
                netInVal.textContent = `${data.network_in} KB/s`;
                netOutVal.textContent = `${data.network_out} KB/s`;
                latencyVal.textContent = `${data.latency} ms`;

                // Update Progress animations
                updateRadialProgress(cpuRadial, data.cpu);
                memoryBar.style.width = `${data.memory}%`;
                diskBar.style.width = `${data.disk}%`;

                // Update charts
                metricsHistory.cpu.push(data.cpu);
                metricsHistory.latency.push(data.latency);
                metricsHistory.timestamps.push(data.timestamp);

                if (metricsHistory.cpu.length > maxHistoryPoints) {
                    metricsHistory.cpu.shift();
                    metricsHistory.latency.shift();
                    metricsHistory.timestamps.shift();
                }

                drawChart();
            })
            .catch(err => console.error('Error fetching metrics:', err));
    }

    // Run poll immediately, then every 2 seconds
    pollMetrics();
    setInterval(pollMetrics, 2000);

    // 4. Ping Health Checker
    const pingForm = document.getElementById('ping-form');
    const pingUrlInput = document.getElementById('ping-url');
    const pingSubmit = document.getElementById('ping-submit');
    const pingResultContainer = document.getElementById('ping-result-container');
    const resStatusBadge = document.getElementById('res-status-badge');
    const resUrl = document.getElementById('res-url');
    const resCode = document.getElementById('res-code');
    const resLatency = document.getElementById('res-latency');
    const resTime = document.getElementById('res-time');
    const pingHistoryBody = document.getElementById('ping-history-body');

    pingForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const url = pingUrlInput.value.trim();
        if (!url) return;

        // Visual loading state
        pingSubmit.disabled = true;
        pingSubmit.querySelector('span').textContent = '檢測中...';

        fetch(`/api/ping?url=${encodeURIComponent(url)}`)
            .then(res => res.json())
            .then(data => {
                // Show result container
                pingResultContainer.classList.remove('hidden');

                // Update result card
                resUrl.textContent = data.url;
                resCode.textContent = data.status_code;
                resLatency.textContent = `${data.latency} ms`;
                resTime.textContent = data.timestamp.split(' ')[1]; // show time part only

                const statusLabel = data.status === 'UP' ? '正常' : '異常';
                resStatusBadge.textContent = statusLabel;
                if (data.status === 'UP') {
                    resStatusBadge.className = 'badge';
                } else {
                    resStatusBadge.className = 'badge red-badge';
                }

                // Add to table history (at the top)
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${data.url}</td>
                    <td><span class="badge ${data.status === 'UP' ? '' : 'red-badge'}">${statusLabel}</span></td>
                    <td>${data.status_code}</td>
                    <td>${data.latency} ms</td>
                    <td>${data.timestamp}</td>
                `;
                pingHistoryBody.insertBefore(tr, pingHistoryBody.firstChild);

                // Limit rows to 10
                if (pingHistoryBody.children.length > 10) {
                    pingHistoryBody.removeChild(pingHistoryBody.lastChild);
                }
            })
            .catch(err => {
                console.error('Error checking service:', err);
                alert('服務檢測失敗，請至控制台查看錯誤。');
            })
            .finally(() => {
                pingSubmit.disabled = false;
                pingSubmit.querySelector('span').textContent = '開始檢測';
            });
    });

    // 5. Log Stream Viewer
    const logTerminal = document.getElementById('log-terminal-body');
    const logFilterSelect = document.getElementById('log-filter-select');
    const clearLogsBtn = document.getElementById('clear-logs-btn');
    let displayedLogTimes = new Set();

    function formatLogLine(log, logId) {
        const line = document.createElement('div');
        line.className = `log-line log-${log.level.toLowerCase()}`;
        line.dataset.id = logId;
        
        line.innerHTML = `
            <span class="log-time">${log.timestamp}</span>
            <span class="log-tag">[${log.level}]</span>
            <span class="log-tag">${log.service}:</span>
            <span class="log-msg">${log.message}</span>
        `;
        return line;
    }

    function pollLogs() {
        const level = logFilterSelect.value;
        fetch(`/api/logs?level=${level}&limit=12`)
            .then(res => res.json())
            .then(logs => {
                // Determine if user is scrolled near bottom
                const isNearBottom = logTerminal.scrollHeight - logTerminal.clientHeight - logTerminal.scrollTop < 60;

                // Logs are in newest-first order from API. Reverse it to display chronologically.
                logs.reverse().forEach(log => {
                    const logId = `${log.timestamp}-${log.level}-${log.service}-${log.message.substring(0, 15)}`;
                    if (!displayedLogTimes.has(logId)) {
                        logTerminal.appendChild(formatLogLine(log, logId));
                        displayedLogTimes.add(logId);
                    }
                });

                // Prune old logs if they exceed 100 rows
                while (logTerminal.children.length > 100) {
                    const firstChild = logTerminal.firstChild;
                    if (firstChild) {
                        const idToRemove = firstChild.dataset.id;
                        if (idToRemove) {
                            displayedLogTimes.delete(idToRemove);
                        }
                        logTerminal.removeChild(firstChild);
                    }
                }

                // Scroll to bottom if appropriate
                if (isNearBottom) {
                    logTerminal.scrollTop = logTerminal.scrollHeight;
                }
            })
            .catch(err => console.error('Error fetching logs:', err));
    }

    // Refresh logs on select option filter change
    logFilterSelect.addEventListener('change', () => {
        logTerminal.innerHTML = '';
        displayedLogTimes.clear();
        pollLogs();
    });

    clearLogsBtn.addEventListener('click', () => {
        logTerminal.innerHTML = '';
        displayedLogTimes.clear();
    });

    // Initial logs poll and interval
    pollLogs();
    setInterval(pollLogs, 3000);

    // 6. Morning Stock (晨間股市) Monitor
    const stockGrid = document.getElementById('stock-ticker-grid');

    function getSparklinePath(history) {
        if (!history || history.length < 2) return '';
        const min = Math.min(...history);
        const max = Math.max(...history);
        const range = max - min === 0 ? 1 : max - min;
        const width = 100;
        const height = 24; // 24px height bounds
        return history.map((val, idx) => {
            const x = idx * (width / (history.length - 1));
            const y = height + 3 - ((val - min) / range) * height;
            return `${idx === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`;
        }).join(' ');
    }

    function pollStocks() {
        // Only fetch stock updates if the morning stock section is visible
        if (sections['#stocks-company'].classList.contains('hidden')) return;

        fetch('/api/stocks')
            .then(res => res.json())
            .then(stocks => {
                stocks.forEach(stock => {
                    const sparkPath = getSparklinePath(stock.history);
                    const isPositive = stock.change >= 0;
                    const cardId = `stock-card-${stock.ticker}`;
                    let card = document.getElementById(cardId);
                    
                    if (!card) {
                        card = document.createElement('div');
                        card.id = cardId;
                        card.className = 'card glass-card stock-card';
                        card.innerHTML = `
                            <div class="stock-card-header">
                                <div class="stock-card-meta">
                                    <span class="stock-ticker">${stock.ticker}</span>
                                    <span class="stock-name">${stock.name}</span>
                                </div>
                            </div>
                            <div class="stock-card-body">
                                <div class="stock-price-row">
                                    <span class="stock-price"></span>
                                    <span class="stock-change"></span>
                                </div>
                                <div class="stock-sparkline-wrapper">
                                    <svg class="stock-sparkline-svg" viewBox="0 0 100 30" preserveAspectRatio="none">
                                        <path d="" fill="none" stroke="" stroke-width="2"></path>
                                    </svg>
                                </div>
                            </div>
                        `;
                        stockGrid.appendChild(card);
                    }
                    
                    // Update content in-place
                    const priceEl = card.querySelector('.stock-price');
                    const changeEl = card.querySelector('.stock-change');
                    const pathEl = card.querySelector('.stock-sparkline-svg path');
                    
                    priceEl.textContent = `$${stock.price.toFixed(2)}`;
                    changeEl.textContent = `${isPositive ? '+' : ''}${stock.change.toFixed(2)} (${stock.change_percent.toFixed(2)}%)`;
                    
                    // Toggle positive/negative classes
                    changeEl.classList.toggle('positive', isPositive);
                    changeEl.classList.toggle('negative', !isPositive);
                    
                    // Update sparkline SVG path and color
                    pathEl.setAttribute('d', sparkPath);
                    pathEl.setAttribute('stroke', isPositive ? '#10b981' : '#ef4444');
                });
            })
            .catch(err => console.error('Error fetching stock data:', err));
    }

    // Poll stocks on navigation to #stocks-company, and set interval
    window.addEventListener('hashchange', () => {
        if (window.location.hash === '#stocks-company') {
            pollStocks();
        }
    });
    if (window.location.hash === '#stocks-company') {
        pollStocks();
    }
    setInterval(pollStocks, 2500);

    // 7. Afternoon Company (午後公司)
    const shiftsBody = document.getElementById('company-shifts-body');
    const incidentsBody = document.getElementById('company-incidents-body');
    const companyTerminal = document.getElementById('company-terminal-body');
    const actionBtns = document.querySelectorAll('.action-btn');

    function renderCompanyData(data) {
        // Render Shifts
        shiftsBody.innerHTML = '';
        data.shifts.forEach(shift => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>${shift.shift}</strong></td>
                <td>${shift.name}</td>
                <td><span class="badge">${shift.assignment}</span></td>
            `;
            shiftsBody.appendChild(tr);
        });

        // Render Incidents
        incidentsBody.innerHTML = '';
        data.incidents.forEach(inc => {
            let badgeClass = 'badge-pending';
            let statusText = '等待處理 (PENDING)';
            if (inc.status === 'INVESTIGATING') {
                badgeClass = 'badge-investigating';
                statusText = '調查中 (INVESTIGATING)';
            }
            if (inc.status === 'RESOLVED') {
                badgeClass = 'badge-resolved';
                statusText = '已解決 (RESOLVED)';
            }

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>${inc.id}</strong></td>
                <td>${inc.title}</td>
                <td>${inc.assignee}</td>
                <td><span class="badge ${badgeClass}">${statusText}</span></td>
                <td>${inc.time}</td>
            `;
            incidentsBody.appendChild(tr);
        });
    }

    function fetchCompanyInfo() {
        fetch('/api/company')
            .then(res => res.json())
            .then(data => renderCompanyData(data))
            .catch(err => console.error('Error fetching company info:', err));
    }

    // Set up action button listeners
    actionBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const action = btn.getAttribute('data-action');
            if (!action) return;

            // Visual feedback on button clicked
            const originalText = btn.textContent;
            btn.disabled = true;
            btn.textContent = '⏳ 正在執行...';

            companyTerminal.innerHTML = '[系統] 正在發送自動化復原指令至後端...';

            fetch('/api/company/action', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: action })
            })
            .then(res => res.json())
            .then(data => {
                if (data.status === 'SUCCESS') {
                    // Update incidents list
                    renderCompanyData({
                        shifts: Array.from(shiftsBody.children).map(tr => {
                            return {
                                shift: tr.children[0].textContent,
                                name: tr.children[1].textContent,
                                assignment: tr.children[2].textContent
                            };
                        }),
                        incidents: data.incidents
                    });

                    // Print log simulation to panel terminal
                    companyTerminal.innerHTML = '';
                    data.logs.forEach((logLine, index) => {
                        setTimeout(() => {
                            const line = document.createElement('div');
                            line.textContent = logLine;
                            // Color code info vs error/warning
                            if (logLine.includes('[ERROR]')) line.style.color = '#fda4af';
                            else if (logLine.includes('[WARNING]')) line.style.color = '#fde047';
                            else line.style.color = '#00f2fe';
                            
                            companyTerminal.appendChild(line);
                            companyTerminal.scrollTop = companyTerminal.scrollHeight;
                        }, index * 200); // progressive print effect!
                    });
                } else {
                    companyTerminal.innerHTML = `[系統錯誤] 執行失敗: ${data.error}`;
                }
            })
            .catch(err => {
                console.error('Error executing company SRE action:', err);
                companyTerminal.innerHTML = '[系統錯誤] 連線伺服器發生異常，無法執行動作。';
            })
            .finally(() => {
                btn.disabled = false;
                btn.textContent = originalText;
            });
        });
    });

    // Load company shift info initially and on tab activation
    fetchCompanyInfo();
    window.addEventListener('hashchange', () => {
        if (window.location.hash === '#stocks-company') {
            fetchCompanyInfo();
        }
    });
});
