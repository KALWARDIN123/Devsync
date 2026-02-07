// Team functionality
class TeamManager {
    constructor() {
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Copy invite code functionality
        const copyButtons = document.querySelectorAll('[data-copy-invite]');
        copyButtons.forEach(button => {
            button.addEventListener('click', () => this.copyInviteCode(button));
        });

        // Modal handling
        document.addEventListener('htmx:afterSwap', (evt) => {
            if (evt.detail.target.id === 'modal') {
                evt.detail.target.classList.remove('hidden');
            }
        });

        document.addEventListener('click', (evt) => {
            if (evt.target.id === 'modal') {
                evt.target.classList.add('hidden');
            }
        });

        // Form validation
        const teamForms = document.querySelectorAll('.team-form');
        teamForms.forEach(form => {
            form.addEventListener('submit', (e) => this.validateTeamForm(e));
        });
    }

    async copyInviteCode(button) {
        const inviteCode = document.getElementById('inviteCode').textContent;
        try {
            await navigator.clipboard.writeText(inviteCode);
            this.showNotification('Invite code copied to clipboard!', 'success');
        } catch (err) {
            this.showNotification('Failed to copy invite code', 'error');
        }
    }

    validateTeamForm(e) {
        const form = e.target;
        const nameInput = form.querySelector('[name="name"]');
        const descriptionInput = form.querySelector('[name="description"]');

        let isValid = true;

        if (nameInput && !nameInput.value.trim()) {
            this.showFieldError(nameInput, 'Team name is required');
            isValid = false;
        }

        if (descriptionInput && !descriptionInput.value.trim()) {
            this.showFieldError(descriptionInput, 'Description is required');
            isValid = false;
        }

        if (!isValid) {
            e.preventDefault();
        }
    }

    showFieldError(field, message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-feedback';
        errorDiv.textContent = message;
        
        const existingError = field.parentElement.querySelector('.error-feedback');
        if (existingError) {
            existingError.remove();
        }
        
        field.parentElement.appendChild(errorDiv);
        field.classList.add('error');
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.classList.add('fade-out');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
}

// Initialize team functionality when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new TeamManager();
}); 