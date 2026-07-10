/**
 * Toast Notification System
 * A reusable toast notification component with Django messages framework integration
 */

class ToastManager {
  constructor(options = {}) {
    this.toasts = [];
    this.container = null;
    this.defaultDuration = options.defaultDuration || 4000; // 4 seconds
    this.maxToasts = options.maxToasts || 5;
    this.init();
  }

  /**
   * Initialize the toast container and process Django messages
   */
  init() {
    this.ensureContainer();
    this.processDjangoMessages();
  }

  /**
   * Ensure the toast container exists in the DOM
   */
  ensureContainer() {
    let container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      container.className = 'toast-container';
      document.body.appendChild(container);
    }
    this.container = container;
  }

  /**
   * Show a toast notification
   * @param {string} message - The message text
   * @param {string} type - The toast type: 'success', 'error', 'warning', 'info'
   * @param {Object} options - Additional options
   */
  show(message, type = 'info', options = {}) {
    const {
      title = this.getTitleByType(type),
      duration = this.defaultDuration,
      closeable = true,
    } = options;

    // Limit the number of toasts
    if (this.toasts.length >= this.maxToasts) {
      this.toasts[0].remove();
    }

    const toast = this.createToastElement(title, message, type, closeable);
    this.container.appendChild(toast);
    this.toasts.push(toast);

    // Trigger animation
    setTimeout(() => {
      toast.classList.add('show');
    }, 10);

    // Auto-dismiss
    if (duration > 0) {
      const timeoutId = setTimeout(() => {
        this.dismissToast(toast);
      }, duration);

      // Store timeout ID for cleanup
      toast.dataset.timeoutId = timeoutId;
    }

    return toast;
  }

  /**
   * Create a toast element
   */
  createToastElement(title, message, type, closeable) {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', type === 'error' ? 'assertive' : 'polite');

    const icon = this.getIconByType(type);

    toast.innerHTML = `
      <div class="toast-icon" aria-hidden="true">${icon}</div>
      <div class="toast-content">
        <p class="toast-title">${this.escapeHtml(title)}</p>
        <p class="toast-description">${this.escapeHtml(message)}</p>
      </div>
      ${closeable ? '<button class="toast-close" type="button" aria-label="Close notification">×</button>' : ''}
    `;

    if (closeable) {
      const closeButton = toast.querySelector('.toast-close');
      closeButton.addEventListener('click', () => this.dismissToast(toast));
    }

    // Clear timeout on hover (optional - prevents accidental dismissal while reading)
    toast.addEventListener('mouseenter', () => {
      if (toast.dataset.timeoutId) {
        clearTimeout(parseInt(toast.dataset.timeoutId));
      }
    });

    toast.addEventListener('mouseleave', () => {
      if (toast.dataset.timeoutId && !toast.classList.contains('removing')) {
        const timeoutId = setTimeout(() => {
          this.dismissToast(toast);
        }, 2000); // 2 second remaining time
        toast.dataset.timeoutId = timeoutId;
      }
    });

    return toast;
  }

  /**
   * Dismiss a toast notification
   */
  dismissToast(toast) {
    if (toast.classList.contains('removing')) return;

    toast.classList.add('removing');

    // Wait for animation to complete
    setTimeout(() => {
      if (toast.dataset.timeoutId) {
        clearTimeout(parseInt(toast.dataset.timeoutId));
      }
      toast.remove();
      this.toasts = this.toasts.filter((t) => t !== toast);
    }, 300); // Match CSS animation duration
  }

  /**
   * Get icon SVG by type
   */
  getIconByType(type) {
    const icons = {
      success: '✓',
      error: '✕',
      warning: '⚠',
      info: 'ℹ',
    };
    return icons[type] || icons.info;
  }

  /**
   * Get title by type
   */
  getTitleByType(type) {
    const titles = {
      success: 'Success',
      error: 'Error',
      warning: 'Warning',
      info: 'Info',
    };
    return titles[type] || titles.info;
  }

  /**
   * Escape HTML to prevent XSS
   */
  escapeHtml(text) {
    const map = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;',
    };
    return text.replace(/[&<>"']/g, (m) => map[m]);
  }

  /**
   * Show success toast
   */
  success(message, title = 'Success', duration) {
    return this.show(message, 'success', { title, duration });
  }

  /**
   * Show error toast
   */
  error(message, title = 'Error', duration) {
    return this.show(message, 'error', { title, duration });
  }

  /**
   * Show warning toast
   */
  warning(message, title = 'Warning', duration) {
    return this.show(message, 'warning', { title, duration });
  }

  /**
   * Show info toast
   */
  info(message, title = 'Info', duration) {
    return this.show(message, 'info', { title, duration });
  }

  /**
   * Process Django messages from data attributes
   * This method reads messages from hidden data attributes set by Django template
   */
  processDjangoMessages() {
    const messagesContainer = document.getElementById('django-messages');
    if (!messagesContainer) return;

    const messages = messagesContainer.querySelectorAll('[data-message]');
    messages.forEach((msg) => {
      const text = msg.getAttribute('data-message');
      const tags = msg.getAttribute('data-tags') || 'info';
      
      // Map Django message tags to toast types
      let type = 'info';
      if (tags.includes('success')) type = 'success';
      else if (tags.includes('error') || tags.includes('danger')) type = 'error';
      else if (tags.includes('warning')) type = 'warning';

      // Extract extra title if provided
      const title = msg.getAttribute('data-title') || undefined;

      this.show(text, type, { title, duration: 4000 });
    });
  }

  /**
   * Clear all toasts
   */
  clearAll() {
    this.toasts.forEach((toast) => this.dismissToast(toast));
    this.toasts = [];
  }

  /**
   * Get active toasts count
   */
  getCount() {
    return this.toasts.length;
  }
}

// Initialize toast manager on document ready
let toastManager;

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    toastManager = new ToastManager();
  });
} else {
  toastManager = new ToastManager();
}

// Global functions for backward compatibility and easy access
window.Toast = {
  show: (message, type, options) => toastManager && toastManager.show(message, type, options),
  success: (message, title, duration) => toastManager && toastManager.success(message, title, duration),
  error: (message, title, duration) => toastManager && toastManager.error(message, title, duration),
  warning: (message, title, duration) => toastManager && toastManager.warning(message, title, duration),
  info: (message, title, duration) => toastManager && toastManager.info(message, title, duration),
  clearAll: () => toastManager && toastManager.clearAll(),
};
