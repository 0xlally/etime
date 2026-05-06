import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import { Capacitor } from '@capacitor/core';

const TOKEN_KEY = 'etime_token';
const REFRESH_TOKEN_KEY = 'etime_refresh_token';

const normalizeBaseUrl = (baseUrl: string) => baseUrl.replace(/\/+$/, '');

const getApiBaseUrl = () => {
  const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim();
  const nativeBaseUrl = import.meta.env.VITE_NATIVE_API_BASE_URL?.trim();
  if (Capacitor.isNativePlatform() && nativeBaseUrl) {
    return normalizeBaseUrl(nativeBaseUrl);
  }

  if (configuredBaseUrl) {
    return normalizeBaseUrl(configuredBaseUrl);
  }

  return '/api/v1';
};

const API_BASE_URL = getApiBaseUrl();

interface RetryableRequestConfig extends InternalAxiosRequestConfig {
  _retry?: boolean;
}

class ApiClient {
  private client: AxiosInstance;
  private isRefreshing = false;
  private refreshPromise: Promise<string | null> | null = null;

  constructor() {
    this.client = axios.create({
      // 与后端 FastAPI 主路由前缀保持一致 (/api/v1)
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // 请求拦截器：自动添加 token
    this.client.interceptors.request.use(
      (config) => {
        const token = this.getToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // 响应拦截器：401 自动跳转登录
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as RetryableRequestConfig | undefined;

        if (error.response?.status !== 401 || !originalRequest) {
          return Promise.reject(error);
        }

        if (originalRequest.url?.includes('/auth/login') || originalRequest.url?.includes('/auth/refresh')) {
          this.clearAuth();
          window.location.href = '/login';
          return Promise.reject(error);
        }

        if (originalRequest._retry) {
          this.clearAuth();
          window.location.href = '/login';
          return Promise.reject(error);
        }

        originalRequest._retry = true;
        const newAccessToken = await this.refreshAccessToken();

        if (!newAccessToken) {
          this.clearAuth();
          window.location.href = '/login';
          return Promise.reject(error);
        }

        originalRequest.headers = originalRequest.headers ?? {};
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return this.client(originalRequest);
      }
    );
  }

  // Token 管理
  setToken(token: string) {
    localStorage.setItem(TOKEN_KEY, token);
  }

  setAuthTokens(accessToken: string, refreshToken: string) {
    localStorage.setItem(TOKEN_KEY, accessToken);
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  }

  getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  }

  getRefreshToken(): string | null {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  }

  removeToken() {
    localStorage.removeItem(TOKEN_KEY);
  }

  removeRefreshToken() {
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  }

  clearAuth() {
    this.removeToken();
    this.removeRefreshToken();
  }

  isAuthenticated(): boolean {
    return !!this.getToken();
  }

  private async refreshAccessToken(): Promise<string | null> {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) {
      return null;
    }

    if (this.isRefreshing && this.refreshPromise) {
      return this.refreshPromise;
    }

    this.isRefreshing = true;
    this.refreshPromise = (async () => {
      try {
        const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        });

        const newAccessToken = response.data?.access_token as string | undefined;
        const newRefreshToken = (response.data?.refresh_token as string | undefined) ?? refreshToken;

        if (!newAccessToken) {
          return null;
        }

        this.setAuthTokens(newAccessToken, newRefreshToken);
        return newAccessToken;
      } catch (_e) {
        return null;
      } finally {
        this.isRefreshing = false;
        this.refreshPromise = null;
      }
    })();

    return this.refreshPromise;
  }

  getUserRole(): string | null {
    const token = this.getToken();
    if (!token) return null;
    try {
      const base = token.split('.')[1];
      if (!base) return null;
      // Base64URL decode with padding
      let padded = base.replace(/-/g, '+').replace(/_/g, '/');
      while (padded.length % 4 !== 0) padded += '=';
      const payload = JSON.parse(atob(padded));
      return payload?.role ?? null;
    } catch (e) {
      return null;
    }
  }

  isAdmin(): boolean {
    return this.getUserRole() === 'admin';
  }

  // API 方法
  async get<T>(url: string, params?: any): Promise<T> {
    const response = await this.client.get<T>(url, { params });
    return response.data;
  }

  async post<T>(url: string, data?: any): Promise<T> {
    const response = await this.client.post<T>(url, data);
    return response.data;
  }

  async patch<T>(url: string, data?: any): Promise<T> {
    const response = await this.client.patch<T>(url, data);
    return response.data;
  }

  async delete<T>(url: string): Promise<T> {
    const response = await this.client.delete<T>(url);
    return response.data;
  }
}

export const apiClient = new ApiClient();
