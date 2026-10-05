/**
 * Checkout Page JavaScript
 * Agri-Market Uganda - External JS
 * Handles payment processing, form validation, and order submission
 */

(function() {
    'use strict';

    const page = document.getElementById('checkout-page');
    const checkoutData = {
        total: Number(page?.dataset.total || 0),
        shipping: page?.dataset.shipping === 'true',
        storeUrl: page?.dataset.storeUrl || '/shop/',
        userInfo: {
            name: page?.dataset.userName || '',
            email: page?.dataset.userEmail || ''
        }
    };
    const total = checkoutData.total;
    const shipping = checkoutData.shipping;
    const csrftoken = window.csrftoken || ''; 
    const userInfo = checkoutData.userInfo;

    // Convert UGX to USD (approximate rate for PayPal)
    const usdTotal = (total / 3700).toFixed(2);
    let selectedPaymentMethod = null;

    // DOM Elements
    const form = document.getElementById('checkout-form');
    const formButton = document.getElementById('form-button');
    const paymentInfo = document.getElementById('payment-info');
    const momoPhoneInput = document.getElementById('momo-phone');
    const phoneInput = document.getElementById('phone');

    if (!form || !formButton || !paymentInfo) {
        console.error('Required checkout elements not found');
        return;
    }

    // Initialize checkout
    function init() {
        setupFormSubmission();
        setupPaymentMethodSelection();
        setupMomoPhoneValidation();
        setupPhoneSync();
        setupPaypalButtons();
        setupCodButton();
    }

    // Copy shipping phone to MoMo phone by default
    function setupPhoneSync() {
        if (phoneInput && momoPhoneInput) {
            phoneInput.addEventListener('input', function() {
                momoPhoneInput.value = this.value;
                validateMomoPhone();
            });
        }
    }

    // Form submission - show payment
    function setupFormSubmission() {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Validate form
            if (!form.checkValidity()) {
                form.reportValidity();
                return;
            }
            
            formButton.classList.add('d-none');
            paymentInfo.classList.remove('d-none');
            
            // Copy phone to MoMo
            if (momoPhoneInput && phoneInput) {
                momoPhoneInput.value = phoneInput.value;
                validateMomoPhone();
            }
            
            // Scroll to payment section
            paymentInfo.scrollIntoView({ behavior: 'smooth' });
        });
    }

    // Payment Method Selection
    function setupPaymentMethodSelection() {
        document.querySelectorAll('input[name="payment_method"]').forEach(function(input) {
            input.addEventListener('change', function() {
                selectedPaymentMethod = this.value;
                
                // Update UI
                document.querySelectorAll('.payment-card').forEach(function(card) {
                    card.classList.remove('border-success', 'bg-success-subtle');
                    const check = card.querySelector('.payment-check');
                    if (check) check.classList.add('d-none');
                });
                
                const selectedCard = this.nextElementSibling;
                if (selectedCard) {
                    selectedCard.classList.add('border-success', 'bg-success-subtle');
                    const check = selectedCard.querySelector('.payment-check');
                    if (check) check.classList.remove('d-none');
                }
                
                // Show/hide appropriate section
                hideAllPaymentSections();
                
                if (this.value === 'mtn' || this.value === 'airtel') {
                    showSection('momo-phone-section');
                    validateMomoPhone();
                } else if (this.value === 'paypal') {
                    showSection('paypal-section');
                } else if (this.value === 'cod') {
                    showSection('cod-section');
                }
            });
        });
    }

    function hideAllPaymentSections() {
        ['momo-phone-section', 'paypal-section', 'cod-section', 'payment-processing'].forEach(function(id) {
            const el = document.getElementById(id);
            if (el) el.classList.add('d-none');
        });
    }

    function showSection(id) {
        const el = document.getElementById(id);
        if (el) el.classList.remove('d-none');
    }

    // MoMo phone validation
    function setupMomoPhoneValidation() {
        if (momoPhoneInput) {
            momoPhoneInput.addEventListener('input', validateMomoPhone);
        }
    }

    function validateMomoPhone() {
        if (!momoPhoneInput) return;
        
        const phone = momoPhoneInput.value.replace(/\s/g, '');
        const hint = document.getElementById('momo-provider-hint');
        const payBtn = document.getElementById('momo-pay-btn');
        
        if (!hint || !payBtn) return;
        
        if (phone.length === 9) {
            const mtnPrefixes = ['076', '077', '078'];
            const airtelPrefixes = ['070', '074', '075'];
            
            if (mtnPrefixes.some(p => phone.startsWith(p))) {
                hint.textContent = 'MTN Mobile Money number detected';
                payBtn.disabled = false;
                payBtn.className = 'btn btn-warning btn-lg w-100';
            } else if (airtelPrefixes.some(p => phone.startsWith(p))) {
                hint.textContent = 'Airtel Money number detected';
                payBtn.disabled = false;
                payBtn.className = 'btn btn-danger btn-lg w-100';
            } else {
                hint.textContent = 'Unknown mobile network';
                payBtn.disabled = true;
            }
        } else {
            hint.textContent = 'Enter 9 digits (e.g., 772 123 456)';
            payBtn.disabled = true;
        }
    }

    // Mobile Money Payment
    function setupMomoPayment() {
        const momoPayBtn = document.getElementById('momo-pay-btn');
        if (!momoPayBtn) return;

        momoPayBtn.addEventListener('click', function() {
            const phone = '256' + momoPhoneInput.value.replace(/\s/g, '');
            
            // Show processing
            hideAllPaymentSections();
            showSection('payment-processing');
            updatePaymentStatus('Sending payment request to ' + phone + '...');
            
            // Initiate Mobile Money Payment
            fetchWithTimeout('/api/momo/initiate/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken,
                },
                body: JSON.stringify({
                    'phone': phone,
                    'amount': total,
                    'provider': selectedPaymentMethod
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updatePaymentStatus('Payment prompt sent! Please check your phone and enter your PIN.');
                    pollPaymentStatus(data.payment_id, data.reference);
                } else {
                    hideAllPaymentSections();
                    showSection('momo-phone-section');
                    showToast('Error: ' + data.message, 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                hideAllPaymentSections();
                showSection('momo-phone-section');
                showToast('An error occurred. Please try again.', 'error');
            });
        });
    }

    function pollPaymentStatus(paymentId, reference) {
        let pollCount = 0;
        const maxPolls = 60; // 2 minutes max
        
        const pollInterval = setInterval(function() {
            pollCount++;
            
            fetchWithTimeout('/api/momo/status/?payment_id=' + paymentId)
            .then(response => response.json())
            .then(data => {
                if (data.status === 'successful') {
                    clearInterval(pollInterval);
                    submitFormData(reference, selectedPaymentMethod);
                } else if (data.status === 'failed') {
                    clearInterval(pollInterval);
                    hideAllPaymentSections();
                    showSection('momo-phone-section');
                    showToast('Payment failed: ' + (data.message || 'Transaction declined'), 'error');
                } else if (pollCount >= maxPolls) {
                    clearInterval(pollInterval);
                    hideAllPaymentSections();
                    showSection('momo-phone-section');
                    showToast('Payment timed out. Please try again.', 'error');
                } else {
                    updatePaymentStatus('Waiting for confirmation... (' + pollCount + 's)');
                }
            })
            .catch(error => {
                console.error('Poll error:', error);
            });
        }, 2000);
    }

    // Cash on Delivery
    function setupCodButton() {
        const codBtn = document.getElementById('cod-btn');
        if (codBtn) {
            codBtn.addEventListener('click', function() {
                submitFormData('COD-' + Date.now(), 'cod');
            });
        }
    }

    // PayPal Buttons
    function setupPaypalButtons() {
        if (typeof paypal === 'undefined') {
            console.warn('PayPal SDK not loaded');
            return;
        }

        paypal.Buttons({
            style: {
                shape: 'pill',
                color: 'gold',
                layout: 'vertical',
                label: 'pay'
            },

            createOrder: function(data, actions) {
                return actions.order.create({
                    purchase_units: [{
                        amount: {
                            value: usdTotal
                        },
                        description: 'Agri-Market Order'
                    }]
                });
            },

            onApprove: function(data, actions) {
                return actions.order.capture().then(function(details) {
                    submitFormData(details.id, 'paypal');
                });
            },

            onError: function(err) {
                console.error('PayPal Error:', err);
                showToast('Payment failed. Please try again.', 'error');
            }
        }).render('#paypal-button-container');
    }

    function submitFormData(transactionId, paymentMethod) {
        showSection('payment-processing');
        updatePaymentStatus('Creating your order...');
        
        const formData = {
            'name': document.getElementById('name')?.value || userInfo.name || '',
            'email': document.getElementById('email')?.value || userInfo.email || '',
            'total': total,
        };

        const shippingData = {
            'phone': '256' + (phoneInput?.value || '').replace(/\s/g, ''),
            'address': document.getElementById('address')?.value || '',
            'city': document.getElementById('city')?.value || '',
            'region': document.getElementById('region')?.value || '',
            'zipcode': document.getElementById('zipcode')?.value || '',
            'country': document.getElementById('country')?.value || 'Uganda',
            'landmark': document.getElementById('landmark')?.value || '',
        };

        fetchWithTimeout('/process_order/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken,
            },
            body: JSON.stringify({
                'form': formData,
                'shipping': shippingData,
                'transaction_id': transactionId,
                'payment_method': paymentMethod
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Clear cart cookie
                if (window.setCartCookie) window.setCartCookie({});;
                
                // Show success
                updatePaymentStatus(
                    '<i class="bi bi-check-circle-fill text-success me-2"></i>Order placed successfully! Order ID: <strong>' + data.order_id + '</strong>'
                );
                
                showToast('Order placed successfully! Redirecting...', 'success');
                
                setTimeout(function() {
                    window.location.href = checkoutData.storeUrl + '?order=' + data.order_id;
                }, 2000);
            } else {
                hideAllPaymentSections();
                showToast('Error: ' + data.message, 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            hideAllPaymentSections();
            showToast('An error occurred. Please try again.', 'error');
        });
    }

    function updatePaymentStatus(message) {
        const statusEl = document.getElementById('payment-status-msg');
        if (statusEl) {
            statusEl.textContent = String(message || '');
        }
    }

    function showToast(message, type) {
        const wrapper = document.createElement('div');
        wrapper.className = 'position-fixed bottom-0 end-0 p-3 checkout-toast';
        wrapper.style.zIndex = '1100';

        const toast = document.createElement('div');
        toast.className = 'toast show align-items-center text-white ' +
            (type === 'error' ? 'bg-danger' : 'bg-success');
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');

        const row = document.createElement('div');
        row.className = 'd-flex';

        const body = document.createElement('div');
        body.className = 'toast-body';
        body.textContent = String(message || '');

        const close = document.createElement('button');
        close.type = 'button';
        close.className = 'btn-close btn-close-white me-2 m-auto';
        close.setAttribute('aria-label', 'Close');

        row.append(body, close);
        toast.appendChild(row);
        wrapper.appendChild(toast);
        document.body.appendChild(wrapper);

        close.addEventListener('click', () => wrapper.remove());
        setTimeout(() => wrapper.remove(), 5000);
    }


    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            init();
            setupMomoPayment();
        });
    } else {
        init();
        setupMomoPayment();
    }
})();
