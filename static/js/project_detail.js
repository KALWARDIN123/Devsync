// Project Detail Page JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Progress bar initialization
    function initializeProgressBar() {
        const progressBar = document.querySelector('.progress-bar');
        if (progressBar) {
            const percentage = progressBar.getAttribute('data-progress');
            progressBar.style.width = `${percentage}%`;
        }
    }

    // Task status toggle
    function initializeTaskToggles() {
        const taskCheckboxes = document.querySelectorAll('.task-checkbox');
        taskCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                const taskTitle = this.closest('.task-card').querySelector('.task-title');
                if (this.checked) {
                    taskTitle.classList.add('completed');
                } else {
                    taskTitle.classList.remove('completed');
                }
            });
        });
    }

    // Modal handling
    function initializeModal() {
        const modal = document.getElementById('modal');
        const modalContainer = modal.querySelector('.modal-container');

        // Close modal when clicking outside
        modal.addEventListener('click', function(event) {
            if (event.target === modal) {
                modal.classList.add('hidden');
            }
        });

        // Prevent modal close when clicking inside
        modalContainer.addEventListener('click', function(event) {
            event.stopPropagation();
        });
    }

    // HTMX after swap handling
    document.addEventListener('htmx:afterSwap', function(evt) {
        if (evt.detail.target.id === 'modal') {
            evt.detail.target.classList.remove('hidden');
        }
        
        // Reinitialize components after HTMX updates
        initializeProgressBar();
        initializeTaskToggles();
    });

    // Task filter handling
    function initializeTaskFilter() {
        const filterSelect = document.querySelector('.task-filter');
        if (filterSelect) {
            filterSelect.addEventListener('change', function() {
                const selectedValue = this.value;
                const taskCards = document.querySelectorAll('.task-card');
                
                taskCards.forEach(card => {
                    const status = card.getAttribute('data-status');
                    if (selectedValue === 'all' || status === selectedValue) {
                        card.style.display = 'block';
                    } else {
                        card.style.display = 'none';
                    }
                });
            });
        }
    }

    // Initialize all components
    initializeProgressBar();
    initializeTaskToggles();
    initializeModal();
    initializeTaskFilter();
}); 