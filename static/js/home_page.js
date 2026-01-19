  let selectedEmployeeId = null;

// Get CSRF token helper function
function getCookie(name) {
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

// Clear error messages
function clearErrors() {
    document.querySelectorAll('.error-messages').forEach(el => {
        el.innerHTML = '';
    });
    document.querySelectorAll('.form-control.is-invalid').forEach(el => {
        el.classList.remove('is-invalid');
    });
}

// Show error messages
function showErrors(errors) {
    clearErrors();
    
    for (const field in errors) {
        const fieldName = field === '__all__' ? 'general' : field;
        const errorContainer = document.getElementById(`${fieldName}-errors`);
        const inputField = document.getElementById(`id_${fieldName}`);
        
        if (errorContainer) {
            errors[field].forEach(error => {
                const errorDiv = document.createElement('div');
                errorDiv.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${error}`;
                errorContainer.appendChild(errorDiv);
            });
        }
        
        if (inputField) {
            inputField.classList.add('is-invalid');
        }
    }
}

// Show notification
function showNotification(type, message) {
    // Remove existing notifications
    document.querySelectorAll('.notification').forEach(n => n.remove());
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div style="display: flex; align-items: center; gap: 10px;">
            <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
            <span>${message}</span>
        </div>
        <button onclick="this.parentElement.remove()" style="background: none; border: none; color: inherit; cursor: pointer;">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    // Style the notification
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background: ${type === 'success' ? 'var(--success)' : 'var(--danger)'};
        color: white;
        border-radius: var(--radius);
        box-shadow: var(--shadow-lg);
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 15px;
        min-width: 300px;
        max-width: 400px;
        z-index: 1000;
        animation: slideIn 0.3s ease;
    `;
    
    document.body.appendChild(notification);
    
    // Remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }
    }, 5000);
}

// Update avatar preview for add form
function updateAvatarPreview() {
    const firstName = document.getElementById('id_first_name')?.value || '';
    const lastName = document.getElementById('id_last_name')?.value || '';
    const fullName = `${firstName} ${lastName}`.trim() || 'User';
    const avatarPreview = document.getElementById('avatarPreview');
    
    if (avatarPreview) {
        // Create avatar with initials
        const initials = fullName.split(' ').map(n => n[0]).join('').toUpperCase();
        avatarPreview.innerHTML = `<span style="font-weight: bold; font-size: 2rem;">${initials}</span>`;
        
        // Set background color based on name
        const colors = [
            'linear-gradient(135deg, #4361ee 0%, #3a56d4 100%)',
            'linear-gradient(135deg, #7209b7 0%, #5e0896 100%)',
            'linear-gradient(135deg, #06d6a0 0%, #05c190 100%)',
            'linear-gradient(135deg, #ef476f 0%, #e6355e 100%)',
            'linear-gradient(135deg, #4cc9f0 0%, #3ab7e0 100%)',
        ];
        
        // Simple hash function to get consistent color for same name
        let hash = 0;
        for (let i = 0; i < fullName.length; i++) {
            hash = fullName.charCodeAt(i) + ((hash << 5) - hash);
        }
        const colorIndex = Math.abs(hash) % colors.length;
        
        avatarPreview.style.background = colors[colorIndex];
    }
}

// Update avatar preview for edit form
function updateEditAvatarPreview() {
    const firstName = document.getElementById('edit_first_name')?.value || '';
    const lastName = document.getElementById('edit_last_name')?.value || '';
    const fullName = `${firstName} ${lastName}`.trim() || 
                     document.getElementById('edit_username')?.value || 'User';
    
    const avatarPreview = document.getElementById('edit_avatarPreview');
    
    if (avatarPreview) {
        const initials = fullName.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2);
        avatarPreview.innerHTML = `<span style="font-weight: bold; font-size: 2rem;">${initials}</span>`;
        
        // Set consistent background color
        const colors = [
            'linear-gradient(135deg, #4361ee 0%, #3a56d4 100%)',
            'linear-gradient(135deg, #7209b7 0%, #5e0896 100%)',
            'linear-gradient(135deg, #06d6a0 0%, #05c190 100%)',
            'linear-gradient(135deg, #ef476f 0%, #e6355e 100%)',
            'linear-gradient(135deg, #4cc9f0 0%, #3ab7e0 100%)',
        ];
        
        let hash = 0;
        for (let i = 0; i < fullName.length; i++) {
            hash = fullName.charCodeAt(i) + ((hash << 5) - hash);
        }
        const colorIndex = Math.abs(hash) % colors.length;
        
        avatarPreview.style.background = colors[colorIndex];
    }
}

// Update character count for address in add form
function updateCharCount() {
    const addressField = document.getElementById('id_address');
    const charCount = document.getElementById('addressCharCount');
    
    if (addressField && charCount) {
        const currentLength = addressField.value.length;
        const maxLength = 100;
        charCount.textContent = `${currentLength}/${maxLength}`;
        
        if (currentLength > maxLength * 0.9) {
            charCount.style.color = 'var(--warning)';
        } else if (currentLength > maxLength) {
            charCount.style.color = 'var(--danger)';
        } else {
            charCount.style.color = 'var(--gray)';
        }
    }
}

// Update character count for address in edit form
function updateEditCharCount() {
    const addressField = document.getElementById('edit_address');
    const charCount = document.getElementById('edit_addressCharCount');
    
    if (addressField && charCount) {
        const currentLength = addressField.value.length;
        const maxLength = 100;
        charCount.textContent = `${currentLength}/${maxLength}`;
        
        if (currentLength > maxLength * 0.9) {
            charCount.style.color = 'var(--warning)';
        } else if (currentLength > maxLength) {
            charCount.style.color = 'var(--danger)';
        } else {
            charCount.style.color = 'var(--gray)';
        }
    }
}

// Check password strength
function checkPasswordStrength(password) {
    const strengthFill = document.getElementById('passwordStrengthFill');
    const strengthText = document.getElementById('passwordStrengthText');
    
    if (!strengthFill || !strengthText) return;
    
    let strength = 0;
    let text = '';
    let color = '';
    let width = '0%';
    
    // Check password length
    if (password.length >= 8) strength += 1;
    
    // Check for lowercase letters
    if (/[a-z]/.test(password)) strength += 1;
    
    // Check for uppercase letters
    if (/[A-Z]/.test(password)) strength += 1;
    
    // Check for numbers
    if (/[0-9]/.test(password)) strength += 1;
    
    // Check for special characters
    if (/[^A-Za-z0-9]/.test(password)) strength += 1;
    
    // Determine strength level
    if (password.length === 0) {
        text = 'Password strength';
        color = 'var(--gray)';
        width = '0%';
    } else if (strength < 2) {
        text = 'Weak';
        color = 'var(--danger)';
        width = '33%';
    } else if (strength < 4) {
        text = 'Fair';
        color = 'var(--warning)';
        width = '66%';
    } else {
        text = 'Strong';
        color = 'var(--success)';
        width = '100%';
    }
    
    strengthFill.style.width = width;
    strengthFill.style.background = color;
    strengthText.textContent = text;
    strengthText.style.color = color;
}

// Live search functionality
document.getElementById('live-search')?.addEventListener('input', function(e) {
    const searchTerm = e.target.value.toLowerCase();
    const rows = document.querySelectorAll('#employee-table-body tr');
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        if (text.includes(searchTerm)) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
});

// View employee details
async function viewEmployee(employeeId) {
    selectedEmployeeId = employeeId;
    const modal = document.getElementById('employeeModal');
    const modalBody = document.getElementById('employeeModalBody');
    
    modalBody.innerHTML = '<div class="spinner"></div>';
    modal.classList.add('active');
    
    try {
        // Find the employee row to get data from the table
        const row = document.querySelector(`tr[data-employee-id="${employeeId}"]`);
        if (row) {
            const employeeName = row.querySelector('.employee-name').textContent.trim();
            const username = row.querySelector('.employee-username').textContent.trim().replace('@', '');
            const email = row.querySelector('.fa-envelope').parentNode.textContent.trim();
            const phone = row.querySelector('.fa-phone').parentNode.textContent.trim();
            const address = row.querySelector('.fa-map-marker-alt').parentNode.textContent.trim();
            const department = row.querySelector('.badge-primary')?.textContent.trim() || 'No Department';
            const role = row.querySelector('.role-badge').textContent.trim();
            const status = row.querySelector('.badge-success, .badge-danger')?.textContent.trim() || 'Unknown';
            const joined = row.querySelector('td:nth-child(6) div:first-child').textContent.trim();
            
            modalBody.innerHTML = `
              <div style="display: flex; gap: 20px; margin-bottom: 20px;">
                <img 
                  src="https://ui-avatars.com/api/?name=${encodeURIComponent(employeeName)}&background=4361ee&color=fff&size=100"
                  alt="Employee Avatar"
                  style="width: 100px; height: 100px; border-radius: 50%; border: 3px solid var(--primary);"
                />
                <div>
                  <h2 style="margin-bottom: 5px;">${employeeName}</h2>
                  <p style="color: var(--gray);">@${username} | Employee ID: ${employeeId}</p>
                  <div style="display: flex; gap: 10px; margin-top: 10px;">
                    <span class="badge badge-primary">${department}</span>
                    <span class="role-badge role-${role.toLowerCase().split(' ')[0]}">${role}</span>
                    <span class="badge ${status === 'Active' ? 'badge-success' : 'badge-danger'}">
                      ${status}
                    </span>
                  </div>
                </div>
              </div>
              
              <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin-top: 20px;">
                <div>
                  <h4><i class="fas fa-envelope"></i> Contact Information</h4>
                  <p><strong>Email:</strong> ${email}</p>
                  <p><strong>Phone:</strong> ${phone}</p>
                  <p><strong>Address:</strong> ${address}</p>
                </div>
                <div>
                  <h4><i class="fas fa-briefcase"></i> Work Information</h4>
                  <p><strong>Department:</strong> ${department}</p>
                  <p><strong>Role:</strong> ${role}</p>
                  <p><strong>Joined:</strong> ${joined}</p>
                  <p><strong>Employee ID:</strong> ${employeeId}</p>
                </div>
              </div>
              
              <div style="margin-top: 20px; padding: 15px; background: var(--light); border-radius: var(--radius);">
                <h4><i class="fas fa-history"></i> Account Information</h4>
                <p><strong>Status:</strong> ${status}</p>
                <p><strong>Username:</strong> @${username}</p>
              </div>
            `;
        } else {
            modalBody.innerHTML = `<div class="empty-state"><i class="fas fa-exclamation-circle"></i><h3>Error</h3><p>Employee data not found</p></div>`;
        }
    } catch (error) {
        console.error('Error loading employee details:', error);
        modalBody.innerHTML = `<div class="empty-state"><i class="fas fa-exclamation-circle"></i><h3>Error</h3><p>Failed to load employee details</p></div>`;
    }
}

// Toggle employee status (activate/deactivate)
async function toggleEmployeeStatus(employeeId, action) {
    if (confirm(`Are you sure you want to ${action} this employee?`)) {
        try {
            const response = await fetch(`/toggle-status/${employeeId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({})
            });
            
            const data = await response.json();
            
            if (data.success) {
                showNotification('success', data.message);
                
                // Update the row in the table
                const row = document.querySelector(`tr[data-employee-id="${employeeId}"]`);
                if (row) {
                    const statusCell = row.querySelector('.badge-success, .badge-danger');
                    const newStatus = data.is_active ? 'Active' : 'Inactive';
                    const newStatusClass = data.is_active ? 'badge-success' : 'badge-danger';
                    
                    if (statusCell) {
                        statusCell.className = `badge ${newStatusClass}`;
                        statusCell.innerHTML = `<i class="fas fa-${data.is_active ? 'check' : 'times'}-circle"></i> ${newStatus}`;
                    }
                    
                    // Update row class
                    row.className = data.is_active ? 'active' : 'inactive';
                    
                    // Update the button
                    const statusBtn = row.querySelector('.action-buttons').lastElementChild;
                    if (statusBtn) {
                        if (data.is_active) {
                            statusBtn.className = 'btn btn-outline btn-xs btn-icon';
                            statusBtn.innerHTML = '<i class="fas fa-user-slash"></i>';
                            statusBtn.onclick = () => toggleEmployeeStatus(employeeId, 'deactivate');
                            statusBtn.title = 'Deactivate';
                        } else {
                            statusBtn.className = 'btn btn-success btn-xs btn-icon';
                            statusBtn.innerHTML = '<i class="fas fa-user-check"></i>';
                            statusBtn.onclick = () => toggleEmployeeStatus(employeeId, 'activate');
                            statusBtn.title = 'Activate';
                        }
                    }
                }
            } else {
                showNotification('error', data.error || 'Failed to update status');
            }
        } catch (error) {
            console.error('Error:', error);
            showNotification('error', 'Failed to update employee status');
        }
    }
}

// Update the deleteEmployee function with better error handling
async function deleteEmployee(employeeId) {
    if (confirm('Are you sure you want to delete this employee? This action cannot be undone.')) {
        try {
            const response = await fetch(`/delete-employee/${employeeId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json'
                },
                credentials: 'same-origin'  // Important for session/cookie authentication
            });
            
            // Check if response is OK
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                showNotification('success', data.message);
                
                // Remove the row from the table
                const row = document.querySelector(`tr[data-employee-id="${employeeId}"]`);
                if (row) {
                    row.style.transition = 'all 0.3s ease';
                    row.style.opacity = '0';
                    row.style.transform = 'translateX(-100px)';
                    
                    // Remove row after animation
                    setTimeout(() => {
                        row.remove();
                        
                        // Check if table is empty
                        const tableBody = document.getElementById('employee-table-body');
                        if (tableBody && tableBody.children.length === 0) {
                            tableBody.innerHTML = `
                                <tr>
                                    <td colspan="7">
                                        <div class="empty-state">
                                            <i class="fas fa-users-slash"></i>
                                            <h3>No employees found</h3>
                                            <p>Try adjusting your filters or add new employees.</p>
                                            <button class="btn btn-primary" onclick="showAddEmployeeModal()" style="margin-top: 15px;">
                                                <i class="fas fa-user-plus"></i> Add First Employee
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            `;
                        }
                    }, 300);
                }
                
                // Refresh stats after 1 second
                setTimeout(() => {
                    refreshStats();
                }, 1000);
                
            } else {
                showNotification('error', data.error || 'Failed to delete employee');
            }
        } catch (error) {
            console.error('Delete error details:', error);
            showNotification('error', `Failed to delete employee: ${error.message}`);
        }
    }
}


