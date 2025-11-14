// Theme Toggle Functionality
document.addEventListener('DOMContentLoaded', function() {
    // Load user's theme preference
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
    
    // Theme toggle button click handler
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', function(e) {
            e.preventDefault();
            const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            
            // Update DOM
            document.documentElement.setAttribute('data-theme', newTheme);
            
            // Update icon
            const icon = this.querySelector('i');
            if (icon) {
                icon.className = newTheme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
            }
            
            // Save to server
            fetch('/update_theme', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: 'theme=' + newTheme
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    console.log('Theme updated to:', data.theme);
                }
            })
            .catch(error => console.error('Error updating theme:', error));
        });
    }
    
    // Language selector change handler
    const languageSelect = document.getElementById('languageSelect');
    if (languageSelect) {
        languageSelect.addEventListener('change', function() {
            const newLanguage = this.value;
            
            // Save to server
            fetch('/update_language', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: 'language=' + newLanguage
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Reload page to apply new language
                    window.location.reload();
                }
            })
            .catch(error => console.error('Error updating language:', error));
        });
    }
});
