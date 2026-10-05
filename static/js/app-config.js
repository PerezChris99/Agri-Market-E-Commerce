(function () {
    'use strict';
    const body = document.body;
    window.isAuthenticated = body?.dataset.authenticated === 'true';
    function getCookie(name) {
        const prefix = name + '=';
        const cookies = document.cookie ? document.cookie.split(';') : [];
        for (const raw of cookies) {
            const cookie = raw.trim();
            if (cookie.startsWith(prefix)) return decodeURIComponent(cookie.slice(prefix.length));
        }
        return null;
    }
    window.csrftoken = getCookie('csrftoken');
    try {
        window.cart = JSON.parse(getCookie('cart') || '{}');
        if (!window.cart || typeof window.cart !== 'object' || Array.isArray(window.cart)) window.cart = {};
    } catch (_) { window.cart = {}; }
    window.fetchWithTimeout = async function (input, options = {}, timeout = 15000) {
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), timeout);
        try {
            return await fetch(input, { ...options, signal: controller.signal });
        } finally {
            clearTimeout(timer);
        }
    };

    window.setCartCookie = function (cart) {
        const secure = window.location.protocol === 'https:' ? '; Secure' : '';
        document.cookie = 'cart=' + encodeURIComponent(JSON.stringify(cart)) + '; Path=/; SameSite=Lax' + secure;
    };
}());
