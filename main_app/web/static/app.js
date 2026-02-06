/* ═══════════════════════════════════════════════════════════
   Progress Tracker – Core Interactive Features
   ═══════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {
    enhanceForms();
    setupToggleSections();
    setupAutoSave();
    setupMobileOptimizations();
    setupKeyboardShortcuts();
    setupThemeToggle();
});

/* ── Theme toggle ──────────────────────────────────────────── */

function setupThemeToggle() {
    const btn = document.getElementById('themeToggle');
    if (!btn) return;

    const saved = localStorage.getItem('theme');
    if (saved) {
        document.documentElement.setAttribute('data-theme', saved);
    }
    updateThemeIcon(btn);

    btn.addEventListener('click', () => {
        const current = document.documentElement.getAttribute('data-theme');
        const isDark = current === 'dark' ||
            (!current && window.matchMedia('(prefers-color-scheme: dark)').matches);
        const next = isDark ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        localStorage.setItem('theme', next);
        updateThemeIcon(btn);
    });
}

function updateThemeIcon(btn) {
    const theme = document.documentElement.getAttribute('data-theme');
    const isDark = theme === 'dark' ||
        (!theme && window.matchMedia('(prefers-color-scheme: dark)').matches);
    btn.textContent = isDark ? '\u2600\ufe0f' : '\ud83c\udf19';
    btn.setAttribute('aria-label', isDark ? 'Switch to light mode' : 'Switch to dark mode');
}

/* ── Form enhancement ──────────────────────────────────────── */

function enhanceForms() {
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', () => {
            const btn = form.querySelector('button[type="submit"]');
            if (btn && !btn.disabled) {
                btn.classList.add('loading');
                btn.disabled = true;
                const text = btn.textContent;
                btn.innerHTML = '<span class="spinner"></span> ' + text;
            }
        });

        form.querySelectorAll('input, select, textarea').forEach(input => {
            input.addEventListener('blur', validateField);
            input.addEventListener('input', (e) => clearFieldError(e.target));
        });
    });
}

/* ── Validation ────────────────────────────────────────────── */

function validateField(e) {
    const field = e.target;
    const value = field.value.trim();

    clearFieldError(field);

    if (field.hasAttribute('required') && !value) {
        showFieldError(field, 'This field is required');
        return false;
    }

    if (field.type === 'email' && value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
        showFieldError(field, 'Please enter a valid email');
        return false;
    }

    if (field.type === 'number' && value) {
        const num = parseFloat(value);
        const min = field.getAttribute('min');
        const max = field.getAttribute('max');
        if (min !== null && num < parseFloat(min)) {
            showFieldError(field, 'Minimum value is ' + min);
            return false;
        }
        if (max !== null && num > parseFloat(max)) {
            showFieldError(field, 'Maximum value is ' + max);
            return false;
        }
    }

    return true;
}

function showFieldError(field, message) {
    const group = field.closest('.form-group');
    if (!group) return;

    const existing = group.querySelector('.field-error');
    if (existing) existing.remove();

    field.classList.add('field-invalid');
    field.setAttribute('aria-invalid', 'true');

    const err = document.createElement('div');
    err.className = 'field-error';
    err.setAttribute('role', 'alert');
    err.textContent = message;
    group.appendChild(err);
}

function clearFieldError(field) {
    const group = field.closest('.form-group');
    if (!group) return;

    const err = group.querySelector('.field-error');
    if (err) err.remove();

    field.classList.remove('field-invalid');
    field.removeAttribute('aria-invalid');
}

/* ── Progressive disclosure ────────────────────────────────── */

function setupToggleSections() {
    document.querySelectorAll('.form-section.optional').forEach(section => {
        const title = section.querySelector('.form-section-title');
        if (!title) return;

        const content = section.querySelector('.collapsible-content') || wrapContent(section);

        title.classList.add('toggle-section');
        title.setAttribute('role', 'button');
        title.setAttribute('aria-expanded', 'false');
        title.setAttribute('tabindex', '0');

        // Only add toggle elements if they're not already there
        if (!title.querySelector('.toggle-icon')) {
            const text = title.textContent;
            title.innerHTML = '<span class="toggle-icon" aria-hidden="true">\u25b6</span> ' + text;
            if (!title.querySelector('.optional-badge')) {
                title.insertAdjacentHTML('beforeend', ' <span class="optional-badge">Optional</span>');
            }
        }

        content.style.maxHeight = '0';
        content.style.overflow = 'hidden';

        const toggle = () => {
            const expanded = title.classList.toggle('expanded');
            title.setAttribute('aria-expanded', String(expanded));
            content.style.maxHeight = expanded ? content.scrollHeight + 'px' : '0';
        };

        title.addEventListener('click', toggle);
        title.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(); }
        });
    });
}

