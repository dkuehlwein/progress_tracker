/**
 * Shared table filtering, sorting, and filter chip management.
 * Used by reading.html, drawing.html, and fitness.html.
 *
 * Usage:
 *   const table = new FilterableTable({
 *     filters: [
 *       { id: 'userFilter', dataAttr: 'userId', label: 'User', type: 'select' },
 *       { id: 'statusFilter', dataAttr: 'status', label: 'Status', type: 'select' },
 *       { id: 'searchFilter', dataAttr: 'search', label: 'Search', type: 'search' },
 *     ],
 *     tableBodyId: 'entriesTableBody',
 *     counterId: 'entryCount',
 *     activeFiltersId: 'activeFilters',
 *     filterChipsId: 'filterChips',
 *     clearButtonId: 'clearFilters',
 *     sortConfig: {
 *       dateColumns: [6, 7],
 *       numericColumns: [5],
 *     },
 *   });
 */

class FilterableTable {
    constructor(config) {
        this.config = config;
        this.currentSort = { column: -1, direction: 'asc' };
        this.activeFilters = {};

        this._bindFilters();
        this._bindRowExpansion();
        this.filter();
    }

    /* ── Filtering ─────────────────────────────────────────── */

    filter() {
        const filterValues = {};
        this.config.filters.forEach(f => {
            const el = document.getElementById(f.id);
            if (!el) return;
            filterValues[f.id] = f.type === 'search' ? el.value.toLowerCase() : el.value;
        });
        this.activeFilters = filterValues;

        const tbody = document.getElementById(this.config.tableBodyId);
        if (!tbody) return;

        const rows = tbody.querySelectorAll('tr:not(.details-row)');
        let visible = 0;

        rows.forEach(row => {
            let show = true;
            this.config.filters.forEach(f => {
                const val = filterValues[f.id];
                if (!val) return;
                if (f.type === 'search') {
                    if (!row.dataset[f.dataAttr].includes(val)) show = false;
                } else {
                    if (row.dataset[f.dataAttr] !== val) show = false;
                }
            });

            row.style.display = show ? '' : 'none';
            if (show) visible++;

            if (!show) {
                const detailsRow = this._getDetailsRow(row);
                if (detailsRow) detailsRow.style.display = 'none';
            }
        });

        const counter = document.getElementById(this.config.counterId);
        if (counter) counter.textContent = visible;

        this._updateNoResultsMessage(tbody, visible);
        this._updateFilterChips();
    }

    /* ── Sorting ───────────────────────────────────────────── */

    sort(columnIndex) {
        const tbody = document.getElementById(this.config.tableBodyId);
        if (!tbody) return;

        const rows = Array.from(tbody.querySelectorAll('tr:not(.details-row)'));
        const headers = document.querySelectorAll('.data-table th.sortable');
        const sc = this.config.sortConfig || {};

        if (this.currentSort.column === columnIndex) {
            this.currentSort.direction = this.currentSort.direction === 'asc' ? 'desc' : 'asc';
        } else {
            this.currentSort.column = columnIndex;
            this.currentSort.direction = 'asc';
        }

        headers.forEach((h, i) => {
            h.classList.remove('sort-asc', 'sort-desc');
            if (i === columnIndex) {
                h.classList.add(this.currentSort.direction === 'asc' ? 'sort-asc' : 'sort-desc');
            }
        });

        const isDate = (sc.dateColumns || []).includes(columnIndex);
        const isNumeric = (sc.numericColumns || []).includes(columnIndex);

        rows.sort((a, b) => {
            let aVal = a.children[columnIndex]?.textContent.trim() ?? '';
            let bVal = b.children[columnIndex]?.textContent.trim() ?? '';

            if (isDate) {
                const aMatch = aVal.match(/\d{4}-\d{2}-\d{2}/);
                const bMatch = bVal.match(/\d{4}-\d{2}-\d{2}/);
                aVal = aMatch ? new Date(aMatch[0]) : new Date(0);
                bVal = bMatch ? new Date(bMatch[0]) : new Date(0);
            } else if (isNumeric) {
                aVal = parseFloat(aVal) || 0;
                bVal = parseFloat(bVal) || 0;
            } else {
                aVal = aVal.toLowerCase();
                bVal = bVal.toLowerCase();
            }

            if (aVal < bVal) return this.currentSort.direction === 'asc' ? -1 : 1;
            if (aVal > bVal) return this.currentSort.direction === 'asc' ? 1 : -1;
            return 0;
        });

        rows.forEach(row => {
            tbody.appendChild(row);
            const details = this._getDetailsRow(row);
            if (details) tbody.appendChild(details);
        });
    }

