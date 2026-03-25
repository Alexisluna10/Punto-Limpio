window.toggleMenu = function() {
    const sidebar = document.getElementById("adminSidebar");
    const overlay = document.getElementById("sidebarOverlay");
    
    if (!sidebar) return;
    
    sidebar.classList.toggle("open");
    
    if (overlay) {
        overlay.classList.toggle("open");
    }
};