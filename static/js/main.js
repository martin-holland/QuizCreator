/**
 * Main JavaScript utilities for Quiz Application
 */

// Utility function for date formatting
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Utility function for showing toast notifications (if needed in future)
function showToast(message, type = 'info') {
    // Placeholder for future toast implementation
    console.log(`[${type.toUpperCase()}] ${message}`);
}
