// Track Issues JavaScript functionality
let viewIssueModal = null;
let currentSort = { column: 'created_at', direction: 'desc' };

document.addEventListener('DOMContentLoaded', function() {
    console.log('Track Issues page loaded');
    
    // Initialize modal
    viewIssueModal = new bootstrap.Modal(document.getElementById('viewIssueModal'));
    
    // Set today's date as max for date filters
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('fromDateFilter').max = today;
    document.getElementById('toDateFilter').max = today;
    
    // Initialize table sorting
    initializeTableSorting();
    
    // Add active class to current page in sidebar
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.sidebar .nav-link');
    
    navLinks.forEach(function(link) {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
    
    // Validate date range
    validateDateRange();
    
    // Add event listeners for date validation
    document.getElementById('fromDateFilter').addEventListener('change', validateDateRange);
    document.getElementById('toDateFilter').addEventListener('change', validateDateRange);
});

function initializeTableSorting() {
    const headers = document.querySelectorAll('#issuesTable th[data-sort]');
    headers.forEach(header => {
        header.style.cursor = 'pointer';
        header.addEventListener('click', function() {
            const column = this.getAttribute('data-sort');
            sortTable(column);
        });
    });
}

function sortTable(column) {
    const table = document.getElementById('issuesTable');
    if (!table) return;
    
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    // Toggle sort direction if same column
    if (currentSort.column === column) {
        currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
    } else {
        currentSort.column = column;
        currentSort.direction = 'asc';
    }
    
    // Sort rows
    rows.sort((a, b) => {
        let aValue = getCellValue(a, column);
        let bValue = getCellValue(b, column);
        
        // Handle different data types
        if (column === 'created_at') {
            aValue = new Date(aValue.split('/').reverse().join('-'));
            bValue = new Date(bValue.split('/').reverse().join('-'));
        } else if (column === 'issue_id') {
            aValue = parseInt(aValue.replace('#', '')) || 0;
            bValue = parseInt(bValue.replace('#', '')) || 0;
        } else {
            aValue = (aValue || '').toString().toLowerCase();
            bValue = (bValue || '').toString().toLowerCase();
        }
        
        if (currentSort.direction === 'asc') {
            return aValue > bValue ? 1 : -1;
        } else {
            return aValue < bValue ? 1 : -1;
        }
    });
    
    // Update sort indicators
    updateSortIndicators(column);
    
    // Rebuild table
    rows.forEach(row => tbody.appendChild(row));
}

function getCellValue(row, column) {
    const headers = Array.from(row.parentNode.parentNode.querySelectorAll('th[data-sort]'));
    const cellIndex = headers.findIndex(th => th.getAttribute('data-sort') === column);
    
    if (cellIndex === -1) return '';
    
    const cell = row.cells[cellIndex];
    if (!cell) return '';
    
    // For issue ID, get the text without the # symbol
    if (column === 'issue_id') {
        return cell.textContent.replace('#', '').trim();
    }
    
    return cell.textContent.trim();
}

function updateSortIndicators(activeColumn) {
    const headers = document.querySelectorAll('#issuesTable th[data-sort]');
    headers.forEach(header => {
        const icon = header.querySelector('i');
        if (header.getAttribute('data-sort') === activeColumn) {
            icon.className = currentSort.direction === 'asc' ? 
                'fas fa-sort-up' : 'fas fa-sort-down';
        } else {
            icon.className = 'fas fa-sort';
        }
    });
}

function applyQuickDate(range) {
    const today = new Date();
    let fromDate = new Date();
    let toDate = new Date(today); // Default toDate is today
    
    switch(range) {
        case 'today':
            fromDate = new Date(today);
            break;
        case 'yesterday':
            fromDate.setDate(today.getDate() - 1);
            toDate.setDate(today.getDate() - 1);
            break;
        case 'last_week':
            fromDate.setDate(today.getDate() - 7);
            break;
        case 'last_month':
            fromDate.setDate(today.getDate() - 30);
            break;
        case 'this_month':
            fromDate = new Date(today.getFullYear(), today.getMonth(), 1);
            break;
        case 'last_3_months':
            fromDate.setMonth(today.getMonth() - 3);
            break;
        default:
            return;
    }
    
    // Format dates as YYYY-MM-DD
    const formatDate = (date) => date.toISOString().split('T')[0];
    
    document.getElementById('fromDateFilter').value = formatDate(fromDate);
    document.getElementById('toDateFilter').value = formatDate(toDate);
    
    // Reset quick date selector
    document.getElementById('quickDateFilter').value = '';
}

function validateDateRange() {
    const fromDate = document.getElementById('fromDateFilter');
    const toDate = document.getElementById('toDateFilter');
    
    if (fromDate.value && toDate.value && fromDate.value > toDate.value) {
        toDate.setCustomValidity('To date must be after from date');
        toDate.reportValidity();
    } else {
        toDate.setCustomValidity('');
    }
}

function clearFilters() {
    document.getElementById('filterForm').reset();
    window.location.href = '/track-issues';
}

function refreshPage() {
    window.location.reload();
}

function viewIssue(issueId) {
    // Show loading state
    document.getElementById('issueDetailsContent').innerHTML = 
        '<div class="text-center py-4">' +
        '<div class="spinner-border text-primary" role="status">' +
        '<span class="visually-hidden">Loading...</span>' +
        '</div>' +
        '<p class="mt-2">Loading issue details...</p>' +
        '</div>';
    
    // Fetch issue details
    fetch('/api/issue-details/' + issueId)
        .then(function(response) {
            if (!response.ok) {
                throw new Error('Network response was not ok: ' + response.status);
            }
            return response.json();
        })
        .then(function(data) {
            if (data.success) {
                displayIssueDetails(data.issue);
                logIssueView(issueId);
            } else {
                throw new Error(data.error || 'Failed to load issue details');
            }
        })
        .catch(function(error) {
            console.error('Error:', error);
            document.getElementById('issueDetailsContent').innerHTML = 
                '<div class="alert alert-danger">' +
                '<i class="fas fa-exclamation-triangle me-2"></i>' +
                'Error loading issue details: ' + error.message +
                '</div>';
        });
    
    viewIssueModal.show();
}

function displayIssueDetails(issue) {
    const typeLabels = {
        'power_outage': 'Power Outage',
        'voltage_fluctuation': 'Voltage Fluctuation', 
        'meter_problem': 'Meter Problem',
        'billing_dispute': 'Billing Dispute',
        'safety_hazard': 'Safety Hazard',
        'equipment_damage': 'Equipment Damage',
        'street_light_fault': 'Street Light Fault',
        'transformer_issue': 'Transformer Issue',
        'wire_fault': 'Wire Fault',
        'electric_shock': 'Electric Shock',
        'other': 'Other'
    };
    
    // Determine worker assignment display based on issue status
    let workerAssignmentHtml = '';
    
    if (issue.status === 'resolved') {
        // For resolved issues, show completion message
        workerAssignmentHtml = 
            '<div class="alert alert-success mb-0">' +
            '<div class="d-flex align-items-center">' +
            '<i class="fas fa-check-circle fa-2x me-3"></i>' +
            '<div>' +
            '<h6 class="alert-heading mb-1">Issue Resolved Successfully</h6>' +
            '<p class="mb-0">' +
            'This issue has been completed and resolved.' +
            (issue.assigned_worker_names ? '<br><small>Workers involved: ' + issue.assigned_worker_names + '</small>' : '') +
            '</p>' +
            '</div>' +
            '</div>' +
            '</div>';
    } else {
        // For pending issues, show assignment status
        if (issue.assigned_workers_count > 0) {
            workerAssignmentHtml = 
                '<div class="alert alert-success mb-0">' +
                '<div class="d-flex align-items-center">' +
                '<i class="fas fa-check-circle fa-2x me-3"></i>' +
                '<div>' +
                '<h6 class="alert-heading mb-1">Workers Assigned</h6>' +
                '<p class="mb-0">' +
                '<strong>' + (issue.assigned_workers_count || 0) + ' worker(s)</strong> are working on your issue.' +
                (issue.assigned_worker_names ? '<br><small>Assigned workers: ' + issue.assigned_worker_names + '</small>' : '') +
                '</p>' +
                '</div>' +
                '</div>' +
                '</div>';
        } else {
            workerAssignmentHtml = 
                '<div class="alert alert-info mb-0">' +
                '<div class="d-flex align-items-center">' +
                '<i class="fas fa-clock fa-2x me-3"></i>' +
                '<div>' +
                '<h6 class="alert-heading mb-1">Awaiting Assignment</h6>' +
                '<p class="mb-0">' +
                'No workers assigned yet. Your issue is in the queue and will be assigned to available workers soon.' +
                '</p>' +
                '</div>' +
                '</div>' +
                '</div>';
        }
    }
    
    const content = 
        '<div class="row mb-3">' +
        '<div class="col-12">' +
        '<h5 class="text-primary">#' + (issue.issue_id || '') + ' - ' + (issue.title || '') + '</h5>' +
        '<p class="text-muted mb-0">' + (typeLabels[issue.issue_type] || issue.issue_type || '') + '</p>' +
        '</div>' +
        '</div>' +
        
        '<div class="row mb-3">' +
        '<div class="col-md-6">' +
        '<strong>Status:</strong>' +
        '<span class="status-badge status-' + (issue.status || '') + ' ms-2">' +
        '<i class="fas ' + (issue.status === 'pending' ? 'fa-clock' : 'fa-check-circle') + ' me-1"></i>' +
        (issue.status === 'pending' ? 'Pending' : 'Resolved') +
        '</span>' +
        '</div>' +
        '<div class="col-md-6">' +
        '<strong>Priority:</strong>' +
        '<span class="priority-badge priority-' + (issue.priority || '') + ' ms-2">' +
        '<i class="fas ' + 
        (issue.priority === 'low' ? 'fa-arrow-down' : 
         issue.priority === 'medium' ? 'fa-minus' : 
         issue.priority === 'high' ? 'fa-arrow-up' : 'fa-exclamation-triangle') + 
        ' me-1"></i>' +
        (issue.priority ? issue.priority.charAt(0).toUpperCase() + issue.priority.slice(1) : '') +
        '</span>' +
        '</div>' +
        '</div>' +
        
        '<div class="row mb-3">' +
        '<div class="col-12">' +
        '<strong>Division:</strong>' +
        '<span class="ms-2">' + (issue.division_name || '') + '</span>' +
        '</div>' +
        '</div>' +
        
        '<div class="row">' +
        '<div class="col-12">' +
        '<div class="card border-0 bg-light">' +
        '<div class="card-body">' +
        '<h6 class="card-title">' +
        '<i class="fas fa-users me-2"></i>' + 
        (issue.status === 'resolved' ? 'Resolution Status' : 'Worker Assignment Status') +
        '</h6>' +
        workerAssignmentHtml +
        '</div>' +
        '</div>' +
        '</div>' +
        '</div>' +
        
        ((issue.status === 'pending') ? 
            '<div class="row mt-3">' +
            '<div class="col-12">' +
            '<div class="alert alert-warning">' +
            '<i class="fas fa-info-circle me-2"></i>' +
            '<strong>Note:</strong> You can edit this issue while it\'s pending. Click the "Edit" button in the issues table.' +
            '</div>' +
            '</div>' +
            '</div>' : '');
    
    document.getElementById('issueDetailsContent').innerHTML = content;
}

function logIssueView(issueId) {
    fetch('/api/log-issue-view', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            issue_id: issueId,
            action_type: 'VIEWED'
        })
    }).catch(function(error) {
        console.error('Error logging view:', error);
    });
}

