// Main JavaScript file for Postcard Database

document.addEventListener('DOMContentLoaded', function() {
    // Add date filter functionality
    setupDateFilters();
    
    // Add dropdown functionality for mobile
    setupMobileDropdown();
    
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
 * Setup dropdown functionality for mobile devices and desktop
 */
function setupMobileDropdown() {
    const dropdownTriggers = document.querySelectorAll('.dropdown-trigger');
    
    dropdownTriggers.forEach(trigger => {
        let dropdownTimeout;
        const dropdown = trigger.closest('.user-dropdown');
        const dropdownMenu = dropdown.querySelector('.dropdown-menu');
        
        // Hover and click events for desktop
        dropdown.addEventListener('mouseenter', function() {
            // Clear any existing timeout
            clearTimeout(dropdownTimeout);
            
            // Show dropdown with a slight delay to prevent accidental closing
            dropdownTimeout = setTimeout(() => {
                dropdown.classList.add('active');
            }, 100);
        });
        
        dropdown.addEventListener('mouseleave', function() {
            // Clear timeout and close dropdown after a short delay
            clearTimeout(dropdownTimeout);
            dropdownTimeout = setTimeout(() => {
                dropdown.classList.remove('active');
            }, 200);
        });
        
        // Click event for mobile and as a fallback
        trigger.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            // Toggle this dropdown
            dropdown.classList.toggle('active');
            
            // Close all other open dropdowns
            document.querySelectorAll('.user-dropdown.active').forEach(openDropdown => {
                if (openDropdown !== dropdown) {
                    openDropdown.classList.remove('active');
                }
            });
        });
        
        // Prevent dropdown from closing immediately when interacting with menu
        dropdownMenu.addEventListener('mouseenter', function() {
            clearTimeout(dropdownTimeout);
        });
        
        dropdownMenu.addEventListener('mouseleave', function() {
            clearTimeout(dropdownTimeout);
            dropdownTimeout = setTimeout(() => {
                dropdown.classList.remove('active');
            }, 200);
        });
    });
    
    // Close dropdowns when clicking outside
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.dropdown-trigger')) {
            document.querySelectorAll('.user-dropdown.active').forEach(dropdown => {
                dropdown.classList.remove('active');
            });
        }
    });
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