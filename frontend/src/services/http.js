import axios from 'axios';
import { getAccessToken, getCsrfToken, getUserAccessToken, getUserCsrfToken } from './auth';

const http = axios.create({
  baseURL: '/',
  timeout: 20000,
});

http.interceptors.request.use((config) => {
  const url = config.url || '';
  const isUserApi = url.startsWith('/api/user/');

  let token;
  let csrf;
  if (isUserApi) {
    token = getUserAccessToken();
    csrf = getUserCsrfToken();
  } else {
    token = getAccessToken();
    csrf = getCsrfToken();
  }

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  const method = (config.method || 'get').toUpperCase();
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
    if (csrf) {
      config.headers['X-CSRF-Token'] = csrf;
    }
  }

  return config;
});

export function extractErrorMessage(error) {
  if (error?.response?.data?.message) {
    return error.response.data.message;
  }
  return '请求失败，请稍后重试';
}

export default http;
