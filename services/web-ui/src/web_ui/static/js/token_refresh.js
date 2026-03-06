(function() {
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
        if (refreshPromise) {
            console.log('Token refresh already in progress, joining...');
            return refreshPromise;
        }

        console.log('Starting token refresh...');
        refreshPromise = (async () => {
            const refreshToken = localStorage.getItem('refresh_token');
            if (!refreshToken) {
                console.log('No refresh token found in storage');
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
                    console.log('Token refresh successful');
                    localStorage.setItem('access_token', data.access_token);
                    localStorage.setItem('refresh_token', data.refresh_token);
                    return data.access_token;
                } else {
                    console.warn('Token refresh failed:', response.status);
                    if (response.status === 401 || response.status === 403) {
                        localStorage.removeItem('access_token');
                        localStorage.removeItem('refresh_token');
                    }
                    return null;
                }
            } catch (e) {
                console.error('Token refresh network error:', e);
                return null;
            } finally {
                refreshPromise = null;
            }
        })();

        return refreshPromise;
    }

    window.__forceRefreshToken = async function() {
        const expiry = window.__getTokenExpiry();
        const now = Date.now();
        const buffer = 5 * 60 * 1000; // 5 minutes

        if (expiry && now < expiry - buffer) {
            console.log('Token still valid, expiry:', new Date(expiry).toISOString());
            return localStorage.getItem('access_token');
        }

        console.log('Token expired or expiring soon, forcing refresh...');
        return await refreshToken();
    };

    window.__getAccessToken = function() {
        return localStorage.getItem('access_token');
    };

    function checkAuthRedirect() {
        const token = localStorage.getItem('access_token');
        const expiry = window.__getTokenExpiry();
        
        // If token is expired, clear it
        if (token && expiry && Date.now() > expiry) {
            console.log('Token expired on load, clearing storage');
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            return;
        }

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