async function refreshStats() {
    try {
        
        showNotification('info', 'Employee deleted. Page will refresh to update statistics.');
        setTimeout(() => {
            window.location.reload();
        }, 2000);
        
    } catch (error) {
        console.error('Error refreshing stats:', error);
    }
}
// Load employee data for editing
async function editEmployee(employeeId) {
    selectedEmployeeId = employeeId;
    
    try {
        const response = await fetch(`/edit-employee/${employeeId}/`, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            const employee = data.employee;
            
            // Fill the form with employee data
            document.getElementById('edit_employee_id').value = employee.id;
            document.getElementById('edit_username').value = employee.username;
            document.getElementById('edit_email').value = employee.email;
            document.getElementById('edit_first_name').value = employee.first_name || '';
            document.getElementById('edit_last_name').value = employee.last_name || '';
            document.getElementById('edit_phone_number').value = employee.phone_number;
            document.getElementById('edit_department').value = employee.department_id || '';
            document.getElementById('edit_address').value = employee.address || '';
            document.getElementById('edit_role').value = employee.role;
            document.getElementById('edit_is_active').checked = employee.is_active;
            
            // Update character count
            updateEditCharCount();
            
            // Update avatar preview
            updateEditAvatarPreview();
            
            // Clear password fields
            document.getElementById('edit_password1').value = '';
            document.getElementById('edit_password2').value = '';
            
            // Clear any previous errors
            document.querySelectorAll('#editEmployeeForm .error-messages').forEach(el => {
                el.innerHTML = '';
            });
            document.querySelectorAll('#editEmployeeForm .form-control.is-invalid').forEach(el => {
                el.classList.remove('is-invalid');
            });
            
            // Show the edit modal
            const modal = document.getElementById('editEmployeeModal');
            modal.classList.add('active');
            
        } else {
            showNotification('error', data.error || 'Failed to load employee data');
        }
    } catch (error) {
        console.error('Error loading employee data:', error);
        showNotification('error', 'Failed to load employee data');
    }
}

