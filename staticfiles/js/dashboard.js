// Dashboard JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize charts
    function initializeCharts() {
        // Activity Chart
        const activityCtx = document.getElementById('activity-chart');
        if (activityCtx) {
            new Chart(activityCtx, {
                type: 'line',
                data: {
                    labels: activityData.labels,
                    datasets: [{
                        label: 'Team Activity',
                        data: activityData.values,
                        borderColor: '#2563EB',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        }

        // Task Distribution Chart
        const taskDistributionCtx = document.getElementById('task-distribution-chart');
        if (taskDistributionCtx) {
            new Chart(taskDistributionCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Completed', 'In Progress', 'Pending'],
                    datasets: [{
                        data: taskDistributionData,
                        backgroundColor: ['#059669', '#2563EB', '#D97706']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        }
    }

    // Initialize activity feed
    function initializeActivityFeed() {
        const activityFeed = document.querySelector('.activity-feed');
        if (activityFeed) {
            // Infinite scroll
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        loadMoreActivities();
                    }
                });
            });

            const loadMoreTrigger = document.querySelector('.load-more-trigger');
            if (loadMoreTrigger) {
                observer.observe(loadMoreTrigger);
            }
        }
    }

    // Load more activities
    async function loadMoreActivities() {
        const lastActivity = document.querySelector('.activity-item:last-child');
        if (!lastActivity) return;

        const lastTimestamp = lastActivity.dataset.timestamp;
        const response = await fetch(`/api/activities/?before=${lastTimestamp}`);
        const newActivities = await response.json();

        if (newActivities.length > 0) {
            const activityFeed = document.querySelector('.activity-feed');
            newActivities.forEach(activity => {
                activityFeed.insertAdjacentHTML('beforeend', createActivityHTML(activity));
            });
        }
    }

    // Create activity HTML
    function createActivityHTML(activity) {
        return `
            <div class="activity-item" data-timestamp="${activity.timestamp}">
                <div class="activity-icon">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        ${getActivityIcon(activity.type)}
                    </svg>
                </div>
                <div class="activity-content">
                    <div class="activity-header">
                        <span class="activity-title">${activity.title}</span>
                        <span class="activity-time">${formatTimeAgo(activity.timestamp)}</span>
                    </div>
                    <p class="activity-description">${activity.description}</p>
                </div>
            </div>
        `;
    }

    // Get activity icon based on type
    function getActivityIcon(type) {
        const icons = {
            task: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>',
            comment: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>',
            update: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>'
        };
        return icons[type] || icons.update;
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

    // Initialize dashboard components
    initializeCharts();
    initializeActivityFeed();
}); 