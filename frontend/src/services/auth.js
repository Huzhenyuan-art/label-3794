const TOKEN_KEY = 'portal_admin_token';
const CSRF_KEY = 'portal_admin_csrf';

export function getAccessToken() {
  return localStorage.getItem(TOKEN_KEY) || '';
}

export function getCsrfToken() {
  return localStorage.getItem(CSRF_KEY) || '';
}

export function saveAuth(accessToken, csrfToken) {
  localStorage.setItem(TOKEN_KEY, accessToken);
  localStorage.setItem(CSRF_KEY, csrfToken);
}

export function clearAuth() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(CSRF_KEY);
}