// Update employee in table after edit
function updateEmployeeInTable(employee) {
    const row = document.querySelector(`tr[data-employee-id="${employee.id}"]`);
    
    if (!row) return;
    
    // Update employee info
    const nameCell = row.querySelector('.employee-name');
    const usernameCell = row.querySelector('.employee-username');
    const emailCell = row.querySelector('.fa-envelope').parentNode;
    const phoneCell = row.querySelector('.fa-phone').parentNode;
    const deptCell = row.querySelector('.badge-primary, .badge-warning');
    const roleCell = row.querySelector('.role-badge');
    const statusCell = row.querySelector('.badge-success, .badge-danger');
    const statusClass = employee.status === 'Active' ? 'badge-success' : 'badge-danger';
    
    if (nameCell) {
        nameCell.textContent = employee.name;
    }
    
    if (usernameCell) {
        usernameCell.textContent = `@${employee.username}`;
    }
    
    if (emailCell) {
        emailCell.innerHTML = `<i class="fas fa-envelope"></i> ${employee.email}`;
    }
    
    if (phoneCell) {
        phoneCell.innerHTML = `<i class="fas fa-phone"></i> ${employee.phone}`;
    }
    
    if (deptCell) {
        deptCell.className = 'badge badge-primary';
        deptCell.innerHTML = `<i class="fas fa-building"></i> ${employee.department}`;
    }
    
    if (roleCell) {
        roleCell.className = `role-badge role-${employee.role.toLowerCase()}`;
        roleCell.innerHTML = `<i class="fas fa-user-tag"></i> ${employee.role}`;
    }
    
    if (statusCell) {
        statusCell.className = `badge ${statusClass}`;
        statusCell.innerHTML = `<i class="fas fa-${employee.status === 'Active' ? 'check' : 'times'}-circle"></i> ${employee.status}`;
    }
    
    // Update row class
    row.className = employee.status === 'Active' ? 'active' : 'inactive';
    
    // Update avatar image
    const avatarImg = row.querySelector('.employee-avatar');
    if (avatarImg) {
        avatarImg.src = employee.avatar_url;
        avatarImg.alt = employee.name;
    }
}

