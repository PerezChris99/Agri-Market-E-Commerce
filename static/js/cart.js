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
    fetchWithTimeout('/update_item/', {
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
    if (window.setCartCookie) window.setCartCookie(cart);
    
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
    fetchWithTimeout('/toggle-wishlist/', {
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
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'position-fixed bottom-0 end-0 p-3';
        toastContainer.style.zIndex = '1050';
        document.body.appendChild(toastContainer);
    }

    const toastElement = document.createElement('div');
    toastElement.className = 'toast align-items-center text-white ' +
        (type === 'success' ? 'bg-success' : 'bg-danger') + ' border-0';
    toastElement.setAttribute('role', 'alert');
    toastElement.setAttribute('aria-live', 'assertive');
    toastElement.setAttribute('aria-atomic', 'true');

    const wrapper = document.createElement('div');
    wrapper.className = 'd-flex';

    const body = document.createElement('div');
    body.className = 'toast-body';
    body.textContent = String(message || '');

    const close = document.createElement('button');
    close.type = 'button';
    close.className = 'btn-close btn-close-white me-2 m-auto';
    close.setAttribute('data-bs-dismiss', 'toast');
    close.setAttribute('aria-label', 'Close');

    wrapper.append(body, close);
    toastElement.appendChild(wrapper);
    toastContainer.appendChild(toastElement);

    const toast = new bootstrap.Toast(toastElement, { delay: 3000 });
    toast.show();
    toastElement.addEventListener('hidden.bs.toast', () => toastElement.remove());
}
