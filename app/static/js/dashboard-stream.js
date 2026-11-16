// Bosch Vehicle Tracking - 24/7 TV Stream & Kiosk Controller
// Strictly One-Page Viewport Layout
// Left: Location-Wise Vehicle Quantities | Right: Live Movement Stream
// Bottom: Continuous Broadcast News Ticker

(function () {
    const REFRESH_INTERVAL_MS = 20000; // 20 seconds relaxed live sync for comfortable reading
    let countdownSec = REFRESH_INTERVAL_MS / 1000;
    let countdownTimer = null;

    let currentTelemetry = null;
    let activeLocationFilter = 'ALL';

    // Universal Shortform Number Formatter (e.g. 1100 -> 1.1k, 1M, 2B)
    function formatShortNumber(val) {
        if (val === null || val === undefined) return '0';
        const num = Number(val);
        if (isNaN(num)) return String(val);
        const abs = Math.abs(num);
        if (abs >= 1e9) {
            return (num / 1e9).toFixed(1).replace(/\.0$/, '') + 'B';
        }
        if (abs >= 1e6) {
            return (num / 1e6).toFixed(1).replace(/\.0$/, '') + 'M';
        }
        if (abs >= 1e3) {
            return (num / 1e3).toFixed(1).replace(/\.0$/, '') + 'k';
        }
        return Number.isInteger(num) ? String(num) : num.toFixed(1);
    }

    document.addEventListener('DOMContentLoaded', () => {
        // Initialize Theme Toggle
        initDashboardThemeToggle();

        // Initialize Fullscreen Toggle
        initFullscreenToggle();

        // Initialize Manual Sync Button
        document.getElementById('manualSyncBtn')?.addEventListener('click', () => {
            fetchTelemetry(true);
        });

        // Initialize Location Cards Click Delegation
        initLocationClickEvents();

        // Start Polling Telemetry Loop
        startStreamPolling();
    });

    function initDashboardThemeToggle() {
        const btn = document.getElementById('toggleThemeBtn');
        if (!btn) return;

        btn.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-bs-theme') || 'dark';
            const nextTheme = currentTheme === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-bs-theme', nextTheme);
            localStorage.setItem('dashboard_theme', nextTheme);

            fetch('/api/theme', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ dashboard_theme: nextTheme })
            }).catch(err => console.warn('Dashboard theme sync failed:', err));
        });
    }

    function initFullscreenToggle() {
        const btn = document.getElementById('toggleFullscreenBtn');
        if (!btn) return;

        btn.addEventListener('click', () => {
            if (!document.fullscreenElement) {
                document.documentElement.requestFullscreen().catch(err => {
                    console.warn(`Fullscreen error: ${err.message}`);
                });
            } else {
                if (document.exitFullscreen) {
                    document.exitFullscreen();
                }
            }
        });
    }

    function initLocationClickEvents() {
        const list = document.getElementById('locationQuantitiesList');
        if (!list) return;

        list.addEventListener('click', (e) => {
            const card = e.target.closest('.location-chip-card');
            if (!card) return;

            const loc = card.getAttribute('data-location') || 'ALL';
            if (activeLocationFilter === loc && loc !== 'ALL') {
                activeLocationFilter = 'ALL';
                list.querySelectorAll('.location-chip-card').forEach(c => {
                    if (c.getAttribute('data-location') === 'ALL') c.classList.add('active');
                    else c.classList.remove('active');
                });
            } else {
                activeLocationFilter = loc;
                list.querySelectorAll('.location-chip-card').forEach(c => c.classList.remove('active'));
                card.classList.add('active');
            }

            filterMovementsByLocation(activeLocationFilter);
        });
    }

    function filterMovementsByLocation(loc) {
        const items = document.querySelectorAll('#movementTickerList .movement-card');
        items.forEach(item => {
            if (loc === 'ALL') {
                item.style.display = '';
            } else {
                const itemLoc = item.getAttribute('data-location') || '';
                if (itemLoc.toLowerCase().includes(loc.toLowerCase())) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            }
        });
    }

    function startStreamPolling() {
        resetCountdown();
        fetchTelemetry(false);

        setInterval(() => {
            fetchTelemetry(false);
        }, REFRESH_INTERVAL_MS);
    }

    function resetCountdown() {
        countdownSec = REFRESH_INTERVAL_MS / 1000;
        const countdownEl = document.getElementById('nextRefreshCountdown');
        if (countdownTimer) clearInterval(countdownTimer);

        if (countdownEl) {
            countdownEl.textContent = `Refresh in ${countdownSec}s`;
        }

        countdownTimer = setInterval(() => {
            countdownSec--;
            if (countdownEl) {
                countdownEl.textContent = `Refresh in ${countdownSec}s`;
            }
            if (countdownSec <= 0) {
                countdownSec = REFRESH_INTERVAL_MS / 1000;
            }
        }, 1000);
    }

    function fetchTelemetry(isManual) {
        const countdownEl = document.getElementById('nextRefreshCountdown');
        if (countdownEl) countdownEl.textContent = 'Refreshing...';

        fetch('/api/telemetry')
            .then(res => {
                if (!res.ok) throw new Error('Network error');
                return res.json();
            })
            .then(data => {
                currentTelemetry = data;
                updateTelemetryState(data);
                resetCountdown();
                if (countdownEl) countdownEl.textContent = 'Refreshed';
            })
            .catch(err => {
                console.error('Telemetry fetch error:', err);
                if (countdownEl) countdownEl.textContent = 'Sync Error';
            });
    }

    function updateTelemetryState(data) {
        // 1. Update KPI Values with shortform formatting
        updateMiniKpis(data);

        // 2. Update Left Location-Wise Quantities Box
        updateLocationQuantities(data);

        // 3. Update Right Live Movement Stream
        updateMovementStream(data);

        // 4. Update Bottom Running News Updates Ticker
        updateRunningTicker(data);

        // 5. Reinitialize Lucide Icons for dynamic content
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }

    function updateMiniKpis(data) {
        const fleetEl = document.getElementById('kpiTotalFleet');
        const hubsEl = document.getElementById('kpiActiveHubs');
        const hopsEl = document.getElementById('kpiTotalHops');
        const oemEl = document.getElementById('kpiOemBrands');
        const issuesEl = document.getElementById('kpiActiveIssues');

        if (fleetEl) fleetEl.textContent = formatShortNumber(data.total_vehicles);
        if (hubsEl && data.location_breakdown) hubsEl.textContent = formatShortNumber(data.location_breakdown.length);
        if (hopsEl) {
            const totalHops = data.total_hops !== undefined ? data.total_hops : 
                (data.vehicles ? data.vehicles.reduce((sum, v) => sum + (v.total_hops || 0), 0) : 0);
            hopsEl.textContent = formatShortNumber(totalHops);
        }
        if (oemEl && data.oem_distribution) oemEl.textContent = formatShortNumber(data.oem_distribution.length);
        if (issuesEl) issuesEl.textContent = formatShortNumber(data.problem_count);
    }

    function updateLocationQuantities(data) {
        const container = document.getElementById('locationQuantitiesList');
        const summaryBadge = document.getElementById('locationSummaryBadge');

        if (summaryBadge && data.location_breakdown) {
            summaryBadge.textContent = `${formatShortNumber(data.location_breakdown.length)} Hubs • ${formatShortNumber(data.total_vehicles)} Units`;
        }

        if (container && data.location_breakdown) {
            const total = data.total_vehicles || 1;
            const isAllActive = activeLocationFilter === 'ALL';

            let html = `
            <div class="location-chip-card ${isAllActive ? 'active' : ''}" data-location="ALL">
                <div class="chip-card-header">
                    <div class="d-flex align-items-center gap-2 overflow-hidden">
                        <i data-lucide="layers" class="text-info" style="width: 14px; height: 14px;"></i>
                        <span class="chip-card-name text-truncate">ALL LOCATIONS</span>
                    </div>
                    <span class="chip-card-badge">${formatShortNumber(data.total_vehicles)}</span>
                </div>
                <div class="chip-card-footer">
                    <span class="small text-muted" style="font-size: 0.68rem;">100% of Fleet Active</span>
                    <span class="chip-card-pct font-monospace text-info ms-auto">${data.location_breakdown.length} Hubs</span>
                </div>
            </div>`;

            data.location_breakdown.forEach(loc => {
                const pct = ((loc.count / total) * 100).toFixed(1);
                const isActive = activeLocationFilter === loc.location;

                html += `
                <div class="location-chip-card ${isActive ? 'active' : ''}" data-location="${escapeHtml(loc.location)}">
                    <div class="chip-card-header">
                        <div class="d-flex align-items-center gap-2 overflow-hidden">
                            <span class="chip-pin-dot"></span>
                            <span class="chip-card-name text-truncate" title="${escapeHtml(loc.location)}">${escapeHtml(loc.location)}</span>
                        </div>
                        <span class="chip-card-badge">
                            ${formatShortNumber(loc.count)}
                        </span>
                    </div>
                    <div class="chip-card-footer">
                        <div class="progress flex-grow-1" style="height: 3px; background: #1e293b;">
                            <div class="progress-bar bg-info" role="progressbar" style="width: ${pct}%;"></div>
                        </div>
                        <span class="chip-card-pct font-monospace text-muted">${pct}%</span>
                    </div>
                </div>`;
            });
            container.innerHTML = html;
        }
    }

    function updateMovementStream(data) {
        const list = document.getElementById('movementTickerList');
        if (!list || !data.recent_movements) return;

        let html = '';
        data.recent_movements.forEach(m => {
            const isMatch = (activeLocationFilter === 'ALL' || (m.to && m.to.toLowerCase().includes(activeLocationFilter.toLowerCase())));
            const displayStyle = isMatch ? '' : 'display: none;';

            html += `
            <div class="movement-card" 
                 data-vehicle-id="${m.vehicle_id}" 
                 data-vin="${escapeHtml(m.vin)}" 
                 data-location="${escapeHtml(m.to)}"
                 style="${displayStyle}">
                <div class="d-flex justify-content-between align-items-center mb-1">
                    <div class="d-flex align-items-center gap-2">
                        <span class="font-monospace fw-bold text-info small">${escapeHtml(m.vin)}</span>
                        <span class="badge bg-secondary bg-opacity-50 text-white-50 font-monospace" style="font-size: 0.65rem;">
                            ${escapeHtml(m.oem)} ${escapeHtml(m.name)}
                        </span>
                    </div>
                    <span class="badge bg-primary bg-opacity-25 text-info font-monospace" style="font-size: 0.65rem;">
                        Hop #${m.hop}
                    </span>
                </div>

                <div class="movement-route py-1 d-flex align-items-center text-truncate">
                    <span class="text-white fw-medium small text-truncate">${escapeHtml(m.from)}</span>
                    <i data-lucide="arrow-right" class="text-warning mx-2 flex-shrink-0" style="width: 14px; height: 14px;"></i>
                    <span class="text-warning fw-semibold small text-truncate">${escapeHtml(m.to)}</span>
                </div>

                <div class="d-flex justify-content-between align-items-center text-muted mt-1" style="font-size: 0.7rem;">
                    <span class="text-truncate pe-2">
                        <i data-lucide="tag" class="me-1" style="width: 12px; height: 12px;"></i>${escapeHtml(m.purpose || 'Fleet Transit')}
                    </span>
                    <span class="font-monospace text-secondary flex-shrink-0">
                        <i data-lucide="calendar" class="me-1" style="width: 12px; height: 12px;"></i>${escapeHtml(m.date || '-')}
                    </span>
                </div>
            </div>`;
        });

        list.innerHTML = html;
    }

    function updateRunningTicker(data) {
        const tickerTrack = document.getElementById('tickerTrack');
        if (!tickerTrack) return;

        let items = data.ticker_items;
        if (!items || items.length === 0) {
            items = [
                `FLEET ACTIVE: ${formatShortNumber(data.total_vehicles)} vehicles monitored across ${data.location_breakdown ? data.location_breakdown.length : 0} facilities`,
                `TELEMETRY ACTIVE: 24/7 continuous operations telemetry synchronized`
            ];
        }

        let html = '';
        // Duplicate items array once for seamless marquee continuity
        const allItems = items.concat(items);
        allItems.forEach(item => {
            html += `<span class="ticker-item">${item}</span><span class="ticker-separator">&bull;</span>`;
        });

        tickerTrack.innerHTML = html;
    }

    function escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }
})();
