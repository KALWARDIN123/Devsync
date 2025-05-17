// Team Detail JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize vibe meter
    function initializeVibeMeter() {
        const vibeMeter = document.querySelector('.vibe-progress');
        if (vibeMeter) {
            const score = vibeMeter.getAttribute('data-score');
            vibeMeter.style.width = `${score * 10}%`;
        }
    }

    // Initialize member actions
    function initializeMemberActions() {
        const memberButtons = document.querySelectorAll('[data-member-action]');
        memberButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const action = this.getAttribute('data-member-action');
                const memberId = this.getAttribute('data-member-id');
                handleMemberAction(action, memberId);
            });
        });
    }

    // Handle member actions
    async function handleMemberAction(action, memberId) {
        try {
            const response = await fetch(`/api/team/members/${memberId}/${action}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                }
            });

            if (response.ok) {
                // Refresh the member list section
                const membersList = document.querySelector('.members-section');
                if (membersList) {
                    const result = await response.json();
                    membersList.innerHTML = result.html;
                    initializeMemberActions();
                }
            } else {
                console.error('Failed to perform member action');
            }
        } catch (error) {
            console.error('Error:', error);
        }
    }

    // Initialize project filters
    function initializeProjectFilters() {
        const filterButtons = document.querySelectorAll('.project-filter');
        filterButtons.forEach(button => {
            button.addEventListener('click', function() {
                const status = this.getAttribute('data-status');
                filterProjects(status);
                
                // Update active state
                filterButtons.forEach(btn => btn.classList.remove('active'));
                this.classList.add('active');
            });
        });
    }

    // Filter projects by status
    function filterProjects(status) {
        const projects = document.querySelectorAll('.project-card');
        projects.forEach(project => {
            const projectStatus = project.getAttribute('data-status');
            if (status === 'all' || projectStatus === status) {
                project.style.display = 'block';
            } else {
                project.style.display = 'none';
            }
        });
    }

    // Initialize activity feed
    function initializeActivityFeed() {
        const loadMoreButton = document.querySelector('.load-more-activities');
        if (loadMoreButton) {
            loadMoreButton.addEventListener('click', loadMoreActivities);
        }
    }

    // Load more activities
    async function loadMoreActivities() {
        const activityFeed = document.querySelector('.activity-feed');
        const lastActivity = activityFeed.lastElementChild;
        if (!lastActivity) return;

        const timestamp = lastActivity.getAttribute('data-timestamp');
        
        try {
            const response = await fetch(`/api/team/activities/?before=${timestamp}`);
            if (response.ok) {
                const data = await response.json();
                if (data.activities.length > 0) {
                    // Append new activities
                    data.activities.forEach(activity => {
                        activityFeed.insertAdjacentHTML('beforeend', createActivityHTML(activity));
                    });

                    // Hide load more button if no more activities
                    if (!data.has_more) {
                        document.querySelector('.load-more-activities').style.display = 'none';
                    }
                }
            }
        } catch (error) {
            console.error('Error loading more activities:', error);
        }
    }

    // Create activity HTML
    function createActivityHTML(activity) {
        return `
            <div class="activity-item" data-timestamp="${activity.timestamp}">
                <div class="activity-header">
                    <img src="${activity.user.avatar}" alt="${activity.user.name}" class="activity-avatar">
                    <span class="activity-user">${activity.user.name}</span>
                    <span class="activity-time">${formatTimeAgo(activity.timestamp)}</span>
                </div>
                <p class="activity-description">${activity.description}</p>
            </div>
        `;
    }

    // Format timestamp to "time ago"
    function formatTimeAgo(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const seconds = Math.floor((now - date) / 1000);

        let interval = Math.floor(seconds / 31536000);
        if (interval > 1) return interval + ' years ago';
        if (interval === 1) return 'a year ago';

        interval = Math.floor(seconds / 2592000);
        if (interval > 1) return interval + ' months ago';
        if (interval === 1) return 'a month ago';

        interval = Math.floor(seconds / 86400);
        if (interval > 1) return interval + ' days ago';
        if (interval === 1) return 'yesterday';

        interval = Math.floor(seconds / 3600);
        if (interval > 1) return interval + ' hours ago';
        if (interval === 1) return 'an hour ago';

        interval = Math.floor(seconds / 60);
        if (interval > 1) return interval + ' minutes ago';
        if (interval === 1) return 'a minute ago';

        return 'just now';
    }

    // Get CSRF token from cookies
    function getCsrfToken() {
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Initialize all components
    initializeVibeMeter();
    initializeMemberActions();
    initializeProjectFilters();
    initializeActivityFeed();

    // HTMX event handlers
    document.addEventListener('htmx:afterSwap', function(evt) {
        if (evt.detail.target.id === 'members-list') {
            initializeMemberActions();
        }
    });
}); 