// Progress Tracker - Interactive Features
document.addEventListener('DOMContentLoaded', function() {
    
    // Form Enhancement
    enhanceForms();
    
    // Progressive Disclosure
    setupToggleSections();
    
    // Auto-save for forms
    setupAutoSave();
    
    // Status updates with animation
    animateStatusChanges();
    
    // Mobile optimizations
    setupMobileOptimizations();
    
});

// Enhanced Form Experience
function enhanceForms() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        // Add loading state on submit
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.classList.add('loading');
                submitBtn.disabled = true;
                
                // Add spinner
                const originalText = submitBtn.textContent;
                submitBtn.innerHTML = `
                    <span class="spinner"></span>
                    ${originalText}
                `;
            }
        });
        
        // Smart form validation
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', validateField);
            input.addEventListener('input', clearErrors);
        });
    });
}

// Progressive Disclosure for Optional Sections
function setupToggleSections() {
    const optionalSections = document.querySelectorAll('.form-section.optional');
    
    optionalSections.forEach(section => {
        const title = section.querySelector('.form-section-title');
        const content = section.querySelector('.collapsible-content') || createCollapsibleWrapper(section);
        
        // Create toggle functionality
        title.classList.add('toggle-section');
        title.innerHTML = `
            <span class="toggle-icon">▶</span>
            ${title.textContent}
            <span class="optional-badge">Optional</span>
        `;
        
        // Initially hide optional sections
        content.style.maxHeight = '0';
        content.style.overflow = 'hidden';
        
        title.addEventListener('click', () => {
            const isExpanded = title.classList.contains('expanded');
            
            if (isExpanded) {
                title.classList.remove('expanded');
                content.style.maxHeight = '0';
            } else {
                title.classList.add('expanded');
                content.style.maxHeight = content.scrollHeight + 'px';
            }
        });
    });
}

function createCollapsibleWrapper(section) {
    const content = document.createElement('div');
    content.className = 'collapsible-content';
    
    // Move all children except title to wrapper
    const title = section.querySelector('.form-section-title');
    while (section.children.length > 1) {
        if (section.children[1] !== title) {
            content.appendChild(section.children[1]);
        } else {
            break;
        }
    }
    
    section.appendChild(content);
    return content;
}

// Auto-save Draft Functionality
function setupAutoSave() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        const formId = form.action || 'default-form';
        const inputs = form.querySelectorAll('input, select, textarea');
        
        // Load saved data
        loadFormData(form, formId);
        
        // Save on input
        inputs.forEach(input => {
            input.addEventListener('input', debounce(() => {
                saveFormData(form, formId);
                showAutoSaveIndicator();
            }, 500));
        });
        
        // Clear saved data on successful submit
        form.addEventListener('submit', () => {
            setTimeout(() => {
                clearFormData(formId);
            }, 1000);
        });
    });
}

// Form Validation
function validateField(e) {
    const field = e.target;
    const value = field.value.trim();
    const isRequired = field.hasAttribute('required');
    
    clearFieldError(field);
    
    if (isRequired && !value) {
        showFieldError(field, 'This field is required');
        return false;
    }
    
    // Specific validations
    if (field.type === 'email' && value && !isValidEmail(value)) {
        showFieldError(field, 'Please enter a valid email');
        return false;
    }
    
    if (field.type === 'number' && value) {
        const min = field.getAttribute('min');
        const max = field.getAttribute('max');
        const numValue = parseFloat(value);
        
        if (min && numValue < parseFloat(min)) {
            showFieldError(field, `Minimum value is ${min}`);
            return false;
        }
        
        if (max && numValue > parseFloat(max)) {
            showFieldError(field, `Maximum value is ${max}`);
            return false;
        }
    }
    
    return true;
}

function showFieldError(field, message) {
    const formGroup = field.closest('.form-group');
    
    // Remove existing error
    const existingError = formGroup.querySelector('.field-error');
    if (existingError) existingError.remove();
    
    // Add error styling
    field.style.borderColor = 'var(--error)';
    
    // Add error message
    const errorDiv = document.createElement('div');
    errorDiv.className = 'field-error';
    errorDiv.style.color = 'var(--error)';
    errorDiv.style.fontSize = 'var(--font-sm)';
    errorDiv.style.marginTop = 'var(--spacing-xs)';
    errorDiv.textContent = message;
    
    formGroup.appendChild(errorDiv);
}

