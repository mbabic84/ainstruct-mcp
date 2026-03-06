(function() {
    let isRefreshing = false;
    let refreshPromise = null;

    window.__getTokenExpiry = function() {
        const token = localStorage.getItem('access_token');
        if (!token) return null;
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            return payload.exp * 1000;
        } catch (e) {
            return null;
        }
    }

    async function refreshToken() {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) {
            return null;
        }

        try {
            const response = await fetch('/api/v1/auth/refresh', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh_token: refreshToken })
            });

            if (response.ok) {
                const data = await response.json();
                localStorage.setItem('access_token', data.access_token);
                localStorage.setItem('refresh_token', data.refresh_token);
                return data.access_token;
            }
        } catch (e) {
            console.error('Token refresh failed:', e);
        }
        return null;
    }

    window.__forceRefreshToken = async function() {
        const expiry = window.__getTokenExpiry();
        const now = Date.now();
        const buffer = 5 * 60 * 1000;

        if (expiry && now < expiry - buffer) {
            return localStorage.getItem('access_token');
        }

        return await refreshToken();
    };

    window.__getAccessToken = function() {
        return localStorage.getItem('access_token');
    };

    function checkAuthRedirect() {
        const token = localStorage.getItem('access_token');
        const path = window.location.pathname;
        if (token && (path === '/login' || path === '/register' || path === '/')) {
            window.location.href = '/dashboard';
        }
    }
    window.addEventListener('DOMContentLoaded', checkAuthRedirect);

    function setupTabUrlUpdate() {
        if (window.location.pathname === '/tokens') {
            const observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    if (mutation.type === 'childList') {
                        mutation.addedNodes.forEach(function(node) {
                            if (node.nodeType === 1) {
                                const tabs = node.querySelector ? node.querySelector('.q-tab') : null;
                                if (tabs) {
                                    const tabButtons = document.querySelectorAll('.q-tab');
                                    tabButtons.forEach(function(tab) {
                                        tab.addEventListener('click', function() {
                                            const isCat = tab.textContent.includes('Collection');
                                            const newUrl = isCat ? '/tokens?tab=cat' : '/tokens?tab=pat';
                                            window.history.replaceState({}, '', newUrl);
                                        });
                                    });
                                    observer.disconnect();
                                }
                            }
                        });
                    }
                });
            });
            observer.observe(document.body, { childList: true, subtree: true });
        }
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setupTabUrlUpdate);
    } else {
        setupTabUrlUpdate();
    }
})();
