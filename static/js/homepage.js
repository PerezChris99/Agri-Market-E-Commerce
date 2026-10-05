/* =====================================================
   🌾 Agri-Market Homepage JavaScript
   ===================================================== */

// Configuration
const HomepageConfig = {
    counterDuration: 2000,
    countdownRefresh: 1000,
    recentlyViewedKey: 'agrimarket_recently_viewed',
    maxRecentlyViewed: 8
};

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', function() {
    initCounterAnimation();
    initFlashDealCountdown();
    initNewsletterForm();
    initContactForm();
    initTestimonialsCarousel();
    initRecentlyViewed();
    initProductRecommendations();
    initWhatsAppWidget();
    initSmoothScroll();
    trackProductView();
});

/* ===== Counter Animation ===== */
function initCounterAnimation() {
    const counters = document.querySelectorAll('.stat-number');
    if (!counters.length) return;
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateCounters(counters);
                observer.disconnect();
            }
        });
    }, { threshold: 0.5 });
    
    const heroStats = document.querySelector('.hero-stats');
    if (heroStats) {
        observer.observe(heroStats);
    }
}

function animateCounters(counters) {
    counters.forEach(counter => {
        const target = parseInt(counter.getAttribute('data-count')) || 0;
        const duration = HomepageConfig.counterDuration;
        const step = target / (duration / 16);
        let current = 0;
        
        const updateCounter = () => {
            current += step;
            if (current < target) {
                counter.textContent = Math.floor(current).toLocaleString();
                requestAnimationFrame(updateCounter);
            } else {
                counter.textContent = target.toLocaleString();
            }
        };
        updateCounter();
    });
}

/* ===== Flash Deal Countdown ===== */
function initFlashDealCountdown() {
    const countdown = document.getElementById('flash-countdown');
    if (!countdown) return;
    
    function updateCountdown() {
        const now = new Date();
        const midnight = new Date();
        midnight.setHours(24, 0, 0, 0);
        const diff = midnight - now;
        
        const hours = Math.floor(diff / (1000 * 60 * 60));
        const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((diff % (1000 * 60)) / 1000);
        
        const hoursEl = document.getElementById('hours');
        const minutesEl = document.getElementById('minutes');
        const secondsEl = document.getElementById('seconds');
        
        if (hoursEl) hoursEl.textContent = hours.toString().padStart(2, '0');
        if (minutesEl) minutesEl.textContent = minutes.toString().padStart(2, '0');
        if (secondsEl) secondsEl.textContent = seconds.toString().padStart(2, '0');
    }
    
    updateCountdown();
    setInterval(updateCountdown, HomepageConfig.countdownRefresh);
}

/* ===== Newsletter Form ===== */
function initNewsletterForm() {
    const form = document.getElementById('newsletter-form');
    if (!form) return;
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const emailInput = this.querySelector('input[type="email"]');
        const submitBtn = this.querySelector('button[type="submit"]');
        const email = emailInput.value.trim();
        
        if (!email) {
            showToast('Please enter your email address', 'error');
            return;
        }
        
        // Disable button and show loading
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Subscribing...';
        
        fetchWithTimeout('/api/newsletter/subscribe/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({ email: email })
        })
        .then(response => response.json())
        .then(data => {
            showToast(data.message, data.success ? 'success' : 'error');
            if (data.success) {
                form.reset();
            }
        })
        .catch(error => {
            showToast('An error occurred. Please try again.', 'error');
        })
        .finally(() => {
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'Subscribe';
        });
    });
}

/* ===== Contact Form ===== */
function initContactForm() {
    const form = document.getElementById('contact-form');
    if (!form) return;
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const submitBtn = this.querySelector('button[type="submit"]');
        
        // Show loading
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Sending...';
        
        // Simulate form submission (in production, this would be an API call)
        setTimeout(() => {
            showToast('Message sent successfully! We\'ll get back to you soon.', 'success');
            form.reset();
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="bi bi-send me-2"></i>Send Message';
        }, 1500);
    });
}

