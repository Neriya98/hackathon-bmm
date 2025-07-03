// DealSure Frontend Application
class DealSureApp {
    constructor() {
        this.apiBase = '/api/v1';
        this.csrfToken = window.csrfToken;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupAjaxDefaults();
        this.initializeComponents();
        this.setupToastNotifications();
    }

    setupEventListeners() {
        // Global error handling
        window.addEventListener('error', (e) => {
            console.error('Global error:', e.error);
            this.showToast('An unexpected error occurred', 'error');
        });

        // Handle form submissions
        document.addEventListener('submit', (e) => {
            const form = e.target;
            if (form.dataset.ajax === 'true') {
                e.preventDefault();
                this.handleAjaxForm(form);
            }
        });

        // Handle dynamic content loading
        document.addEventListener('click', (e) => {
            const link = e.target.closest('[data-load]');
            if (link) {
                e.preventDefault();
                this.loadDynamicContent(link);
            }
        });

        // Handle file uploads
        document.addEventListener('change', (e) => {
            if (e.target.type === 'file') {
                this.handleFileUpload(e.target);
            }
        });
    }

    setupAjaxDefaults() {
        // Setup default headers for all AJAX requests
        if (typeof jQuery !== 'undefined') {
            $.ajaxSetup({
                beforeSend: (xhr) => {
                    xhr.setRequestHeader('X-CSRFToken', this.csrfToken);
                }
            });
        }
    }

    initializeComponents() {
        // Initialize copy to clipboard buttons
        this.initializeCopyButtons();
        
        // Initialize auto-refresh components
        this.initializeAutoRefresh();
        
        // Initialize loading states
        this.initializeLoadingStates();
        
        // Initialize tooltips
        this.initializeTooltips();
    }

    initializeCopyButtons() {
        document.querySelectorAll('[data-copy]').forEach(button => {
            button.addEventListener('click', () => {
                const text = button.dataset.copy || button.textContent;
                navigator.clipboard.writeText(text).then(() => {
                    this.showToast('Copied to clipboard', 'success');
                }).catch(() => {
                    this.showToast('Failed to copy', 'error');
                });
            });
        });
    }

    initializeAutoRefresh() {
        const autoRefreshElements = document.querySelectorAll('[data-auto-refresh]');
        autoRefreshElements.forEach(element => {
            const interval = parseInt(element.dataset.autoRefresh) || 30000;
            setInterval(() => {
                if (!document.hidden) {
                    this.refreshElement(element);
                }
            }, interval);
        });
    }

    initializeLoadingStates() {
        // Add loading states to buttons
        document.querySelectorAll('button[type="submit"]').forEach(button => {
            const form = button.closest('form');
            if (form) {
                form.addEventListener('submit', () => {
                    this.setLoadingState(button, true);
                });
            }
        });
    }

    initializeTooltips() {
        // Simple tooltip implementation
        document.querySelectorAll('[data-tooltip]').forEach(element => {
            element.addEventListener('mouseenter', (e) => {
                this.showTooltip(e.target);
            });
            element.addEventListener('mouseleave', () => {
                this.hideTooltip();
            });
        });
    }

