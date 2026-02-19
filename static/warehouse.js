/**
 * Warehouse Database Interface
 * Interactive filtering and search for warehouse inventory
 */

class WarehouseApp {
    constructor() {
        this.allItems = [];
        this.filteredItems = [];
        this.currentPage = 1;
        this.itemsPerPage = 50;
        this.sortColumn = null;
        this.sortDirection = 'asc';

        this.initializeElements();
        this.attachEventListeners();
        this.loadDatabases();
    }

    initializeElements() {
        // Form elements
        this.dbSelect = document.getElementById('database');
        this.gradeInput = document.getElementById('grade');
        this.typeRadios = document.querySelectorAll('input[name="type"]');

        // Block inputs
        this.blockX = document.getElementById('block-x');
        this.blockY = document.getElementById('block-y');
        this.blockZ = document.getElementById('block-z');

        // Circle inputs
        this.diameter = document.getElementById('diameter');
        this.circleTolerance = document.getElementById('circle-tolerance');

        // Sheet inputs
        this.sheetX = document.getElementById('sheet-x');
        this.sheetY = document.getElementById('sheet-y');
        this.sheetZ = document.getElementById('sheet-z');
        this.sheetTolerance = document.getElementById('sheet-tolerance');

        // Strip inputs
        this.stripX = document.getElementById('strip-x');
        this.stripY = document.getElementById('strip-y');
        this.stripZ = document.getElementById('strip-z');
        this.stripTolerance = document.getElementById('strip-tolerance');

        // Containers
        this.blockFilters = document.getElementById('block-filters');
        this.circleFilters = document.getElementById('circle-filters');
        this.sheetFilters = document.getElementById('sheet-filters');
        this.stripFilters = document.getElementById('strip-filters');
        this.tableBody = document.getElementById('table-body');
        this.statsText = document.getElementById('stats-text');
        this.pageInfo = document.getElementById('page-info');

        // Buttons
        this.btnSearch = document.getElementById('btn-search');
        this.btnReset = document.getElementById('btn-reset');
        this.btnPrev = document.getElementById('btn-prev');
        this.btnNext = document.getElementById('btn-next');
    }