function wrapContent(section) {
    const wrapper = document.createElement('div');
    wrapper.className = 'collapsible-content';
    const title = section.querySelector('.form-section-title');
    while (section.children.length > 1) {
        if (section.children[1] !== title) {
            wrapper.appendChild(section.children[1]);
        } else break;
    }
    section.appendChild(wrapper);
    return wrapper;
}

/* ── Auto-save drafts ──────────────────────────────────────── */

function setupAutoSave() {
    document.querySelectorAll('form').forEach(form => {
        const key = 'draft-' + (form.action || location.pathname);
        const inputs = form.querySelectorAll('input, select, textarea');

        restoreDraft(form, key);

        inputs.forEach(input => {
            input.addEventListener('input', debounce(() => {
                saveDraft(form, key);
                showToast('Draft saved', 'success');
            }, 500));
        });

        form.addEventListener('submit', () => {
            try { localStorage.removeItem(key); } catch (_) { /* quota */ }
        });
    });
}

function saveDraft(form, key) {
    try {
        const data = {};
        form.querySelectorAll('input, select, textarea').forEach(el => {
            if (el.name && el.value && el.type !== 'file') data[el.name] = el.value;
        });
        localStorage.setItem(key, JSON.stringify(data));
    } catch (_) { /* quota exceeded – silently ignore */ }
}

function restoreDraft(form, key) {
    try {
        const raw = localStorage.getItem(key);
        if (!raw) return;
        const data = JSON.parse(raw);
        let restored = false;
        form.querySelectorAll('input, select, textarea').forEach(el => {
            if (el.name && data[el.name] && el.type !== 'file') {
                el.value = data[el.name];
                restored = true;
            }
        });
        if (restored) {
            showAlert(form, 'Your previous draft has been restored.', 'info');
        }
    } catch (_) { /* corrupt data – ignore */ }
}

/* ── Toast notifications ───────────────────────────────────── */

function showToast(message, type) {
    let toast = document.getElementById('app-toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'app-toast';
        toast.className = 'toast toast-' + (type || 'success');
        toast.setAttribute('role', 'status');
        toast.setAttribute('aria-live', 'polite');
        document.body.appendChild(toast);
    }
    toast.textContent = '\u2713 ' + message;
    toast.classList.add('visible');
    clearTimeout(toast._timer);
    toast._timer = setTimeout(() => toast.classList.remove('visible'), 2000);
}

function showAlert(form, message, type) {
    const alert = document.createElement('div');
    alert.className = 'alert alert-' + type;
    alert.setAttribute('role', 'status');
    alert.innerHTML = '<span aria-hidden="true">\ud83d\udcdd</span> <span>' + message + '</span>' +
        '<button type="button" onclick="this.parentElement.remove()" aria-label="Dismiss" ' +
        'style="margin-left:auto;background:none;border:none;cursor:pointer;font-size:1.2rem;">\u00d7</button>';
    form.insertBefore(alert, form.firstChild);
    setTimeout(() => { if (alert.parentNode) alert.remove(); }, 5000);
}

/* ── Mobile ────────────────────────────────────────────────── */

function setupMobileOptimizations() {
    if ('ontouchstart' in window) {
        document.body.classList.add('touch-device');
    }
    const setVh = () => document.documentElement.style.setProperty('--vh', window.innerHeight * 0.01 + 'px');
    window.addEventListener('resize', setVh);
    setVh();
}

/* ── Keyboard shortcuts ────────────────────────────────────── */

function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey || e.metaKey) {
            if (e.key === 'k') {
                e.preventDefault();
                const search = document.querySelector('input[type="search"], input[placeholder*="search" i], #searchFilter');
                if (search) { search.focus(); search.select(); }
            }
            if (e.key === 's') {
                e.preventDefault();
                const form = document.querySelector('form:focus-within');
                if (form) form.requestSubmit();
            }
        }
        if (e.key === 'Escape') {
            closeImageModal?.();
        }
    });
}

/* ── Utilities ─────────────────────────────────────────────── */

function debounce(fn, ms) {
    let t;
    return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
}
