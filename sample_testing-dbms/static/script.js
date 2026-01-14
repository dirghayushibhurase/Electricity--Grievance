// Show welcome notification
function showWelcomeNotification() {
    const notification = document.getElementById('welcomeNotification');
    if (notification) {
        notification.style.display = 'block';
        
        // Auto hide after 5 seconds
        setTimeout(function() {
            closeNotification();
        }, 5000);
    }
}

function closeNotification() {
    const notification = document.getElementById('welcomeNotification');
    if (notification) {
        notification.style.display = 'none';
    }
}

// Filter issues table
function filterIssues() {
    const searchText = document.getElementById('issueSearch').value.toLowerCase();
    const statusFilter = document.getElementById('statusFilter').value;
    const table = document.getElementById('issuesTable');
    
    if (!table) {
        return;
    }
    
    const rows = table.getElementsByTagName('tbody')[0].getElementsByTagName('tr');

    for (let i = 0; i < rows.length; i++) {
        const row = rows[i];
        const cells = row.getElementsByTagName('td');
        const title = cells[1].textContent.toLowerCase();
        const status = cells[3].textContent.toLowerCase();
        
        const matchesSearch = title.includes(searchText);
        const matchesStatus = !statusFilter || status.includes(statusFilter);
        
        if (matchesSearch && matchesStatus) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    }
}

// Function to handle edit issue
function handleEditIssue(issueId) {
    alert('Edit issue #' + issueId + ' - This functionality will be implemented soon!');
}

// Function to handle view logs
function handleViewLogs(issueId) {
    alert('View logs for issue #' + issueId + ' - This functionality will be implemented soon!');
}

// Initialize status indicators
function initializeStatusIndicators() {
    const indicators = document.querySelectorAll('.status-indicator');
    indicators.forEach(function(indicator) {
        const available = parseInt(indicator.getAttribute('data-available'));
        if (available > 0) {
            indicator.innerHTML = '🟢 Active';
            indicator.classList.add('active');
        } else {
            indicator.innerHTML = '🔴 Busy';
            indicator.classList.add('inactive');
        }
    });
}

// Initialize activity items
function initializeActivityItems() {
    const activityTexts = document.querySelectorAll('.activity-text');
    activityTexts.forEach(function(textElement) {
        const activityType = textElement.getAttribute('data-activity-type');
        const userName = textElement.getAttribute('data-user-name');
        const title = textElement.getAttribute('data-title');
        const workerName = textElement.getAttribute('data-worker-name');
        
        const iconElement = textElement.closest('.activity-item').querySelector('.activity-icon');
        
        if (activityType === 'issue_raised') {
            iconElement.innerHTML = '📝';
            textElement.innerHTML = `<strong>${userName}</strong> raised issue: "${title}"`;
        } else {
            iconElement.innerHTML = '✅';
            textElement.innerHTML = `Issue "${title}" resolved by <strong>${workerName}</strong>`;
        }
    });
}

// Initialize progress bars
function initializeProgressBars() {
    const progressBars = document.querySelectorAll('.type-bar-fill');
    progressBars.forEach(function(bar) {
        const percentage = bar.getAttribute('data-percentage');
        if (percentage) {
            bar.style.width = percentage + '%';
        }
    });
}

// Initialize event listeners for action buttons
function initializeActionButtons() {
    // Edit issue buttons
    const editButtons = document.querySelectorAll('.edit-issue-btn');
    editButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            const issueId = this.getAttribute('data-issue-id');
            handleEditIssue(issueId);
        });
    });
    
    // View logs buttons
    const logsButtons = document.querySelectorAll('.view-logs-btn');
    logsButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            const issueId = this.getAttribute('data-issue-id');
            handleViewLogs(issueId);
        });
    });
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    showWelcomeNotification();
    
    // Add event listeners for filtering
    const issueSearch = document.getElementById('issueSearch');
    const statusFilter = document.getElementById('statusFilter');
    
    if (issueSearch) {
        issueSearch.addEventListener('input', filterIssues);
    }
    if (statusFilter) {
        statusFilter.addEventListener('change', filterIssues);
    }
    
    // Close notification button
    const closeBtn = document.getElementById('closeNotification');
    if (closeBtn) {
        closeBtn.addEventListener('click', closeNotification);
    }
    
    // Initialize all components
    initializeStatusIndicators();
    initializeActivityItems();
    initializeProgressBars();
    initializeActionButtons();
    
    // Smooth scroll for navigation
    const navLinks = document.querySelectorAll('nav a[href^="#"]');
    navLinks.forEach(function(anchor) {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const target = document.querySelector(targetId);
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
});