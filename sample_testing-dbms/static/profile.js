// Profile Management JavaScript
document.addEventListener('DOMContentLoaded', function() {
    console.log('Profile page loaded');
    
    // Load audit log
    loadAuditLog();
    
    // Initialize form handlers
    initializeFormHandlers();
    
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
});

function initializeFormHandlers() {
    // Profile form submission
    const profileForm = document.getElementById('profileForm');
    if (profileForm) {
        profileForm.addEventListener('submit', function(e) {
            e.preventDefault();
            updateProfile();
        });
    }
    
    // Password form submission
    const passwordForm = document.getElementById('passwordForm');
    if (passwordForm) {
        passwordForm.addEventListener('submit', function(e) {
            e.preventDefault();
            changePassword();
        });
    }
    
    // Edit profile button
    const editBtn = document.getElementById('editProfileBtn');
    if (editBtn) {
        editBtn.addEventListener('click', enableEditing);
    }
    
    // Cancel edit button
    const cancelBtn = document.getElementById('cancelEditBtn');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', disableEditing);
    }
    
    // Real-time password validation
    const newPassword = document.getElementById('newPassword');
    const confirmPassword = document.getElementById('confirmPassword');
    
    if (newPassword && confirmPassword) {
        confirmPassword.addEventListener('input', validatePasswordMatch);
    }
}

function enableEditing() {
    const form = document.getElementById('profileForm');
    const inputs = form.querySelectorAll('input');
    const selects = form.querySelectorAll('select');
    
    // Enable name, email, phone inputs (keep joined_date disabled)
    inputs.forEach(input => {
        if (input.name === 'name' || input.name === 'email' || input.name === 'phone') {
            input.readOnly = false;
        }
        // Address fields
        if (input.name === 'address_line1' || input.name === 'address_line2' || 
            input.name === 'city' || input.name === 'pincode') {
            input.readOnly = false;
        }
        // Keep joined_date disabled
        if (input.name === 'joined_date') {
            input.disabled = true;
        }
    });
    
    // Enable selects
    selects.forEach(select => {
        select.disabled = false;
    });
    
    // Show/hide buttons
    document.getElementById('editProfileBtn').style.display = 'none';
    document.getElementById('saveProfileBtn').style.display = 'block';
    document.getElementById('cancelEditBtn').style.display = 'block';
    
    showAlert('You can now edit your profile information.', 'info');
}

function disableEditing() {
    const form = document.getElementById('profileForm');
    const inputs = form.querySelectorAll('input');
    const selects = form.querySelectorAll('select');
    
    // Disable all inputs except joined_date (keep it permanently disabled)
    inputs.forEach(input => {
        if (input.name !== 'joined_date') {
            input.readOnly = true;
        }
    });
    
    selects.forEach(select => {
        select.disabled = true;
    });
    
    // Show/hide buttons
    document.getElementById('editProfileBtn').style.display = 'block';
    document.getElementById('saveProfileBtn').style.display = 'none';
    document.getElementById('cancelEditBtn').style.display = 'none';
    
    showAlert('Editing cancelled.', 'warning');
}

function updateProfile() {
    const form = document.getElementById('profileForm');
    const formData = new FormData(form);
    const submitBtn = document.getElementById('saveProfileBtn');
    
    // Show loading state
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Saving...';
    submitBtn.disabled = true;
    
    fetch(form.action, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Profile updated successfully!', 'success');
            disableEditing();
            // Reload audit log to show the update
            loadAuditLog();
            // Update the header with new name if changed
            const nameInput = document.querySelector('input[name="name"]');
            if (nameInput) {
                const userNameElements = document.querySelectorAll('.navbar-text');
                userNameElements.forEach(element => {
                    const text = element.textContent;
                    if (text.includes('Welcome,')) {
                        element.textContent = `Welcome, ${nameInput.value}`;
                    }
                });
            }
        } else {
            throw new Error(data.error || 'Failed to update profile');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Error updating profile: ' + error.message, 'danger');
    })
    .finally(() => {
        submitBtn.innerHTML = '<i class="fas fa-save me-1"></i>Save Changes';
        submitBtn.disabled = false;
    });
}

