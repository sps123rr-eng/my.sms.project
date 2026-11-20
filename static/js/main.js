/* ==========================================================================
   ACADIFY - MAIN INTERACTIVE JAVASCRIPT
   ========================================================================== */

document.addEventListener('DOMContentLoaded', function () {
    // Mobile sidebar toggle
    const toggleBtn = document.getElementById('sidebarToggleBtn');
    const sidebar = document.getElementById('sidebarWrapper');
    const backdrop = document.getElementById('sidebarBackdrop');

    if (toggleBtn && sidebar && backdrop) {
        toggleBtn.addEventListener('click', function () {
            sidebar.classList.toggle('show');
            backdrop.classList.toggle('show');
        });

        backdrop.addEventListener('click', function () {
            sidebar.classList.remove('show');
            backdrop.classList.remove('show');
        });
    }

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            try {
                const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
                bsAlert.close();
            } catch (e) {
                alert.style.display = 'none';
            }
        }, 5000);
    });

    // Global quick search listener (redirects or filters current table)
    const globalSearchInput = document.getElementById('globalSearchInput');
    if (globalSearchInput) {
        globalSearchInput.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') {
                const query = this.value.trim();
                if (query.length > 0) {
                    const currentUrl = new URL(window.location.href);
                    currentUrl.searchParams.set('q', query);
                    currentUrl.searchParams.set('page', '1');
                    window.location.href = currentUrl.toString();
                }
            }
        });
    }

    // Attendance bulk selector
    const markAllPresentBtn = document.getElementById('markAllPresentBtn');
    if (markAllPresentBtn) {
        markAllPresentBtn.addEventListener('click', function () {
            const presentRadios = document.querySelectorAll('input[type="radio"][value="PRESENT"]');
            presentRadios.forEach(radio => radio.checked = true);
        });
    }
});