function editIssue(issueId) {
    window.location.href = '/edit-issue/' + issueId;
}

function exportToCSV() {
    const table = document.getElementById('issuesTable');
    if (!table) {
        alert('No data to export');
        return;
    }
    
    let csv = [];
    const rows = table.querySelectorAll('tr');
    
    // Get headers (skip the Actions column)
    const headers = [];
    table.querySelectorAll('thead th').forEach((th, index) => {
        if (index < rows[0].cells.length - 1) { // Exclude last column (Actions)
            headers.push('"' + th.textContent.replace(/"/g, '""').trim() + '"');
        }
    });
    csv.push(headers.join(','));
    
    // Get data rows (skip the Actions column)
    for (let i = 1; i < rows.length; i++) {
        const row = [], cols = rows[i].querySelectorAll('td');
        
        for (let j = 0; j < cols.length - 1; j++) { // Exclude last column
            const text = cols[j].textContent.replace(/"/g, '""').trim();
            row.push('"' + text + '"');
        }
        csv.push(row.join(','));
    }
    
    // Download CSV file
    const csvString = csv.join('\n');
    const blob = new Blob([csvString], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', 'msedcl_issues_' + new Date().toISOString().split('T')[0] + '.csv');
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Auto-refresh every 30 seconds if there are pending issues
setInterval(function() {
    const hasPendingIssues = document.querySelector('.status-pending');
    if (hasPendingIssues) {
        console.log('Auto-refreshing for pending issues...');
        refreshPage();
    }
}, 30000);

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl+F to focus on search/filters
    if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
        e.preventDefault();
        document.getElementById('statusFilter').focus();
    }
    
    // F5 to refresh
    if (e.key === 'F5') {
        e.preventDefault();
        refreshPage();
    }
});

// Performance optimization: Debounce resize events
let resizeTimeout;
window.addEventListener('resize', function() {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(function() {
        // Recalculate any responsive elements if needed
        console.log('Window resized - responsive adjustments applied');
    }, 250);
});