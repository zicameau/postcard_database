// Main JavaScript file for Postcard Database

document.addEventListener('DOMContentLoaded', function() {
    // Add date filter functionality
    setupDateFilters();
    
    // Add custom datetime filter for Jinja
    addDateTimeFilter();
    
    // Add line break filter for Jinja
    addLineBreakFilter();
    
    // Handle flash message dismissal
    setupFlashMessages();
});

/**
 * Setup date filters in the list view
 */
function setupDateFilters() {
    const dateInputs = document.querySelectorAll('input[type="date"]');
    
    dateInputs.forEach(input => {
        input.addEventListener('change', function() {
            // If part of a form, submit the form when the date changes
            const form = this.closest('form');
            if (form && form.id === 'filter-form') {
                form.submit();
            }
        });
    });
}

/**
 * Add a custom filter to format datetime values
 */
function addDateTimeFilter() {
    // This would typically be done server-side in Flask, but we include it here for reference
    // Using a template filter like:
    //
    // @app.template_filter('datetime')
    // def format_datetime(value, format='%B %d, %Y'):
    //     if value:
    //         return value.strftime(format)
    //     return ''
}

/**
 * Add a custom filter to convert newlines to <br> tags
 */
function addLineBreakFilter() {
    // This would typically be done server-side in Flask, but we include it here for reference
    // Using a template filter like:
    //
    // @app.template_filter('nl2br')
    // def nl2br(value):
    //     if value:
    //         return Markup(value.replace('\n', '<br>'))
    //     return ''
}

/**
 * Setup dismissable flash messages
 */
function setupFlashMessages() {
    const flashMessages = document.querySelectorAll('.flash-message');
    
    flashMessages.forEach(message => {
        // Create a dismiss button
        const dismissBtn = document.createElement('button');
        dismissBtn.className = 'flash-dismiss';
        dismissBtn.innerHTML = '&times;';
        dismissBtn.setAttribute('aria-label', 'Dismiss');
        
        // Add the button to the message
        message.appendChild(dismissBtn);
        
        // Add click event to dismiss the message
        dismissBtn.addEventListener('click', function() {
            message.remove();
        });
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            message.classList.add('flash-fade');
            setTimeout(() => {
                message.remove();
            }, 500);
        }, 5000);
    });
}

/**
 * Handle image previews for file inputs
 * @param {HTMLElement} inputElement - The file input element
 * @param {HTMLElement} previewElement - The preview container element
 */
function handleImagePreview(inputElement, previewElement) {
    inputElement.addEventListener('change', function() {
        if (this.files && this.files[0]) {
            const reader = new FileReader();
            
            reader.onload = function(e) {
                // Create or update image
                let img = previewElement.querySelector('img');
                
                if (!img) {
                    img = document.createElement('img');
                    previewElement.innerHTML = '';
                    previewElement.appendChild(img);
                }
                
                img.src = e.target.result;
                img.alt = 'Image Preview';
            }
            
            reader.readAsDataURL(this.files[0]);
        } else {
            previewElement.innerHTML = '<div class="placeholder">No image selected</div>';
        }
    });
}

/**
 * Toggle the visibility of a modal
 * @param {string} modalId - The ID of the modal to toggle
 */
function toggleModal(modalId) {
    const modal = document.getElementById(modalId);
    
    if (modal) {
        modal.classList.toggle('visible');
    }
}