function changePassword() {
    const form = document.getElementById('passwordForm');
    const formData = new FormData(form);
    const submitBtn = form.querySelector('button[type="submit"]');
    
    // Validate password match
    if (!validatePasswordMatch()) {
        return;
    }
    
    // Show loading state
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Changing...';
    submitBtn.disabled = true;
    
    fetch(form.action, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Password changed successfully!', 'success');
            form.reset();
            // Reload audit log to show the password change
            loadAuditLog();
        } else {
            throw new Error(data.error || 'Failed to change password');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Error changing password: ' + error.message, 'danger');
    })
    .finally(() => {
        submitBtn.innerHTML = '<i class="fas fa-key me-1"></i>Change Password';
        submitBtn.disabled = false;
    });
}

function validatePasswordMatch() {
    const newPassword = document.getElementById('newPassword');
    const confirmPassword = document.getElementById('confirmPassword');
    
    if (newPassword.value !== confirmPassword.value) {
        confirmPassword.setCustomValidity('Passwords do not match');
        confirmPassword.reportValidity();
        return false;
    } else {
        confirmPassword.setCustomValidity('');
        return true;
    }
}

function togglePassword(inputId) {
    const input = document.getElementById(inputId);
    const icon = input.parentNode.querySelector('i');
    
    if (input.type === 'password') {
        input.type = 'text';
        icon.className = 'fas fa-eye-slash';
    } else {
        input.type = 'password';
        icon.className = 'fas fa-eye';
    }
}

function loadAuditLog() {
    fetch('/api/user-audit-log')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayAuditLog(data.logs);
            } else {
                throw new Error(data.error || 'Failed to load activity');
            }
        })
        .catch(error => {
            console.error('Error loading audit log:', error);
            document.getElementById('auditLogContent').innerHTML = 
                '<div class="alert alert-warning">Could not load recent activity.</div>';
        });
}

function displayAuditLog(logs) {
    const container = document.getElementById('auditLogContent');
    
    if (!logs || logs.length === 0) {
        container.innerHTML = 
            '<div class="text-center py-3 text-muted">' +
            '<i class="fas fa-history fa-2x mb-2"></i>' +
            '<p>No recent activity found.</p>' +
            '</div>';
        return;
    }
    
    let html = '';
    logs.forEach(log => {
        const actionText = formatActionType(log.action_type);
        const timestamp = new Date(log.changed_at).toLocaleString();
        
        html += 
            '<div class="audit-item">' +
            '<div class="audit-action">' + actionText + '</div>' +
            '<div class="audit-time">' + timestamp + '</div>' +
            '</div>';
    });
    
    container.innerHTML = html;
}

function formatActionType(actionType) {
    const actionMap = {
        'PROFILE_UPDATED': 'Profile Updated',
        'PASSWORD_CHANGED': 'Password Changed', 
        'EMAIL_CHANGED': 'Email Changed'
    };
    return actionMap[actionType] || actionType.replace('_', ' ').toLowerCase();
}

function showAlert(message, type) {
    const container = document.getElementById('alertContainer');
    const alertId = 'alert-' + Date.now();
    
    const alert = 
        '<div id="' + alertId + '" class="alert alert-' + type + ' alert-profile alert-dismissible fade show" role="alert">' +
        '<i class="fas ' + getAlertIcon(type) + ' me-2"></i>' +
        message +
        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' +
        '</div>';
    
    container.innerHTML = alert;
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        const alertElement = document.getElementById(alertId);
        if (alertElement) {
            const bsAlert = new bootstrap.Alert(alertElement);
            bsAlert.close();
        }
    }, 5000);
}

function getAlertIcon(type) {
    const icons = {
        'success': 'fa-check-circle',
        'danger': 'fa-exclamation-triangle',
        'warning': 'fa-exclamation-circle',
        'info': 'fa-info-circle'
    };
    return icons[type] || 'fa-info-circle';
}

// Input validation
document.addEventListener('input', function(e) {
    if (e.target.type === 'tel') {
        // Basic phone number validation
        e.target.value = e.target.value.replace(/[^\d+-\s]/g, '');
    }
    
    if (e.target.name === 'pincode') {
        // Pincode validation (6 digits)
        e.target.value = e.target.value.replace(/\D/g, '').slice(0, 6);
    }
});