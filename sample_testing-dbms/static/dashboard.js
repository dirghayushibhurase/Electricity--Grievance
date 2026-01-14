// /* Dashboard UI helpers - unified and resilient
//    - supports both data-percentage and data-width attributes
//    - sets up notification close button
//    - initializes status indicators, activity items, progress bars
// */

// // Notification helpers
// function showWelcomeNotification() {
//     const notification = document.getElementById('welcomeNotification');
//     if (notification) {
//         notification.style.display = 'block';
//         setTimeout(closeNotification, 5000);
//     }
// }

// function closeNotification() {
//     const notification = document.getElementById('welcomeNotification');
//     if (notification) notification.style.display = 'none';
// }

// // Filter issues table
// function filterIssues() {
//     const searchEl = document.getElementById('issueSearch');
//     const statusEl = document.getElementById('statusFilter');
//     if (!searchEl || !statusEl) return;

//     const searchText = searchEl.value.toLowerCase();
//     const statusFilter = statusEl.value;
//     const table = document.getElementById('issuesTable');
//     if (!table) return;

//     const rows = table.querySelectorAll('tbody tr');
//     rows.forEach(row => {
//         const cells = row.getElementsByTagName('td');
//         const title = (cells[1] && cells[1].textContent || '').toLowerCase();
//         const status = (cells[3] && cells[3].textContent || '').toLowerCase();
//         const matchesSearch = title.includes(searchText);
//         const matchesStatus = !statusFilter || status.includes(statusFilter);
//         row.style.display = (matchesSearch && matchesStatus) ? '' : 'none';
//     });
// }

// // Status indicators
// function initializeStatusIndicators() {
//     const indicators = document.querySelectorAll('.status-indicator');
//     indicators.forEach(function(indicator) {
//         const available = parseInt(indicator.getAttribute('data-available')) || 0;
//         if (available > 0) {
//             indicator.innerHTML = '🟢 Active';
//             indicator.classList.add('active');
//         } else {
//             indicator.innerHTML = '🔴 Busy';
//             indicator.classList.add('inactive');
//         }
//     });
// }

// // Activity items
// function initializeActivityItems() {
//     const activityTexts = document.querySelectorAll('.activity-text');
//     activityTexts.forEach(function(textElement) {
//         const activityType = textElement.getAttribute('data-activity-type');
//         const userName = textElement.getAttribute('data-user-name');
//         const title = textElement.getAttribute('data-title');
//         const workerName = textElement.getAttribute('data-worker-name');

//         const iconElement = textElement.closest('.activity-item')?.querySelector('.activity-icon');

//         if (activityType === 'issue_raised') {
//             if (iconElement) iconElement.innerHTML = '📝';
//             textElement.innerHTML = `<strong>${userName}</strong> raised issue: "${title}"`;
//         } else {
//             if (iconElement) iconElement.innerHTML = '✅';
//             textElement.innerHTML = `Issue "${title}" resolved by <strong>${workerName}</strong>`;
//         }
//     });
// }

// // Progress bars: support data-percentage or legacy data-width
// function initializeProgressBars() {
//     const progressBars = document.querySelectorAll('.type-bar-fill');
//     progressBars.forEach(function(bar) {
//         const percentage = bar.getAttribute('data-percentage') || bar.getAttribute('data-width');
//         if (percentage) bar.style.width = percentage + '%';
//     });
// }

// // Action buttons
// function initializeActionButtons() {
//     document.querySelectorAll('.edit-issue-btn').forEach(btn => {
//         btn.addEventListener('click', () => { alert('Edit feature coming soon for issue #' + btn.dataset.issueId); });
//     });
//     document.querySelectorAll('.view-logs-btn').forEach(btn => {
//         btn.addEventListener('click', () => { alert('Logs feature coming soon for issue #' + btn.dataset.issueId); });
//     });
// }

// // DOM ready
// document.addEventListener('DOMContentLoaded', function() {
//     showWelcomeNotification();

//     const issueSearch = document.getElementById('issueSearch');
//     const statusFilter = document.getElementById('statusFilter');
//     if (issueSearch) issueSearch.addEventListener('input', filterIssues);
//     if (statusFilter) statusFilter.addEventListener('change', filterIssues);

//     const closeBtn = document.getElementById('closeNotification');
//     if (closeBtn) closeBtn.addEventListener('click', closeNotification);

//     initializeStatusIndicators();
//     initializeActivityItems();
//     initializeProgressBars();
//     initializeActionButtons();

//     // Smooth scroll for internal nav anchors
//     document.querySelectorAll('nav a[href^="#"]').forEach(anchor => {
//         anchor.addEventListener('click', function (e) {
//             e.preventDefault();
//             const target = document.querySelector(this.getAttribute('href'));
//             if (target) target.scrollIntoView({ behavior: 'smooth' });
//         });
//     });
// });



// Dashboard functionality with unified sidebar layout
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard initialized');
    
    // Add active class to current page in sidebar
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.sidebar .nav-link');
    
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
    
    // Card hover effects
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
            this.style.boxShadow = '0 8px 25px rgba(0,0,0,0.15)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '0 4px 15px rgba(0,0,0,0.1)';
        });
    });
    
    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    // Auto-refresh dashboard data every 30 seconds
    setInterval(() => {
        console.log('Auto-refreshing dashboard data...');
        // You can add AJAX calls here to refresh specific components
    }, 30000);
    
    // Welcome message in console
    console.log(`🚀 Welcome to MSEDCL Dashboard, {{ user_name }}!`);
});