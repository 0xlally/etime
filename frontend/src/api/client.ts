import axios, { AxiosInstance, AxiosError } from 'axios';

const TOKEN_KEY = 'etime_token';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      // 与后端 FastAPI 主路由前缀保持一致 (/api/v1)
      baseURL: '/api/v1',
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
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          this.removeToken();
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Token 管理
  setToken(token: string) {
    localStorage.setItem(TOKEN_KEY, token);
  }

  getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  }

  removeToken() {
    localStorage.removeItem(TOKEN_KEY);
  }

  isAuthenticated(): boolean {
    return !!this.getToken();
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