    /* ── Clear all ─────────────────────────────────────────── */

    clearAll() {
        this.config.filters.forEach(f => {
            const el = document.getElementById(f.id);
            if (el) el.value = '';
        });
        this.filter();
    }

    /* ── Private helpers ───────────────────────────────────── */

    _bindFilters() {
        this.config.filters.forEach(f => {
            const el = document.getElementById(f.id);
            if (!el) return;
            const event = f.type === 'search' ? 'input' : 'change';
            el.addEventListener(event, () => this.filter());
        });
    }

    _bindRowExpansion() {
        const tbody = document.getElementById(this.config.tableBodyId);
        if (!tbody) return;

        tbody.querySelectorAll('tr:not(.details-row)').forEach(row => {
            row.classList.add('expandable');
            row.addEventListener('click', (e) => {
                const tag = e.target.tagName;
                if (tag === 'BUTTON' || tag === 'A' || tag === 'IMG' || e.target.closest('a') || e.target.closest('form')) return;

                const details = this._getDetailsRow(row);
                if (details) {
                    const isVisible = details.style.display !== 'none';
                    details.style.display = isVisible ? 'none' : '';
                    row.classList.toggle('expanded', !isVisible);
                }
            });
        });
    }

    _getDetailsRow(row) {
        const form = row.querySelector('form');
        if (!form) return null;
        const id = form.action.split('/').pop();
        return document.getElementById('details-' + id);
    }

    _updateNoResultsMessage(tbody, visibleCount) {
        let msg = tbody.closest('.table-responsive')?.parentElement?.querySelector('.no-filter-results');
        if (visibleCount === 0) {
            if (!msg) {
                msg = document.createElement('div');
                msg.className = 'no-filter-results';
                msg.setAttribute('role', 'status');
                msg.innerHTML = '<p>No entries match your current filters.</p><button class="btn btn-outline btn-sm" type="button">Clear Filters</button>';
                msg.querySelector('button').addEventListener('click', () => this.clearAll());
                tbody.closest('.table-responsive')?.insertAdjacentElement('afterend', msg);
            }
            msg.style.display = '';
        } else if (msg) {
            msg.style.display = 'none';
        }
    }

    _updateFilterChips() {
        const container = document.getElementById(this.config.activeFiltersId);
        const chips = document.getElementById(this.config.filterChipsId);
        const clearBtn = document.getElementById(this.config.clearButtonId);
        if (!container || !chips) return;

        chips.innerHTML = '';
        let hasActive = false;

        this.config.filters.forEach(f => {
            const val = this.activeFilters[f.id];
            if (!val) return;
            hasActive = true;

            let displayValue = val;
            if (f.type === 'select') {
                const el = document.getElementById(f.id);
                displayValue = el.options[el.selectedIndex]?.text || val;
            } else {
                displayValue = `"${val}"`;
            }

            const chip = document.createElement('div');
            chip.className = 'filter-chip';
            chip.innerHTML = `
                <span>${f.label}: ${this._escapeHtml(displayValue)}</span>
                <button class="filter-chip-remove" type="button" aria-label="Remove ${f.label} filter">&times;</button>
            `;
            chip.querySelector('button').addEventListener('click', (e) => {
                e.stopPropagation();
                document.getElementById(f.id).value = '';
                this.filter();
            });
            chips.appendChild(chip);
        });

        container.classList.toggle('has-filters', hasActive);
        if (clearBtn) clearBtn.style.display = hasActive ? 'inline-flex' : 'none';
    }

    _escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }
}

/* ── Image modal (shared by drawing & index pages) ─────── */

function openImageModal(src, alt) {
    const modal = document.getElementById('imageModal');
    const img = document.getElementById('modalImage');
    if (!modal || !img) return;
    img.src = src;
    img.alt = alt || 'Full size image';
    modal.style.display = 'flex';
    modal.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';

    // Trap focus
    modal.focus();
}

function closeImageModal() {
    const modal = document.getElementById('imageModal');
    if (!modal) return;
    modal.style.display = 'none';
    modal.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
}

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeImageModal();
});
