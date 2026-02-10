/**
 * Agri-Market Cart Management
 * Handles cart operations for both authenticated and anonymous users
 */

// Get all update buttons and attach event listeners
document.addEventListener('DOMContentLoaded', function() {
    initializeCartButtons();
    initializeWishlistButtons();
});

function initializeCartButtons() {
    const updateBtns = document.getElementsByClassName('update-cart');
    
    for (let i = 0; i < updateBtns.length; i++) {
        updateBtns[i].addEventListener('click', function(e) {
            e.preventDefault();
            
            const productId = this.dataset.product;
            const action = this.dataset.action;
            
            if (!productId || !action) return;

            if (isAuthenticated) {
                // Authenticated user - use database cart
                updateDatabaseCart(productId, action);
            } else {
                // Anonymous user - use cookie cart
                updateCookieCart(productId, action);
            }
        });
    }
}

function initializeWishlistButtons() {
    const wishlistBtns = document.querySelectorAll('.wishlist-btn');
    
    wishlistBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            
            if (!isAuthenticated) {
                window.location.href = '/login/';
                return;
            }
            
            const productId = this.dataset.productId;
            toggleWishlist(productId, this);
        });
    });
}

function updateDatabaseCart(productId, action) {
    fetch('/update_item/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken,
        },
        body: JSON.stringify({
            productId: productId,
            action: action
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update cart counter in navbar
            updateCartCounter(data.cartItems);
            
            // Show success message
            showToast(data.message, 'success');
            
            // If on cart page, reload to update items
            if (window.location.pathname === '/cart/') {
                location.reload();
            }
        } else {
            showToast(data.message || 'Error updating cart', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('An error occurred', 'error');
    });
}

function updateCookieCart(productId, action) {
    if (action === 'add') {
        if (!cart[productId]) {
            cart[productId] = { quantity: 1 };
        } else {
            cart[productId].quantity += 1;
        }
        showToast('Added to cart', 'success');
    } else if (action === 'remove') {
        if (cart[productId]) {
            cart[productId].quantity -= 1;
            
            if (cart[productId].quantity <= 0) {
                delete cart[productId];
            }
        }
        showToast('Removed from cart', 'success');
    }
    
    // Save to cookie
    document.cookie = 'cart=' + JSON.stringify(cart) + ';domain=;path=/';
    
    // Update cart counter
    const totalItems = Object.values(cart).reduce((sum, item) => sum + item.quantity, 0);
    updateCartCounter(totalItems);
    
    // If on cart page, reload to update items
    if (window.location.pathname === '/cart/') {
        location.reload();
    }
}

function updateCartCounter(count) {
    const cartTotalElement = document.getElementById('cart-total');
    if (cartTotalElement) {
        cartTotalElement.textContent = count || 0;
        
        // Add animation
        cartTotalElement.classList.add('pulse');
        setTimeout(() => cartTotalElement.classList.remove('pulse'), 300);
    }
}

function toggleWishlist(productId, buttonElement) {
    fetch('/toggle-wishlist/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken,
        },
        body: JSON.stringify({ product_id: productId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const icon = buttonElement.querySelector('i');
            if (data.action === 'added') {
                icon.classList.remove('bi-heart');
                icon.classList.add('bi-heart-fill');
            } else {
                icon.classList.remove('bi-heart-fill');
                icon.classList.add('bi-heart');
            }
            showToast(data.message, 'success');
        } else {
            showToast(data.message || 'Error updating wishlist', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('An error occurred', 'error');
    });
}

function showToast(message, type = 'success') {
    // Create toast container if it doesn't exist
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'position-fixed bottom-0 end-0 p-3';
        toastContainer.style.zIndex = '1050';
        document.body.appendChild(toastContainer);
    }
    
    const toastId = 'toast-' + Date.now();
    const bgClass = type === 'success' ? 'bg-success' : 'bg-danger';
    
    const toastHTML = `
        <div id="${toastId}" class="toast align-items-center text-white ${bgClass} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    <i class="bi bi-${type === 'success' ? 'check-circle' : 'exclamation-circle'} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHTML);
    
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, { delay: 3000 });
    toast.show();
    
    // Remove toast element after it's hidden
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
}

// Add CSS for pulse animation
const style = document.createElement('style');
style.textContent = `
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.2); }
        100% { transform: scale(1); }
    }
    .pulse {
        animation: pulse 0.3s ease-in-out;
    }
`;
document.head.appendChild(style);
