function initDraggableModal() {
    let isDragging = false;
    let startX, startY, initialX, initialY;
    let modalDialog = null;

    $('#farmModal').on('show.bs.modal', function() {
        modalDialog = $('.modal-dialog-draggable')[0];
        
        if (!modalDialog) return;
        
        // Center the modal when it first opens
        setTimeout(function() {
            const windowWidth = window.innerWidth;
            const windowHeight = window.innerHeight;
            const modalWidth = modalDialog.offsetWidth;
            const modalHeight = modalDialog.offsetHeight;
            
            const xOffset = (windowWidth - modalWidth) / 2;
            const yOffset = (windowHeight - modalHeight) / 3;
            
            modalDialog.style.left = xOffset + 'px';
            modalDialog.style.top = yOffset + 'px';
        }, 10);
    });

    // Handle mouse down on draggable handle
    $(document).on('mousedown touchstart', '.draggable-handle', function(e) {
        if (!modalDialog) return;
        
        isDragging = true;
        modalDialog.style.cursor = 'grabbing';
        
        if (e.type === 'touchstart') {
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
        } else {
            startX = e.clientX;
            startY = e.clientY;
        }
        
        initialX = parseInt(modalDialog.style.left) || 0;
        initialY = parseInt(modalDialog.style.top) || 0;
        
        e.preventDefault();
    });

    // Handle mouse move
    $(document).on('mousemove touchmove', function(e) {
        if (!isDragging || !modalDialog) return;
        
        let currentX, currentY;
        
        if (e.type === 'touchmove') {
            currentX = e.touches[0].clientX;
            currentY = e.touches[0].clientY;
        } else {
            currentX = e.clientX;
            currentY = e.clientY;
        }
        
        const deltaX = currentX - startX;
        const deltaY = currentY - startY;
        
        const newX = initialX + deltaX;
        const newY = initialY + deltaY;
        
        // Keep modal within window bounds
        const maxX = window.innerWidth - modalDialog.offsetWidth;
        const maxY = window.innerHeight - modalDialog.offsetHeight;
        
        modalDialog.style.left = Math.max(0, Math.min(newX, maxX)) + 'px';
        modalDialog.style.top = Math.max(0, Math.min(newY, maxY)) + 'px';
    });

    // Handle mouse up
    $(document).on('mouseup touchend', function() {
        if (isDragging && modalDialog) {
            modalDialog.style.cursor = 'grab';
        }
        isDragging = false;
    });

    // Reset when modal is closed
    $('#farmModal').on('hidden.bs.modal', function() {
        isDragging = false;
        if (modalDialog) {
            modalDialog.style.cursor = '';
            modalDialog.style.left = '';
            modalDialog.style.top = '';
        }
        modalDialog = null;
    });
}

$(document).ready(function() {
    initDraggableModal();
});