    // API Methods
    async apiCall(endpoint, options = {}) {
        const url = this.apiBase + endpoint;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.csrfToken,
                ...options.headers
            },
            ...options
        };

        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('API call failed:', error);
            this.showToast('API request failed', 'error');
            throw error;
        }
    }

    async get(endpoint) {
        return this.apiCall(endpoint, { method: 'GET' });
    }

    async post(endpoint, data) {
        return this.apiCall(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async put(endpoint, data) {
        return this.apiCall(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    async delete(endpoint) {
        return this.apiCall(endpoint, { method: 'DELETE' });
    }

    // Contract Management
    async createContract(contractData) {
        try {
            this.showLoading();
            const result = await this.post('/contracts', contractData);
            this.hideLoading();
            this.showToast('Contract created successfully', 'success');
            return result;
        } catch (error) {
            this.hideLoading();
            throw error;
        }
    }

    async signContract(contractId, signature) {
        try {
            this.showLoading();
            const result = await this.post(`/contracts/${contractId}/sign`, { signature });
            this.hideLoading();
            this.showToast('Contract signed successfully', 'success');
            return result;
        } catch (error) {
            this.hideLoading();
            throw error;
        }
    }

    async inviteUser(contractId, email, role = 'participant') {
        try {
            this.showLoading();
            const result = await this.post(`/contracts/${contractId}/invite`, { email, role });
            this.hideLoading();
            this.showToast('Invitation sent successfully', 'success');
            return result;
        } catch (error) {
            this.hideLoading();
            throw error;
        }
    }

    // PSBT Operations
    async createPSBT(psbtData) {
        try {
            this.showLoading();
            const result = await this.post('/psbt/create', psbtData);
            this.hideLoading();
            return result;
        } catch (error) {
            this.hideLoading();
            throw error;
        }
    }

    async signPSBT(psbtHex, privateKey) {
        try {
            this.showLoading();
            const result = await this.post('/psbt/sign', { 
                psbt_hex: psbtHex, 
                private_key: privateKey 
            });
            this.hideLoading();
            return result;
        } catch (error) {
            this.hideLoading();
            throw error;
        }
    }

    async finalizePSBT(psbtHex) {
        try {
            this.showLoading();
            const result = await this.post('/psbt/finalize', { psbt_hex: psbtHex });
            this.hideLoading();
            return result;
        } catch (error) {
            this.hideLoading();
            throw error;
        }
    }

    // UI Helper Methods
    showLoading() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.style.display = 'block';
            setTimeout(() => overlay.classList.add('opacity-100'), 10);
        }
    }

    hideLoading() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.classList.remove('opacity-100');
            setTimeout(() => overlay.style.display = 'none', 300);
        }
    }

    setLoadingState(button, loading) {
        if (loading) {
            button.disabled = true;
            button.dataset.originalText = button.textContent;
            button.innerHTML = `
                <svg class="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Processing...
            `;
        } else {
            button.disabled = false;
            button.textContent = button.dataset.originalText || 'Submit';
        }
    }

    setupToastNotifications() {
        // Create toast container if it doesn't exist
        if (!document.getElementById('toast-container')) {
            const container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'fixed top-4 right-4 z-50 space-y-2';
            document.body.appendChild(container);
        }
    }

    showToast(message, type = 'info', duration = 5000) {
        const container = document.getElementById('toast-container');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `
            max-w-sm bg-white shadow-lg rounded-lg pointer-events-auto ring-1 ring-black ring-opacity-5 overflow-hidden
            transform transition-all duration-300 ease-in-out translate-x-full opacity-0
        `;

        const iconColors = {
            success: 'text-green-400',
            error: 'text-red-400',
            warning: 'text-yellow-400',
            info: 'text-blue-400'
        };

        const icons = {
            success: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
            error: 'M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z',
            warning: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5l-6.928-12c-.77-.833-2.694-.833-3.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z',
            info: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'
        };

        toast.innerHTML = `
            <div class="p-4">
                <div class="flex items-start">
                    <div class="flex-shrink-0">
                        <svg class="h-6 w-6 ${iconColors[type]}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="${icons[type]}" />
                        </svg>
                    </div>
                    <div class="ml-3 w-0 flex-1 pt-0.5">
                        <p class="text-sm font-medium text-gray-900">${message}</p>
                    </div>
                    <div class="ml-4 flex-shrink-0 flex">
                        <button class="bg-white rounded-md inline-flex text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500" onclick="this.parentElement.parentElement.parentElement.parentElement.remove()">
                            <span class="sr-only">Close</span>
                            <svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
        `;

        container.appendChild(toast);

        // Trigger animation
        setTimeout(() => {
            toast.classList.remove('translate-x-full', 'opacity-0');
            toast.classList.add('translate-x-0', 'opacity-100');
        }, 10);

        // Auto-remove toast
        if (duration > 0) {
            setTimeout(() => {
                toast.classList.add('translate-x-full', 'opacity-0');
                setTimeout(() => toast.remove(), 300);
            }, duration);
        }
    }

    showTooltip(element) {
        const tooltip = document.createElement('div');
        tooltip.id = 'tooltip';
        tooltip.className = 'absolute z-50 px-2 py-1 text-sm text-white bg-gray-900 rounded shadow-lg pointer-events-none';
        tooltip.textContent = element.dataset.tooltip;

        document.body.appendChild(tooltip);

        const rect = element.getBoundingClientRect();
        tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
        tooltip.style.top = rect.top - tooltip.offsetHeight - 5 + 'px';
    }

    hideTooltip() {
        const tooltip = document.getElementById('tooltip');
        if (tooltip) {
            tooltip.remove();
        }
    }

    // Form handling
    async handleAjaxForm(form) {
        const formData = new FormData(form);
        const url = form.action || window.location.href;
        const method = form.method || 'POST';

        try {
            const response = await fetch(url, {
                method,
                body: formData,
                headers: {
                    'X-CSRFToken': this.csrfToken
                }
            });

            const result = await response.json();

            if (response.ok) {
                this.showToast(result.message || 'Operation successful', 'success');
                if (result.redirect) {
                    window.location.href = result.redirect;
                }
            } else {
                this.showToast(result.error || 'Operation failed', 'error');
            }
        } catch (error) {
            console.error('Form submission failed:', error);
            this.showToast('Form submission failed', 'error');
        }
    }

    // Dynamic content loading
    async loadDynamicContent(element) {
        const url = element.dataset.load;
        const target = document.querySelector(element.dataset.target);

        if (!target) {
            console.error('Target element not found');
            return;
        }

        try {
            this.showLoading();
            const response = await fetch(url, {
                headers: {
                    'X-CSRFToken': this.csrfToken
                }
            });

            if (response.ok) {
                const html = await response.text();
                target.innerHTML = html;
                
                // Re-initialize components in the new content
                this.initializeComponents();
            } else {
                this.showToast('Failed to load content', 'error');
            }
        } catch (error) {
            console.error('Content loading failed:', error);
            this.showToast('Content loading failed', 'error');
        } finally {
            this.hideLoading();
        }
    }

    // File upload handling
    handleFileUpload(input) {
        const files = Array.from(input.files);
        const maxSize = 10 * 1024 * 1024; // 10MB
        const allowedTypes = ['application/json', 'text/plain'];

        files.forEach(file => {
            if (file.size > maxSize) {
                this.showToast(`File ${file.name} is too large (max 10MB)`, 'error');
                input.value = '';
                return;
            }

            if (!allowedTypes.includes(file.type) && !file.name.endsWith('.psbt')) {
                this.showToast(`File ${file.name} has unsupported type`, 'error');
                input.value = '';
                return;
            }
        });
    }

    // Element refresh
    async refreshElement(element) {
        const url = element.dataset.refreshUrl || window.location.href;
        const selector = element.dataset.refreshSelector || element.tagName.toLowerCase();

        try {
            const response = await fetch(url, {
                headers: {
                    'X-CSRFToken': this.csrfToken
                }
            });

            if (response.ok) {
                const html = await response.text();
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                const newElement = doc.querySelector(selector);

                if (newElement) {
                    element.innerHTML = newElement.innerHTML;
                    this.initializeComponents();
                }
            }
        } catch (error) {
            console.error('Element refresh failed:', error);
        }
    }

    // Utility methods
    formatBTC(amount) {
        return new Intl.NumberFormat('en-US', {
            minimumFractionDigits: 8,
            maximumFractionDigits: 8
        }).format(amount) + ' BTC';
    }

    formatDate(date) {
        return new Intl.DateTimeFormat('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        }).format(new Date(date));
    }

    truncateAddress(address, length = 6) {
        if (!address || address.length <= length * 2) return address;
        return `${address.slice(0, length)}...${address.slice(-length)}`;
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    window.app = new DealSureApp();
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DealSureApp;
}