/* ===== Testimonials Carousel ===== */
function initTestimonialsCarousel() {
    const carousel = document.querySelector('.testimonials-carousel');
    if (!carousel) return;
    
    const cards = carousel.querySelectorAll('.testimonial-card');
    const dotsContainer = carousel.querySelector('.carousel-dots');
    let currentIndex = 0;
    let autoplayInterval;
    
    // Create dots
    if (dotsContainer && cards.length > 1) {
        cards.forEach((_, index) => {
            const dot = document.createElement('button');
            dot.className = `carousel-dot ${index === 0 ? 'active' : ''}`;
            dot.addEventListener('click', () => goToSlide(index));
            dotsContainer.appendChild(dot);
        });
    }
    
    function goToSlide(index) {
        currentIndex = index;
        const offset = -index * 100;
        const track = carousel.querySelector('.carousel-track');
        if (track) {
            track.style.transform = `translateX(${offset}%)`;
        }
        
        // Update dots
        const dots = dotsContainer?.querySelectorAll('.carousel-dot');
        dots?.forEach((dot, i) => {
            dot.classList.toggle('active', i === index);
        });
    }
    
    function nextSlide() {
        goToSlide((currentIndex + 1) % cards.length);
    }
    
    // Auto-play
    function startAutoplay() {
        autoplayInterval = setInterval(nextSlide, 5000);
    }
    
    function stopAutoplay() {
        clearInterval(autoplayInterval);
    }
    
    if (cards.length > 1) {
        startAutoplay();
        carousel.addEventListener('mouseenter', stopAutoplay);
        carousel.addEventListener('mouseleave', startAutoplay);
    }
}

/* ===== Recently Viewed Products ===== */
function initRecentlyViewed() {
    const container = document.getElementById('recently-viewed-products');
    if (!container) return;
    
    const recentlyViewed = getRecentlyViewed();
    
    if (recentlyViewed.length === 0) {
        container.closest('section')?.classList.add('d-none');
        return;
    }
    
    // Render products
    const productsHtml = recentlyViewed.map(product => `
        <div class="col-6 col-md-3">
            <div class="product-card h-100">
                <div class="product-image-wrapper">
                    <img src="${product.image}" alt="${product.name}" class="product-image">
                    <div class="product-actions">
                        <button class="action-btn add-to-cart-btn" data-product="${product.id}" data-action="add">
                            <i class="bi bi-cart-plus"></i>
                        </button>
                    </div>
                </div>
                <div class="product-info">
                    <span class="product-category">${product.category}</span>
                    <h5 class="product-name">
                        <a href="${product.url}">${product.name}</a>
                    </h5>
                    <div class="product-price-row">
                        <span class="product-price">UGX ${product.price.toLocaleString()}</span>
                    </div>
                </div>
            </div>
        </div>
    `).join('');
    
    container.innerHTML = productsHtml;
}

function getRecentlyViewed() {
    try {
        const data = localStorage.getItem(HomepageConfig.recentlyViewedKey);
        return data ? JSON.parse(data) : [];
    } catch (e) {
        return [];
    }
}

function addToRecentlyViewed(product) {
    let recentlyViewed = getRecentlyViewed();
    
    // Remove if already exists
    recentlyViewed = recentlyViewed.filter(p => p.id !== product.id);
    
    // Add to beginning
    recentlyViewed.unshift(product);
    
    // Keep only max items
    recentlyViewed = recentlyViewed.slice(0, HomepageConfig.maxRecentlyViewed);
    
    localStorage.setItem(HomepageConfig.recentlyViewedKey, JSON.stringify(recentlyViewed));
}

function trackProductView() {
    // Get product data from page if on product detail page
    const productData = document.querySelector('[data-product-view]');
    if (productData) {
        const product = {
            id: productData.dataset.productId,
            name: productData.dataset.productName,
            image: productData.dataset.productImage,
            price: parseInt(productData.dataset.productPrice),
            category: productData.dataset.productCategory,
            url: window.location.pathname
        };
        addToRecentlyViewed(product);
    }
}

