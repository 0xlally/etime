// 类型定义
export interface User {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  role: 'user' | 'admin';
  created_at: string;
}

export interface Category {
  id: number;
  user_id: number;
  name: string;
  color: string;
  created_at: string;
}

export interface Session {
  id: number;
  user_id: number;
  category_id: number;
  start_time: string;
  end_time?: string;
  duration_seconds?: number;
  note?: string;
  created_at: string;
  category?: Category;
}

export interface DailyStats {
  date: string;
  total_seconds: number;
  by_category: Array<{
    category_id: number;
    category_name: string;
    category_color: string;
    seconds: number;
  }>;
}

export interface HeatmapDay {
  date: string;
  total_seconds: number;
  sessions?: Session[];
}

export interface WorkTarget {
  id: number;
  user_id: number;
  target_type: 'daily' | 'weekly' | 'monthly';
  target_seconds: number;
  category_ids: number[];
  is_enabled: boolean;
  created_at: string;
}

export interface WorkEvaluation {
  id: number;
  user_id: number;
  target_id: number;
  evaluation_date: string;
  actual_seconds: number;
  is_pass: boolean;
  created_at: string;
  target?: WorkTarget;
}

export interface AdminUser {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  role: string;
  created_at: string;
}

export interface AuditLog {
  id: number;
  admin_user_id: number;
  action: string;
  target_type: string;
  target_id: number;
  detail_json: Record<string, any>;
  created_at: string;
}

export interface PaginatedResponse<T> {
  total: number;
  page: number;
  page_size: number;
  data: T[];
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}
