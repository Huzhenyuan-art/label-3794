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

const USER_TOKEN_KEY = 'portal_user_token';
const USER_CSRF_KEY = 'portal_user_csrf';

export function getUserAccessToken() {
  return localStorage.getItem(USER_TOKEN_KEY) || '';
}

export function getUserCsrfToken() {
  return localStorage.getItem(USER_CSRF_KEY) || '';
}

export function saveUserAuth(accessToken, csrfToken) {
  localStorage.setItem(USER_TOKEN_KEY, accessToken);
  localStorage.setItem(USER_CSRF_KEY, csrfToken);
}

export function clearUserAuth() {
  localStorage.removeItem(USER_TOKEN_KEY);
  localStorage.removeItem(USER_CSRF_KEY);
}
