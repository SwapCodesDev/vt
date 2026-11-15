// Bosch Vehicle Tracking - 24/7 TV Stream & Kiosk Controller
// Strictly One-Page Layout: Location Chips at Top, Split Movements & Vehicle Roadmap

(function () {
    const REFRESH_INTERVAL_MS = 10000; // 10 seconds live sync
    let countdownSec = REFRESH_INTERVAL_MS / 1000;
    let countdownTimer = null;

    // In-memory cache for live telemetry
    let currentTelemetry = null;
    let vehiclesMap = new Map(); // id -> vehicle
    let selectedVehicleId = null;
    let activeLocationFilter = 'ALL';
    let searchQuery = '';

    document.addEventListener('DOMContentLoaded', () => {
        // Initialize Fullscreen Toggle
        initFullscreenToggle();

        // Initialize Manual Sync Button
        document.getElementById('manualSyncBtn')?.addEventListener('click', () => {
            fetchTelemetry(true);
        });

        // Initialize Search Input
        initSearch();

        // Initialize Location Chips Clicks
        initLocationChips();

        // Initialize Movement Card Clicks (Server-rendered initial state)
        bindMovementCardClicks();

        // Start Background Polling
        startStreamPolling();
    });

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

    function initSearch() {
        const searchInput = document.getElementById('kioskSearchInput');
        if (!searchInput) return;

        searchInput.addEventListener('input', (e) => {
            searchQuery = e.target.value.trim().toLowerCase();
            applyFilters();
        });
    }

    function initLocationChips() {
        const container = document.getElementById('locationChipsContainer');
        if (!container) return;

        container.addEventListener('click', (e) => {
            const chip = e.target.closest('.location-chip');
            if (!chip) return;

            const loc = chip.getAttribute('data-location') || 'ALL';
            activeLocationFilter = loc;

            // Update active styling
            container.querySelectorAll('.location-chip').forEach(c => c.classList.remove('active'));
            chip.classList.add('active');

            applyFilters();
        });
    }

    function startStreamPolling() {
        resetCountdown();
        // Initial fetch to populate full map & state
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
                if (!res.ok) throw new Error('Network response error');
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
        // Cache vehicles in map
        vehiclesMap.clear();
        if (data.vehicles && Array.isArray(data.vehicles)) {
            data.vehicles.forEach(v => {
                vehiclesMap.set(v.id, v);
            });
        }

        // Determine currently selected vehicle
        if (!selectedVehicleId && data.recent_movements && data.recent_movements.length > 0) {
            selectedVehicleId = data.recent_movements[0].vehicle_id;
        } else if (!selectedVehicleId && data.vehicles && data.vehicles.length > 0) {
            selectedVehicleId = data.vehicles[0].id;
        }

        // 1. Update Smaller Sized Top KPIs
        updateMiniKpis(data);

        // 2. Update Top Location Chips Bar
        updateLocationChips(data);

        // 3. Update Left Movement Stream
        updateMovementStream(data);

        // 4. Update Right Vehicle Roadmap
        renderVehicleRoadmap(selectedVehicleId);
    }

    function updateMiniKpis(data) {
        const fleetEl = document.getElementById('kpiTotalFleet');
        const hubsEl = document.getElementById('kpiActiveHubs');
        const hopsEl = document.getElementById('kpiTotalHops');
        const oemEl = document.getElementById('kpiOemBrands');
        const issuesEl = document.getElementById('kpiActiveIssues');

        if (fleetEl) fleetEl.textContent = data.total_vehicles;
        if (hubsEl && data.location_breakdown) hubsEl.textContent = data.location_breakdown.length;
        if (hopsEl) {
            const totalHops = data.total_hops !== undefined ? data.total_hops : 
                (data.vehicles ? data.vehicles.reduce((sum, v) => sum + (v.total_hops || 0), 0) : 0);
            hopsEl.textContent = totalHops;
        }
        if (oemEl && data.oem_distribution) oemEl.textContent = data.oem_distribution.length;
        if (issuesEl) issuesEl.textContent = data.problem_count;
    }

    function updateLocationChips(data) {
        const container = document.getElementById('locationChipsContainer');
        const badge = document.getElementById('locationSummaryBadge');

        if (badge) {
            badge.textContent = `${data.location_breakdown.length} Hubs • ${data.total_vehicles} Units`;
        }

        if (container && data.location_breakdown) {
            let html = `
            <div class="location-chip ${activeLocationFilter === 'ALL' ? 'active' : ''}" data-location="ALL">
                <span class="chip-name">ALL LOCATIONS</span>
                <span class="chip-count">${data.total_vehicles}</span>
            </div>`;

            data.location_breakdown.forEach(loc => {
                const isActive = activeLocationFilter === loc.location;
                html += `
                <div class="location-chip ${isActive ? 'active' : ''}" data-location="${escapeHtml(loc.location)}">
                    <span class="chip-dot"></span>
                    <span class="chip-name text-truncate" title="${escapeHtml(loc.location)}">${escapeHtml(loc.location)}</span>
                    <span class="chip-count">${loc.count}</span>
                </div>`;
            });

            container.innerHTML = html;
        }
    }

    function updateMovementStream(data) {
        const tickerList = document.getElementById('movementTickerList');
        const countBadge = document.getElementById('streamCountBadge');

        if (countBadge) {
            countBadge.textContent = `${data.recent_movements.length} Recent Hops`;
        }

        if (tickerList && data.recent_movements) {
            let html = '';
            data.recent_movements.forEach(m => {
                const isSelected = m.vehicle_id === selectedVehicleId;
                html += `
                <div class="movement-card ${isSelected ? 'active' : ''}" 
                     data-vehicle-id="${m.vehicle_id}" 
                     data-vin="${escapeHtml(m.vin)}" 
                     data-oem="${escapeHtml(m.oem || '')}" 
                     data-name="${escapeHtml(m.name || '')}"
                     data-location="${escapeHtml(m.to || '')}">
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
                        <i class="bi bi-arrow-right text-warning mx-2 flex-shrink-0"></i>
                        <span class="text-warning fw-semibold small text-truncate">${escapeHtml(m.to)}</span>
                    </div>

                    <div class="d-flex justify-content-between align-items-center text-muted mt-1" style="font-size: 0.7rem;">
                        <span class="text-truncate pe-2">
                            <i class="bi bi-tag me-1"></i>${escapeHtml(m.purpose || 'Fleet Transit')}
                        </span>
                        <span class="font-monospace text-secondary flex-shrink-0">
                            <i class="bi bi-calendar3 me-1"></i>${escapeHtml(m.date || '-')}
                        </span>
                    </div>
                </div>`;
            });

            tickerList.innerHTML = html;
            bindMovementCardClicks();
            applyFilters();
        }
    }

    function bindMovementCardClicks() {
        document.querySelectorAll('.movement-card').forEach(card => {
            card.onclick = function () {
                const vid = parseInt(this.getAttribute('data-vehicle-id'), 10);
                if (!isNaN(vid)) {
                    selectedVehicleId = vid;
                    // Update active classes on cards
                    document.querySelectorAll('.movement-card').forEach(c => c.classList.remove('active'));
                    this.classList.add('active');
                    // Render selected vehicle roadmap
                    renderVehicleRoadmap(selectedVehicleId);
                }
            };
        });
    }

    function applyFilters() {
        const cards = document.querySelectorAll('#movementTickerList .movement-card');
        let visibleCount = 0;

        cards.forEach(card => {
            const vin = (card.getAttribute('data-vin') || '').toLowerCase();
            const oem = (card.getAttribute('data-oem') || '').toLowerCase();
            const name = (card.getAttribute('data-name') || '').toLowerCase();
            const loc = (card.getAttribute('data-location') || '').toUpperCase();

            // Check location filter
            const matchesLocation = activeLocationFilter === 'ALL' || loc.includes(activeLocationFilter.toUpperCase());

            // Check search text query
            const matchesSearch = !searchQuery || 
                                  vin.includes(searchQuery) || 
                                  oem.includes(searchQuery) || 
                                  name.includes(searchQuery) || 
                                  loc.toLowerCase().includes(searchQuery);

            if (matchesLocation && matchesSearch) {
                card.style.display = '';
                visibleCount++;
            } else {
                card.style.display = 'none';
            }
        });

        const countBadge = document.getElementById('streamCountBadge');
        if (countBadge && currentTelemetry) {
            countBadge.textContent = `${visibleCount} of ${currentTelemetry.recent_movements.length} Hops`;
        }
    }

    function renderVehicleRoadmap(vehicleId) {
        if (!vehicleId) return;
        const v = vehiclesMap.get(vehicleId);
        if (!v) return;

        // 1. Header Badges
        const vinBadge = document.getElementById('roadmapVinBadge');
        const titleEl = document.getElementById('roadmapTitle');
        const typeBadge = document.getElementById('roadmapTypeBadge');
        const fullLink = document.getElementById('roadmapFullTrackingBtn');

        if (vinBadge) vinBadge.textContent = v.bosch_vin;
        if (titleEl) titleEl.textContent = `${v.oem} ${v.vehicle_name}`;
        if (typeBadge) typeBadge.textContent = v.vehicle_type || 'PP';
        if (fullLink) fullLink.href = `/tracking/vehicle/${v.id}`;

        // 2. Specs Strip
        const curLoc = document.getElementById('roadmapCurrentLocation');
        if (curLoc) {
            curLoc.innerHTML = `<i class="bi bi-geo-alt-fill text-danger"></i> ${escapeHtml(v.current_location)}`;
        }

        const curStatus = document.getElementById('roadmapCurrentStatus');
        if (curStatus) {
            curStatus.innerHTML = `Status: <span class="badge bg-secondary font-monospace" style="font-size: 0.65rem;">${escapeHtml(v.current_status)}</span>`;
        }

        const startPoint = document.getElementById('roadmapStartPoint');
        if (startPoint) {
            startPoint.innerHTML = `<i class="bi bi-flag-fill text-success"></i> ${escapeHtml(v.receiving_location || 'BOSCH PLANT')}`;
        }

        const incomingDate = document.getElementById('roadmapIncomingDate');
        if (incomingDate) {
            incomingDate.innerHTML = `Date: <span class="font-monospace text-light">${escapeHtml(v.incoming_date || '-')}</span>`;
        }

        const oemChassis = document.getElementById('roadmapOemChassis');
        if (oemChassis) {
            oemChassis.textContent = v.oem_id_no || 'N/A';
        }

        const chassisNo = document.getElementById('roadmapChassisNo');
        if (chassisNo) {
            chassisNo.textContent = v.chassis_no || '-';
        }

        const owner = document.getElementById('roadmapOwner');
        if (owner) {
            owner.textContent = v.owner || 'Unassigned';
        }

        const material = document.getElementById('roadmapMaterial');
        if (material) {
            material.textContent = v.material_with_vehicle || 'Standard Kit';
            material.title = v.material_with_vehicle || '';
        }

        // 3. Issue Alert Banner
        const alertBox = document.getElementById('roadmapIssueAlert');
        const issueText = document.getElementById('roadmapIssueText');
        const tpmText = document.getElementById('roadmapTpmText');

        if (alertBox && issueText && tpmText) {
            if (v.vehicle_problem_issues && v.vehicle_problem_issues !== 'NA' && v.vehicle_problem_issues !== 'None') {
                alertBox.classList.remove('d-none');
                issueText.textContent = v.vehicle_problem_issues;
                tpmText.textContent = `TPM: ${v.tpm_confirmation || 'Pending'}`;
            } else {
                alertBox.classList.add('d-none');
            }
        }

        // 4. Hop Counter Badge
        const hopCounter = document.getElementById('roadmapHopCounter');
        const movements = v.movements || [];
        if (hopCounter) {
            hopCounter.textContent = `Total Hops: ${movements.length}`;
        }

        // 5. Build Roadmap Timeline Stepper
        const stepperContainer = document.getElementById('roadmapStepperList');
        if (stepperContainer) {
            if (movements.length > 0) {
                let sHtml = '';
                movements.forEach((hop, idx) => {
                    const isFirst = idx === 0;
                    const isLast = idx === movements.length - 1;

                    let markerIcon = '<i class="bi bi-arrow-right-circle text-info"></i>';
                    let hopBadge = `<span class="badge bg-secondary font-monospace" style="font-size: 0.65rem;">Hop #${hop.hop_sequence}</span>`;

                    if (isFirst) {
                        markerIcon = '<i class="bi bi-flag-fill text-success"></i>';
                        hopBadge += ' <span class="badge bg-success bg-opacity-25 text-success font-monospace" style="font-size: 0.65rem;">START POINT (GENESIS)</span>';
                    } else if (isLast) {
                        markerIcon = '<i class="bi bi-geo-alt-fill text-warning"></i>';
                        hopBadge += ' <span class="badge bg-warning bg-opacity-25 text-warning font-monospace" style="font-size: 0.65rem;">CURRENT LOCATION</span>';
                    }

                    sHtml += `
                    <div class="stepper-node ${isLast ? 'is-current' : ''}">
                        <div class="stepper-marker">
                            ${markerIcon}
                        </div>
                        <div class="stepper-card">
                            <div class="d-flex justify-content-between align-items-start mb-1">
                                <div class="d-flex align-items-center gap-2">
                                    ${hopBadge}
                                </div>
                                <span class="font-monospace text-muted small" style="font-size: 0.7rem;">
                                    ${escapeHtml(hop.arrival_date || hop.dispatch_date || '-')}
                                </span>
                            </div>

                            <div class="fw-bold text-white small py-1">
                                <span>${escapeHtml(hop.source_location)}</span>
                                <i class="bi bi-arrow-right text-warning mx-2"></i>
                                <span class="text-warning">${escapeHtml(hop.destination_location)}</span>
                            </div>

                            <div class="stepper-details small text-muted mt-1">
                                ${hop.movement_purpose ? `<div><strong>Purpose:</strong> ${escapeHtml(hop.movement_purpose)}</div>` : ''}
                                ${hop.work_done ? `<div><strong>Work:</strong> ${escapeHtml(hop.work_done)}</div>` : ''}
                                <div class="d-flex align-items-center gap-3 mt-1" style="font-size: 0.68rem;">
                                    ${hop.dc_number ? `<span class="font-monospace text-info">DC: ${escapeHtml(hop.dc_number)}</span>` : ''}
                                    ${hop.status ? `<span class="badge bg-dark border border-secondary text-secondary">${escapeHtml(hop.status)}</span>` : ''}
                                </div>
                            </div>
                        </div>
                    </div>`;
                });
                stepperContainer.innerHTML = sHtml;
            } else {
                stepperContainer.innerHTML = `
                <div class="stepper-node is-current">
                    <div class="stepper-marker">
                        <i class="bi bi-flag-fill text-success"></i>
                    </div>
                    <div class="stepper-card">
                        <div class="badge bg-success bg-opacity-25 text-success font-monospace mb-2" style="font-size: 0.68rem;">
                            HOP #1 &bull; GENESIS START POINT
                        </div>
                        <div class="fw-bold text-white small">
                            Stationed at ${escapeHtml(v.receiving_location || 'BOSCH PLANT')}
                        </div>
                        <div class="small text-muted mt-1">
                            Incoming Date: ${escapeHtml(v.incoming_date || 'N/A')}
                        </div>
                    </div>
                </div>`;
            }
        }
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
