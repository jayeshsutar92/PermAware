// UI tab switching and loader controllers

function switchTab(mode) {
    // Buttons
    const btnAuto = document.getElementById('tab-auto');
    const btnManual = document.getElementById('tab-manual');
    
    // Panels
    const panelAuto = document.getElementById('panel-auto');
    const panelManual = document.getElementById('panel-manual');
    
    if (mode === 'auto') {
        btnAuto.classList.add('active');
        btnManual.classList.remove('active');
        panelAuto.classList.remove('hidden');
        panelManual.classList.add('hidden');
    } else {
        btnAuto.classList.remove('active');
        btnManual.classList.add('active');
        panelAuto.classList.add('hidden');
        panelManual.classList.remove('hidden');
    }
}

function showLoader() {
    const loader = document.getElementById('loader');
    const loaderMsg = document.getElementById('loader-msg');
    
    // Determine which mode we are in
    const activeTab = document.querySelector('.tab-btn.active').id;
    
    if (activeTab === 'tab-auto') {
        const app_id = document.getElementById('app_id').value.strip || document.getElementById('app_id').value;
        if (app_id) {
            loaderMsg.innerText = `Scraping permissions for "${app_id}" and running classification...`;
            loader.classList.remove('hidden');
        }
    } else {
        const permission = document.getElementById('permission').value;
        if (permission) {
            loaderMsg.innerText = `Classifying permission "${permission}"...`;
            loader.classList.remove('hidden');
        }
    }
}

// Preserve selected tab state based on results/error context on load
document.addEventListener('DOMContentLoaded', () => {
    // If there is an active input value in manual form, switch to manual tab
    const permissionVal = document.getElementById('permission') ? document.getElementById('permission').value : '';
    const panelManual = document.getElementById('panel-manual');
    const manualFormHidden = panelManual ? panelManual.classList.contains('hidden') : true;
    
    // Check if form contains a mode state from server side
    const urlParams = new URLSearchParams(window.location.search);
    const mode = urlParams.get('mode');
    
    if (mode === 'manual' || (permissionVal && !manualFormHidden)) {
        switchTab('manual');
    }

    // Theme toggler logic
    const themeToggleBtn = document.getElementById('theme-toggle');
    const themeIcon = document.getElementById('theme-icon');
    
    if (themeToggleBtn && themeIcon) {
        // Check saved theme
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'light') {
            document.body.classList.add('light-theme');
            themeIcon.classList.replace('fa-moon', 'fa-sun');
        }
        
        themeToggleBtn.addEventListener('click', () => {
            const isLight = document.body.classList.toggle('light-theme');
            if (isLight) {
                themeIcon.classList.replace('fa-moon', 'fa-sun');
                localStorage.setItem('theme', 'light');
            } else {
                themeIcon.classList.replace('fa-sun', 'fa-moon');
                localStorage.setItem('theme', 'dark');
            }
        });
    }
});
