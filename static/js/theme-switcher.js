/* ============================== */
/* THEME SWITCHER */
/* ============================== */

// Initialize theme on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeTheme();
    setupThemeToggle();
});

function initializeTheme() {
    // Check if user has a saved theme preference
    const savedTheme = localStorage.getItem('theme') || 'dark';
    const htmlElement = document.documentElement;
    
    // Set the theme
    htmlElement.setAttribute('data-theme', savedTheme);
    updateThemeUI(savedTheme);
}

function setupThemeToggle() {
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
}

function toggleTheme() {
    const htmlElement = document.documentElement;
    const currentTheme = htmlElement.getAttribute('data-theme') || 'dark';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    // Set new theme
    htmlElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeUI(newTheme);
}

function updateThemeUI(theme) {
    const icon = document.getElementById('theme-icon');
    const label = document.getElementById('theme-label');
    
    if (icon) {
        icon.textContent = theme === 'dark' ? '🌙' : '☀️';
    }
    
    if (label) {
        label.textContent = theme === 'dark' ? 'Dark' : 'Light';
    }
}
