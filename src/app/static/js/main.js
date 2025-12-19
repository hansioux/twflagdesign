document.addEventListener('DOMContentLoaded', () => {
    const toggleBtn = document.getElementById('sidePanelToggle');
    const closeBtn = document.getElementById('sidePanelClose');
    const sidePanel = document.getElementById('sidePanel');
    const overlay = document.getElementById('sidePanelOverlay');

    function openPanel() {
        sidePanel.style.transform = 'translateX(0)';
        overlay.style.opacity = '1';
        overlay.style.pointerEvents = 'auto';
    }

    function closePanel() {
        sidePanel.style.transform = 'translateX(100%)';
        overlay.style.opacity = '0';
        overlay.style.pointerEvents = 'none';
    }

    if (toggleBtn) toggleBtn.addEventListener('click', (e) => {
        e.preventDefault();
        openPanel();
    });

    if (closeBtn) closeBtn.addEventListener('click', closePanel);
    if (overlay) overlay.addEventListener('click', closePanel);
});