function clearFieldError(field) {
    const formGroup = field.closest('.form-group');
    const error = formGroup.querySelector('.field-error');
    if (error) error.remove();
    
    field.style.borderColor = '';
}

function clearErrors(e) {
    clearFieldError(e.target);
}

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

function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

// Auto-save Helper Functions
function saveFormData(form, formId) {
    const data = {};
    const inputs = form.querySelectorAll('input, select, textarea');
    
    inputs.forEach(input => {
        if (input.name && input.value) {
            data[input.name] = input.value;
        }
    });
    
    localStorage.setItem(`form-draft-${formId}`, JSON.stringify(data));
}

function loadFormData(form, formId) {
    const savedData = localStorage.getItem(`form-draft-${formId}`);
    if (!savedData) return;
    
    try {
        const data = JSON.parse(savedData);
        const inputs = form.querySelectorAll('input, select, textarea');
        
        inputs.forEach(input => {
            if (input.name && data[input.name]) {
                input.value = data[input.name];
            }
        });
        
        showDraftRestoreMessage();
    } catch (e) {
        console.warn('Failed to restore form data:', e);
    }
}

function clearFormData(formId) {
    localStorage.removeItem(`form-draft-${formId}`);
}

function showAutoSaveIndicator() {
    let indicator = document.getElementById('autosave-indicator');
    if (!indicator) {
        indicator = document.createElement('div');
        indicator.id = 'autosave-indicator';
        indicator.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--success);
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 12px;
            z-index: 1000;
            opacity: 0;
            transition: opacity 0.3s ease;
        `;
        indicator.textContent = '✓ Draft saved';
        document.body.appendChild(indicator);
    }
    
    indicator.style.opacity = '1';
    setTimeout(() => {
        indicator.style.opacity = '0';
    }, 2000);
}

function showDraftRestoreMessage() {
    const alert = document.createElement('div');
    alert.className = 'alert alert-info';
    alert.innerHTML = `
        <span>📝</span>
        <span>Your previous draft has been restored.</span>
        <button onclick="this.parentElement.remove()" style="margin-left: auto; background: none; border: none; cursor: pointer;">×</button>
    `;
    
    const firstCard = document.querySelector('.card');
    if (firstCard) {
        firstCard.parentNode.insertBefore(alert, firstCard);
    }
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        if (alert.parentNode) alert.remove();
    }, 5000);
}

// Animate Status Changes
function animateStatusChanges() {
    const statusBadges = document.querySelectorAll('.status-badge');
    
    statusBadges.forEach((badge, index) => {
        badge.style.animation = `fadeInUp 0.6s ease forwards ${index * 0.1}s`;
        badge.style.opacity = '0';
    });
    
    // Add CSS animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
    `;
    document.head.appendChild(style);
}

// Mobile Optimizations
function setupMobileOptimizations() {
    // Add touch-friendly interactions
    if ('ontouchstart' in window) {
        document.body.classList.add('touch-device');
        
        // Improve button touch targets
        const style = document.createElement('style');
        style.textContent = `
            .touch-device .btn {
                min-height: 44px;
                min-width: 44px;
            }
            
            .touch-device .entry-card {
                padding: var(--spacing-xl);
            }
            
            .touch-device .nav-item {
                padding: var(--spacing-xl);
            }
        `;
        document.head.appendChild(style);
    }
    
    // Handle viewport changes
    function handleViewportChange() {
        const vh = window.innerHeight * 0.01;
        document.documentElement.style.setProperty('--vh', `${vh}px`);
    }
    
    window.addEventListener('resize', handleViewportChange);
    handleViewportChange();
}

// Quick Actions for Better UX
function setupQuickActions() {
    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        if (e.ctrlKey || e.metaKey) {
            switch(e.key) {
                case 'k':
                    e.preventDefault();
                    focusSearch();
                    break;
                case 's':
                    e.preventDefault();
                    const activeForm = document.querySelector('form:focus-within');
                    if (activeForm) {
                        activeForm.requestSubmit();
                    }
                    break;
            }
        }
        
        if (e.key === 'Escape') {
            closeModals();
        }
    });
}

function focusSearch() {
    const searchInput = document.querySelector('input[type="search"], input[placeholder*="search" i]');
    if (searchInput) {
        searchInput.focus();
        searchInput.select();
    }
}

function closeModals() {
    const modals = document.querySelectorAll('.modal, .overlay');
    modals.forEach(modal => modal.remove());
}

// Initialize quick actions
setupQuickActions();