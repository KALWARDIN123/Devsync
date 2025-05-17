// Base JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // User dropdown toggle
    function initializeUserMenu() {
        const userButton = document.querySelector('.user-button');
        const userDropdown = document.querySelector('.user-dropdown');

        if (userButton && userDropdown) {
            userButton.addEventListener('click', function(e) {
                e.stopPropagation();
                userDropdown.classList.toggle('active');
            });

            // Close dropdown when clicking outside
            document.addEventListener('click', function() {
                userDropdown.classList.remove('active');
            });
        }
    }

    // Active navigation link
    function setActiveNavLink() {
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('.nav-link');

        navLinks.forEach(link => {
            if (link.getAttribute('href') === currentPath) {
                link.classList.add('active');
            }
        });
    }

    // Theme toggle
    function initializeThemeToggle() {
        const themeToggle = document.getElementById('theme-toggle');
        const htmlElement = document.documentElement;
        
        if (themeToggle) {
            themeToggle.addEventListener('click', function() {
                const isDark = htmlElement.classList.toggle('dark');
                localStorage.setItem('theme', isDark ? 'dark' : 'light');
            });
        }
    }

    // Initialize notifications
    function initializeNotifications() {
        const notifications = document.querySelectorAll('.notification');
        
        notifications.forEach(notification => {
            const closeBtn = notification.querySelector('.notification-close');
            if (closeBtn) {
                closeBtn.addEventListener('click', () => {
                    notification.remove();
                });

                // Auto-hide after 5 seconds
                setTimeout(() => {
                    notification.remove();
                }, 5000);
            }
        });
    }

    // HTMX event handlers
    document.addEventListener('htmx:afterSwap', function(evt) {
        // Reinitialize components after HTMX updates
        initializeNotifications();
    });

    // Initialize all components
    initializeUserMenu();
    setActiveNavLink();
    initializeThemeToggle();
    initializeNotifications();
}); 