// Bosch Vehicle Tracking - Modern Interactive Frontend Controller

document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize Bootstrap Tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(el => new bootstrap.Tooltip(el));

    // 2. Global Keyboard Shortcut for Search ('/' or 'Ctrl+K')
    const searchInput = document.getElementById('navSearchInput');
    document.addEventListener('keydown', (e) => {
        // If user presses '/' outside of an active input, focus search
        if (e.key === '/' && !['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) {
            e.preventDefault();
            if (searchInput) {
                searchInput.focus();
                searchInput.select();
            }
        }
        // Ctrl+K shortcut
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
            e.preventDefault();
            if (searchInput) {
                searchInput.focus();
                searchInput.select();
            }
        }
    });

    // 3. Auto-Dismiss Flash Alerts after 6 seconds with smooth fade
    const alerts = document.querySelectorAll('.flash-container .alert');
    alerts.forEach(alertEl => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alertEl);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 6000);
    });

    // 4. Navbar Live Auto-Suggest for VIN or OEM ID
    if (searchInput) {
        let debounceTimer;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(debounceTimer);
            const val = e.target.value.trim();
            if (val.length < 2) return;

            debounceTimer = setTimeout(() => {
                fetch(`/api/suggest?term=${encodeURIComponent(val)}`)
                    .then(res => res.json())
                    .then(data => {
                        // Could expand with datalist or custom popover suggestions
                    })
                    .catch(err => console.error("Suggest error:", err));
            }, 300);
        });
    }
});