    attachEventListeners() {
        // Database selection
        this.dbSelect.addEventListener('change', () => this.loadStocks());

        // Type radio buttons
        this.typeRadios.forEach(radio => {
            radio.addEventListener('change', () => this.toggleFilterInputs());
        });

        // Search button
        this.btnSearch.addEventListener('click', () => this.performSearch());

        // Reset button
        this.btnReset.addEventListener('click', () => this.resetFilters());

        // Pagination
        this.btnPrev.addEventListener('click', () => this.previousPage());
        this.btnNext.addEventListener('click', () => this.nextPage());

        // Table header sorting
        document.querySelectorAll('th[data-sort]').forEach(th => {
            th.addEventListener('click', () => {
                this.sortTable(th.dataset.sort);
            });
        });

        // Live search on Enter
        this.gradeInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.performSearch();
        });
    }

    async loadDatabases() {
        try {
            const response = await fetch('/api/warehouse/databases');
            const data = await response.json();

            // Sort databases by date (newest first)
            // Extract date from filename like "Склад на 30.12.25.xlsx" or "Склад 14.08.25.xlsx"
            const sortedDatabases = data.databases.sort((a, b) => {
                const dateA = this.extractDateFromFilename(a);
                const dateB = this.extractDateFromFilename(b);
                return dateB - dateA; // Newest first
            });

            this.dbSelect.innerHTML = '';
            sortedDatabases.forEach(db => {
                const option = document.createElement('option');
                option.value = db;
                option.textContent = db;
                this.dbSelect.appendChild(option);
            });

            // Load newest database (first in sorted list)
            if (sortedDatabases.length > 0) {
                await this.loadStocks();
            }
        } catch (error) {
            console.error('Error loading databases:', error);
            this.showError('Ошибка загрузки списка баз данных');
        }
    }

    extractDateFromFilename(filename) {
        // Extract date from formats like:
        // "Склад на 30.12.25.xlsx" -> 30.12.2025
        // "Склад 14.08.25.xlsx" -> 14.08.2025
        // "Склад НН.xlsx" -> very old date

        const dateMatch = filename.match(/(\d{1,2})\.(\d{1,2})\.(\d{2,4})/);
        if (dateMatch) {
            let day = parseInt(dateMatch[1]);
            let month = parseInt(dateMatch[2]);
            let year = parseInt(dateMatch[3]);

            // Convert 2-digit year to 4-digit
            if (year < 100) {
                year += 2000;
            }

            // Return timestamp for sorting
            return new Date(year, month - 1, day).getTime();
        }

        // Files without date go to the end (very old)
        return new Date(2000, 0, 1).getTime();
    }

    async loadStocks() {
        const db = this.dbSelect.value;
        if (!db) return;

        this.showLoading();

        try {
            const response = await fetch(`/api/warehouse/stocks?db=${encodeURIComponent(db)}`);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            // Ensure items is an array
            this.allItems = Array.isArray(data.items) ? data.items : [];
            this.filteredItems = [...this.allItems];
            this.currentPage = 1;

            this.updateStats();
            this.renderTable();
        } catch (error) {
            console.error('Error loading stocks:', error);
            this.allItems = [];
            this.filteredItems = [];
            this.showError(`Ошибка загрузки данных склада: ${error.message}`);
        }
    }

    async performSearch() {
        const db = this.dbSelect.value;
        if (!db) return;

        this.showLoading();

        // Build search request
        const searchParams = {
            db: db
        };

        // Grade filter
        const grade = this.gradeInput.value.trim();
        if (grade) {
            searchParams.grade = grade;
        }

        // Type filter
        const selectedType = document.querySelector('input[name="type"]:checked').value;
        if (selectedType) {
            searchParams.type = selectedType;
        }

        // Dimension filters for blocks
        if (selectedType === 'block' || !selectedType) {
            const x = parseFloat(this.blockX.value);
            const y = parseFloat(this.blockY.value);
            const z = parseFloat(this.blockZ.value);

            if (x || y || z) {
                searchParams.minDimensions = {
                    x: x || 0,
                    y: y || 0,
                    z: z || 0
                };
            }
        }

        // Diameter filter for circles
        if (selectedType === 'circle') {
            const diam = parseFloat(this.diameter.value);
            if (diam) {
                searchParams.diameter = diam;
                searchParams.tolerance = parseFloat(this.circleTolerance.value) || 5;
            }
        }

        // Thickness filter for sheets (only thickness with tolerance - like circles)
        if (selectedType === 'sheet') {
            const thickness = parseFloat(this.sheetZ.value);
            if (thickness) {
                searchParams.sheetThickness = thickness;
                searchParams.sheetTolerance = parseFloat(this.sheetTolerance.value) || 0.5;
            }
        }

        // Thickness filter for strips (only thickness with tolerance - like circles)
        if (selectedType === 'strip') {
            const thickness = parseFloat(this.stripZ.value);
            if (thickness) {
                searchParams.stripThickness = thickness;
                searchParams.stripTolerance = parseFloat(this.stripTolerance.value) || 0.5;
            }
        }

        try {
            const response = await fetch('/api/warehouse/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(searchParams)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            this.filteredItems = Array.isArray(data.items) ? data.items : [];
            this.currentPage = 1;

            this.updateStats(data.total);
            this.renderTable();
        } catch (error) {
            console.error('Error searching:', error);
            this.filteredItems = [];
            this.showError(`Ошибка поиска: ${error.message}`);
        }
    }

    resetFilters() {
        // Reset form
        this.gradeInput.value = '';
        document.querySelector('input[name="type"][value=""]').checked = true;

        // Reset block inputs
        this.blockX.value = '';
        this.blockY.value = '';
        this.blockZ.value = '';

        // Reset circle inputs
        this.diameter.value = '';
        this.circleTolerance.value = '5';

        // Reset sheet inputs
        this.sheetX.value = '';
        this.sheetY.value = '';
        this.sheetZ.value = '';
        this.sheetTolerance.value = '0.5';

        // Reset strip inputs
        this.stripX.value = '';
        this.stripY.value = '';
        this.stripZ.value = '';
        this.stripTolerance.value = '0.5';

        // Reset data
        this.filteredItems = [...this.allItems];
        this.currentPage = 1;

        this.toggleFilterInputs();
        this.updateStats();
        this.renderTable();
    }

    toggleFilterInputs() {
        const selectedType = document.querySelector('input[name="type"]:checked').value;

        // Show/hide filters based on type
        this.blockFilters.style.display = 'none';
        this.circleFilters.style.display = 'none';
        this.sheetFilters.style.display = 'none';
        this.stripFilters.style.display = 'none';

        if (selectedType === 'block') {
            this.blockFilters.style.display = 'block';
        } else if (selectedType === 'circle') {
            this.circleFilters.style.display = 'block';
        } else if (selectedType === 'sheet') {
            this.sheetFilters.style.display = 'block';
        } else if (selectedType === 'strip') {
            this.stripFilters.style.display = 'block';
        } else {
            // "All" selected - show blocks by default
            this.blockFilters.style.display = 'block';
        }
    }

    sortTable(column) {
        // Toggle sort direction
        if (this.sortColumn === column) {
            this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            this.sortColumn = column;
            this.sortDirection = 'asc';
        }

        // Sort items
        this.filteredItems.sort((a, b) => {
            let valA = a[column];
            let valB = b[column];

            // Handle null values
            if (valA === null || valA === undefined) return 1;
            if (valB === null || valB === undefined) return -1;

            // Numeric comparison
            if (typeof valA === 'number') {
                return this.sortDirection === 'asc' ? valA - valB : valB - valA;
            }

            // String comparison
            const strA = String(valA).toLowerCase();
            const strB = String(valB).toLowerCase();

            if (this.sortDirection === 'asc') {
                return strA < strB ? -1 : strA > strB ? 1 : 0;
            } else {
                return strA > strB ? -1 : strA < strB ? 1 : 0;
            }
        });

        // Update UI
        document.querySelectorAll('th[data-sort]').forEach(th => {
            th.classList.remove('sort-asc', 'sort-desc');
        });

        const th = document.querySelector(`th[data-sort="${column}"]`);
        th.classList.add(`sort-${this.sortDirection}`);

        this.renderTable();
    }

    renderTable() {
        const start = (this.currentPage - 1) * this.itemsPerPage;
        const end = start + this.itemsPerPage;
        const pageItems = this.filteredItems.slice(start, end);

        if (pageItems.length === 0) {
            this.tableBody.innerHTML = `
                <tr>
                    <td colspan="5" class="no-results">
                        <strong>Нет результатов</strong>
                        <div>Попробуйте изменить параметры поиска</div>
                    </td>
                </tr>
            `;
        } else {
            this.tableBody.innerHTML = pageItems.map(item => `
                <tr>
                    <td>${this.escapeHtml(item.full_name)}</td>
                    <td>${this.getTypeBadge(item.type)}</td>
                    <td>${this.escapeHtml(item.size_text)}</td>
                    <td>${this.formatNumber(item.weight)}</td>
                    <td>${item.quantity}</td>
                </tr>
            `).join('');
        }

        this.updatePagination();
    }

    updatePagination() {
        const totalPages = Math.ceil(this.filteredItems.length / this.itemsPerPage);

        this.pageInfo.textContent = `Страница ${this.currentPage} из ${totalPages || 1}`;
        this.btnPrev.disabled = this.currentPage === 1;
        this.btnNext.disabled = this.currentPage >= totalPages;
    }

    previousPage() {
        if (this.currentPage > 1) {
            this.currentPage--;
            this.renderTable();
            this.scrollToTop();
        }
    }

    nextPage() {
        const totalPages = Math.ceil(this.filteredItems.length / this.itemsPerPage);
        if (this.currentPage < totalPages) {
            this.currentPage++;
            this.renderTable();
            this.scrollToTop();
        }
    }

    scrollToTop() {
        document.querySelector('.table-container').scrollTop = 0;
    }

    updateStats(total = null) {
        const totalItems = total !== null ? total : this.allItems.length;
        const showing = this.filteredItems.length;

        if (showing === totalItems) {
            this.statsText.innerHTML = `Показано: <strong>${showing}</strong> записей`;
        } else {
            this.statsText.innerHTML = `Найдено: <strong>${showing}</strong> из <strong>${totalItems}</strong> записей`;
        }
    }

    getTypeBadge(type) {
        const typeNames = {
            block: 'Блок',
            circle: 'Круг',
            sheet: 'Лист',
            strip: 'Полоса',
            square: 'Квадрат'
        };

        const name = typeNames[type] || type;
        return `<span class="type-badge type-${type}">${name}</span>`;
    }

    formatNumber(num) {
        if (!num) return '0';
        return new Intl.NumberFormat('ru-RU', {
            minimumFractionDigits: 0,
            maximumFractionDigits: 3
        }).format(num);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    showLoading() {
        this.tableBody.innerHTML = `
            <tr>
                <td colspan="5" class="loading">Загрузка данных...</td>
            </tr>
        `;
        this.statsText.textContent = 'Загрузка...';
    }

    showError(message) {
        this.tableBody.innerHTML = `
            <tr>
                <td colspan="5" class="no-results">
                    <strong>Ошибка</strong>
                    <div>${message}</div>
                </td>
            </tr>
        `;
        this.statsText.textContent = 'Ошибка загрузки';
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.warehouseApp = new WarehouseApp();
});