// Send message to employee (placeholder)
function sendMessage(employeeId) {
    alert(`Send message to employee ${employeeId}`);
}

// Show add employee modal
function showAddEmployeeModal() {
    const modal = document.getElementById('addEmployeeModal');
    modal.classList.add('active');
    
    // Clear form and errors
    if (document.getElementById('addEmployeeForm')) {
        document.getElementById('addEmployeeForm').reset();
        clearErrors();
        updateAvatarPreview();
        updateCharCount();
        checkPasswordStrength('');
    }
}

// Close all modals
function closeModal() {
    document.querySelectorAll('.modal').forEach(modal => {
        modal.classList.remove('active');
    });
}

// Export data to CSV
function exportData() {
    // Create CSV data
    const rows = document.querySelectorAll('#employee-table-body tr:not([style*="display: none"])');
    let csvContent = "data:text/csv;charset=utf-8,";
    
    // Add headers
    const headers = ["Name", "Username", "Email", "Phone", "Department", "Role", "Status", "Joined Date"];
    csvContent += headers.join(",") + "\n";
    
    // Add data rows
    rows.forEach(row => {
        if (row.style.display !== 'none') {
            const cells = row.querySelectorAll('td');
            const name = cells[0].querySelector('.employee-name').textContent.trim();
            const username = cells[0].querySelector('.employee-username').textContent.trim().replace('@', '');
            const email = cells[0].querySelector('.fa-envelope').parentNode.textContent.trim();
            const phone = cells[1].querySelector('.fa-phone').parentNode.textContent.trim();
            const department = cells[2].querySelector('.badge-primary, .badge-warning')?.textContent.trim() || '';
            const role = cells[3].querySelector('.role-badge').textContent.trim();
            const status = cells[4].querySelector('.badge-success, .badge-danger')?.textContent.trim() || '';
            const joined = cells[5].querySelector('div:first-child').textContent.trim();
            
            const rowData = [name, username, email, phone, department, role, status, joined]
                .map(cell => `"${cell.replace(/"/g, '""')}"`)
                .join(",");
            csvContent += rowData + "\n";
        }
    });
    
    // Create download link
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "employees_export.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Toggle view (placeholder)
function toggleView() {
    alert('Grid view will be implemented in the next update');
}

// Refresh data
function refreshData() {
    window.location.reload();
}

// Add employee to table (for immediate UI update)
function addEmployeeToTable(employee) {
    const tableBody = document.getElementById('employee-table-body');
    
    if (!tableBody) return;
    
    const newRow = document.createElement('tr');
    newRow.className = employee.status === 'Active' ? 'active' : 'inactive';
    newRow.setAttribute('data-employee-id', employee.id);
    
    newRow.innerHTML = `
        <td>
            <div class="employee-info">
                <img 
                    class="employee-avatar"
                    src="${employee.avatar_url}"
                    alt="${employee.name}"
                    onerror="this.src='https://ui-avatars.com/api/?name=User&background=4361ee&color=fff&size=45'"
                />
                <div class="employee-details">
                    <div class="employee-name">${employee.name}</div>
                    <div class="employee-username">@${employee.username}</div>
                    <div style="font-size: 0.8rem; color: var(--gray);">
                        <i class="fas fa-envelope"></i> ${employee.email}
                    </div>
                </div>
            </div>
        </td>
        <td>
            <div style="font-weight: 500;">
                <i class="fas fa-phone"></i> ${employee.phone}
            </div>
        </td>
        <td>
            <span class="badge badge-primary">
                <i class="fas fa-building"></i> ${employee.department}
            </span>
        </td>
        <td>
            <span class="role-badge role-${employee.role.toLowerCase()}">
                <i class="fas fa-user-tag"></i> ${employee.role}
            </span>
        </td>
        <td>
            <span class="badge badge-${employee.status === 'Active' ? 'success' : 'danger'}">
                <i class="fas fa-${employee.status === 'Active' ? 'check' : 'times'}-circle"></i> ${employee.status}
            </span>
        </td>
        <td>
            <div style="font-weight: 500;">${employee.created_at}</div>
            <div style="font-size: 0.85rem; color: var(--gray);">
                just now
            </div>
        </td>
        <td>
            <div class="action-buttons">
                <button class="btn btn-primary btn-xs btn-icon" onclick="viewEmployee('${employee.id}')" title="View">
                    <i class="fas fa-eye"></i>
                </button>
                <button class="btn btn-outline btn-xs btn-icon" onclick="editEmployee('${employee.id}')" title="Edit">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-outline btn-xs btn-icon" onclick="sendMessage('${employee.id}')" title="Message">
                    <i class="fas fa-envelope"></i>
                </button>
                <button class="btn btn-outline btn-xs btn-icon" onclick="toggleEmployeeStatus('${employee.id}', 'deactivate')" title="Deactivate">
                    <i class="fas fa-user-slash"></i>
                </button>
                <button class="btn btn-outline btn-xs btn-icon" onclick="deleteEmployee('${employee.id}')" title="Delete" style="color: var(--danger); border-color: var(--danger);">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </td>
    `;
    
    // Add to the beginning of the table
    if (tableBody.firstChild) {
        tableBody.insertBefore(newRow, tableBody.firstChild);
    } else {
        tableBody.appendChild(newRow);
    }
}

// Handle add employee form submission
document.getElementById('addEmployeeForm')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const form = e.target;
    const submitBtn = document.getElementById('submitEmployeeBtn');
    const btnText = submitBtn?.querySelector('.btn-text');
    const loader = submitBtn?.querySelector('.loader');
    
    // Show loading state
    if (btnText) btnText.style.display = 'none';
    if (loader) loader.style.display = 'block';
    if (submitBtn) submitBtn.disabled = true;
    
    try {
        const formData = new FormData(form);
        
        const response = await fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            // Success - close modal and show success message
            closeModal();
            
            // Show success message
            showNotification('success', data.message || 'Employee added successfully!');
            
            // Add the new employee to the table
            if (data.employee) {
                addEmployeeToTable(data.employee);
            }
            
            // Refresh the page after 2 seconds to show updated stats
            setTimeout(() => {
                window.location.reload();
            }, 2000);
            
        } else {
            // Show errors
            showErrors(data.errors || {});
            showNotification('error', 'Please correct the errors below.');
        }
        
    } catch (error) {
        console.error('Error:', error);
        showNotification('error', 'An error occurred. Please try again.');
    } finally {
        // Reset button state
        if (btnText) btnText.style.display = 'inline';
        if (loader) loader.style.display = 'none';
        if (submitBtn) submitBtn.disabled = false;
    }
});

