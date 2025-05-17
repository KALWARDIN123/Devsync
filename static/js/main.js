// UI State Management
const UIState = {
    sidebarOpen: window.innerWidth > 768,
    darkMode: localStorage.getItem('darkMode') === 'true',
    init() {
        this.setupEventListeners();
        this.applyDarkMode();
    },
    setupEventListeners() {
        document.getElementById('sidebar-toggle')?.addEventListener('click', () => this.toggleSidebar());
        document.getElementById('dark-mode-toggle')?.addEventListener('click', () => this.toggleDarkMode());
    },
    toggleSidebar() {
        const sidebar = document.querySelector('.sidebar');
        if (sidebar) {
            this.sidebarOpen = !this.sidebarOpen;
            sidebar.classList.toggle('active', this.sidebarOpen);
        }
    },
    toggleDarkMode() {
        this.darkMode = !this.darkMode;
        localStorage.setItem('darkMode', this.darkMode);
        this.applyDarkMode();
    },
    applyDarkMode() {
        document.documentElement.classList.toggle('dark', this.darkMode);
    }
};

// Form Handling
const FormHandler = {
    init() {
        this.setupFormValidation();
        this.setupAutoSave();
    },
    setupFormValidation() {
        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', (e) => this.validateForm(e));
        });
    },
    validateForm(e) {
        const form = e.target;
        const requiredFields = form.querySelectorAll('[required]');
        let isValid = true;

        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                isValid = false;
                this.showError(field, 'This field is required');
            } else {
                this.clearError(field);
            }
        });

        if (!isValid) {
            e.preventDefault();
        }
    },
    showError(field, message) {
        const errorDiv = field.nextElementSibling?.classList.contains('error-message')
            ? field.nextElementSibling
            : document.createElement('div');
        
        errorDiv.textContent = message;
        errorDiv.className = 'error-message text-danger mb-2';
        
        if (!field.nextElementSibling?.classList.contains('error-message')) {
            field.parentNode.insertBefore(errorDiv, field.nextElementSibling);
        }
        
        field.classList.add('error');
    },
    clearError(field) {
        const errorDiv = field.nextElementSibling;
        if (errorDiv?.classList.contains('error-message')) {
            errorDiv.remove();
        }
        field.classList.remove('error');
    },
    setupAutoSave() {
        document.querySelectorAll('form[data-autosave]').forEach(form => {
            const inputs = form.querySelectorAll('input, textarea, select');
            inputs.forEach(input => {
                input.addEventListener('change', () => this.autoSave(form));
            });
        });
    },
    autoSave(form) {
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        localStorage.setItem(`autosave_${form.id}`, JSON.stringify(data));
    }
};

// HTMX Extensions
const HTMXHandler = {
    init() {
        document.body.addEventListener('htmx:afterSwap', this.handleAfterSwap);
        document.body.addEventListener('htmx:beforeSwap', this.handleBeforeSwap);
    },
    handleAfterSwap(event) {
        // Reinitialize components after HTMX content swap
        FormHandler.init();
        initializeTooltips();
        initializeDropdowns();
    },
    handleBeforeSwap(event) {
        // Clean up before HTMX content swap
        const target = event.detail.target;
        if (target) {
            // Clean up any event listeners or third-party widgets
        }
    }
};

// Utility Functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function initializeTooltips() {
    document.querySelectorAll('[data-tooltip]').forEach(element => {
        element.addEventListener('mouseenter', (e) => {
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.textContent = element.dataset.tooltip;
            document.body.appendChild(tooltip);
            
            const rect = element.getBoundingClientRect();
            tooltip.style.top = `${rect.top - tooltip.offsetHeight - 5}px`;
            tooltip.style.left = `${rect.left + (rect.width - tooltip.offsetWidth) / 2}px`;
        });
        
        element.addEventListener('mouseleave', () => {
            document.querySelector('.tooltip')?.remove();
        });
    });
}

function initializeDropdowns() {
    document.querySelectorAll('.dropdown-toggle').forEach(toggle => {
        toggle.addEventListener('click', (e) => {
            e.preventDefault();
            const dropdown = toggle.nextElementSibling;
            dropdown.classList.toggle('show');
            
            document.addEventListener('click', (event) => {
                if (!toggle.contains(event.target) && !dropdown.contains(event.target)) {
                    dropdown.classList.remove('show');
                }
            });
        });
    });
}

// Initialize Everything
document.addEventListener('DOMContentLoaded', () => {
    UIState.init();
    FormHandler.init();
    HTMXHandler.init();
    initializeTooltips();
    initializeDropdowns();
}); 