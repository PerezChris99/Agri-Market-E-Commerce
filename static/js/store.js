(function () {
    'use strict';
    const select = document.getElementById('sort-select');
    if (!select) return;
    select.addEventListener('change', function () {
        const url = new URL(window.location.href);
        url.searchParams.set('sort', this.value);
        url.searchParams.delete('page');
        window.location.assign(url.toString());
    });
}());