// Handle edit form submission
document.getElementById('editEmployeeForm')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const form = e.target;
    const submitBtn = document.getElementById('submitEditEmployeeBtn');
    const btnText = submitBtn?.querySelector('.btn-text');
    const loader = submitBtn?.querySelector('.loader');
    const employeeId = document.getElementById('edit_employee_id').value;
    
    // Show loading state
    if (btnText) btnText.style.display = 'none';
    if (loader) loader.style.display = 'block';
    if (submitBtn) submitBtn.disabled = true;
    
    try {
        const formData = new FormData(form);
        
        const response = await fetch(`/edit-employee/${employeeId}/`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            // Success - close modal and show success message
            closeModal();
            showNotification('success', data.message || 'Employee updated successfully!');
            
            // Update the row in the table
            updateEmployeeInTable(data.employee);
            
        } else {
            // Show errors
            showErrors(data.errors || {});
            showNotification('error', 'Please correct the errors below.');
        }
        
    } catch (error) {
        console.error('Error:', error);
        showNotification('error', 'An error occurred. Please try again.');
    } finally {
        // Reset button state
        if (btnText) btnText.style.display = 'inline';
        if (loader) loader.style.display = 'none';
        if (submitBtn) submitBtn.disabled = false;
    }
});

// Close modal when clicking outside
document.querySelectorAll('.modal').forEach(modal => {
    modal.addEventListener('click', function(e) {
        if (e.target === this) {
            closeModal();
        }
    });
});

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl + F for search
    if (e.ctrlKey && e.key === 'f') {
        e.preventDefault();
        const searchInput = document.getElementById('live-search') || document.getElementById('search');
        if (searchInput) searchInput.focus();
    }
    // Escape to close modals
    if (e.key === 'Escape') {
        closeModal();
    }
});