/* ===== Product Recommendations ===== */
function initProductRecommendations() {
    const container = document.getElementById('recommended-products');
    if (!container) return;
    
    // Fetch recommendations based on browsing history
    const recentlyViewed = getRecentlyViewed();
    const categories = [...new Set(recentlyViewed.map(p => p.category))];
    
    if (categories.length === 0) return;
    
    // In production, this would be an API call
    // For now, we'll show the section with placeholder data
    fetchWithTimeout(`/api/recommendations/?categories=${categories.join(',')}`)
        .then(response => response.json())
        .then(data => {
            if (data.products && data.products.length > 0) {
                renderRecommendations(container, data.products);
            }
        })
        .catch(() => {
            // Silently fail - recommendations are not critical
        });
}

function renderRecommendations(container, products) {
    const productsHtml = products.map(product => `
        <div class="col-6 col-md-3">
            <div class="product-card h-100">
                <span class="product-badge badge-recommended">Recommended</span>
                <div class="product-image-wrapper">
                    <img src="${product.image}" alt="${product.name}" class="product-image">
                    <div class="product-actions">
                        <button class="action-btn add-to-cart-btn" data-product="${product.id}" data-action="add">
                            <i class="bi bi-cart-plus"></i>
                        </button>
                    </div>
                </div>
                <div class="product-info">
                    <span class="product-category">${product.category}</span>
                    <h5 class="product-name">
                        <a href="${product.url}">${product.name}</a>
                    </h5>
                    <div class="product-price-row">
                        <span class="product-price">UGX ${product.price.toLocaleString()}</span>
                    </div>
                </div>
            </div>
        </div>
    `).join('');
    
    container.innerHTML = productsHtml;
    container.closest('section')?.classList.remove('d-none');
}

/* ===== WhatsApp Widget ===== */
function initWhatsAppWidget() {
    const whatsappBtn = document.querySelector('.whatsapp-float');
    if (!whatsappBtn) return;
    
    // Show tooltip on first visit
    if (!localStorage.getItem('whatsapp_tooltip_shown')) {
        setTimeout(() => {
            showWhatsAppTooltip(whatsappBtn);
            localStorage.setItem('whatsapp_tooltip_shown', 'true');
        }, 3000);
    }
}

function showWhatsAppTooltip(button) {
    const tooltip = document.createElement('div');
    tooltip.className = 'whatsapp-tooltip';
    tooltip.innerHTML = `
        <span>Need help? Chat with us!</span>
        <button class="tooltip-close">&times;</button>
    `;
    button.parentNode.appendChild(tooltip);
    
    // Position tooltip
    tooltip.style.position = 'fixed';
    tooltip.style.bottom = '100px';
    tooltip.style.right = '90px';
    
    // Close button
    tooltip.querySelector('.tooltip-close').addEventListener('click', () => {
        tooltip.remove();
    });
    
    // Auto-hide after 5 seconds
    setTimeout(() => tooltip.remove(), 5000);
}

/* ===== Smooth Scroll ===== */
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href === '#') return;
            
            e.preventDefault();
            const target = document.querySelector(href);
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

/* ===== Utility Functions ===== */
function getCsrfToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
           document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1] ||
           window.csrftoken;
}

function showToast(message, type = 'info') {
    // Use existing toast function if available
    if (window.showToast) {
        window.showToast(message, type);
        return;
    }
    
    // Fallback toast implementation
    const toast = document.createElement('div');
    toast.className = `toast-notification toast-${type}`;
    toast.innerHTML = `
        <i class="bi bi-${type === 'success' ? 'check-circle' : type === 'error' ? 'x-circle' : 'info-circle'}"></i>
        <span>${message}</span>
    `;
    
    document.body.appendChild(toast);
    
    // Animate in
    setTimeout(() => toast.classList.add('show'), 10);
    
    // Remove after 4 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

/* ===== Bestseller Badge Animation ===== */
function animateBestsellerBadges() {
    const badges = document.querySelectorAll('.badge-bestseller');
    badges.forEach(badge => {
        badge.addEventListener('mouseenter', () => {
            badge.classList.add('pulse');
        });
        badge.addEventListener('mouseleave', () => {
            badge.classList.remove('pulse');
        });
    });
}

/* ===== Export for global access ===== */
window.Homepage = {
    addToRecentlyViewed: addToRecentlyViewed,
    showToast: showToast,
    getCsrfToken: getCsrfToken
};