// Smooth scroll to top button
const scrollToTopBtn = document.createElement('button');
scrollToTopBtn.innerHTML = '<i class="fas fa-arrow-up"></i>';
scrollToTopBtn.style.cssText = `
    position: fixed;
    bottom: 30px;
    right: 30px;
    width: 50px;
    height: 50px;
    border-radius: 50%;
    background: var(--primary);
    color: white;
    border: none;
    cursor: pointer;
    box-shadow: var(--shadow-lg);
    display: none;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
    z-index: 100;
    transition: all 0.3s;
`;

scrollToTopBtn.onmouseover = () => scrollToTopBtn.style.transform = 'translateY(-3px)';
scrollToTopBtn.onmouseout = () => scrollToTopBtn.style.transform = 'translateY(0)';
scrollToTopBtn.onclick = () => window.scrollTo({ top: 0, behavior: 'smooth' });

document.body.appendChild(scrollToTopBtn);

window.addEventListener('scroll', () => {
    scrollToTopBtn.style.display = window.scrollY > 300 ? 'flex' : 'none';
});

// Add keyframe animations for notifications
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
`;
document.head.appendChild(style);

// Add event listeners for real-time updates
document.addEventListener('DOMContentLoaded', function() {
    // Update avatar when name changes in add form
    ['id_first_name', 'id_last_name'].forEach(id => {
        const field = document.getElementById(id);
        if (field) {
            field.addEventListener('input', updateAvatarPreview);
        }
    });
    
    // Update avatar when name changes in edit form
    ['edit_first_name', 'edit_last_name'].forEach(id => {
        const field = document.getElementById(id);
        if (field) {
            field.addEventListener('input', updateEditAvatarPreview);
        }
    });
    
    // Update character count for address in add form
    const addressField = document.getElementById('id_address');
    if (addressField) {
        addressField.addEventListener('input', updateCharCount);
        updateCharCount(); // Initial count
    }
    
    // Update character count for address in edit form
    const editAddressField = document.getElementById('edit_address');
    if (editAddressField) {
        editAddressField.addEventListener('input', updateEditCharCount);
        updateEditCharCount(); // Initial count
    }
    
    // Password strength checker
    const passwordField = document.getElementById('id_password1');
    if (passwordField) {
        passwordField.addEventListener('input', function() {
            checkPasswordStrength(this.value);
        });
    }
    
    // Phone number validation for add form
    const phoneField = document.getElementById('id_phone_number');
    if (phoneField) {
        phoneField.addEventListener('input', function() {
            // Remove non-numeric characters
            this.value = this.value.replace(/\D/g, '');
            
            // Show warning if not within range
            if (this.value.length < 10 || this.value.length > 15) {
                this.classList.add('is-invalid');
            } else {
                this.classList.remove('is-invalid');
            }
        });
    }
    
    // Phone number validation for edit form
    const editPhoneField = document.getElementById('edit_phone_number');
    if (editPhoneField) {
        editPhoneField.addEventListener('input', function() {
            // Remove non-numeric characters
            this.value = this.value.replace(/\D/g, '');
            
            // Show warning if not within range
            if (this.value.length < 10 || this.value.length > 15) {
                this.classList.add('is-invalid');
            } else {
                this.classList.remove('is-invalid');
            }
        });
    }
});