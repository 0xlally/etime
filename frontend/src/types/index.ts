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

export interface SessionListItem {
  id: number;
  user_id: number;
  username?: string | null;
  category_id?: number | null;
  start_time: string;
  end_time?: string | null;
  duration_seconds?: number | null;
  note?: string | null;
  source: string;
  created_at: string;
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

export interface CategoryStatsSummaryItem {
  category_id: number | null;
  category_name: string | null;
  category_color: string | null;
  seconds: number;
}

export interface StatsSummary {
  total_seconds: number;
  by_category: CategoryStatsSummaryItem[];
}

export interface DayDetail {
  id: number;
  category_id: number | null;
  category_name: string | null;
  start_time: string;
  end_time: string;
  duration_seconds: number;
  note: string | null;
  source: string;
}

export interface HeatmapDay {
  date: string;
  total_seconds: number;
  sessions?: DayDetail[];
}

export interface WorkTarget {
  id: number;
  user_id: number;
  target_type?: 'daily' | 'weekly' | 'monthly' | 'tomorrow'; // Legacy field
  period?: 'daily' | 'weekly' | 'monthly' | 'tomorrow'; // New field matching backend
  target_seconds: number;
  category_ids?: number[]; // Legacy field
  include_category_ids?: number[]; // New field matching backend
  is_enabled?: boolean; // Legacy field
  is_active?: boolean; // New field matching backend
  effective_from?: string;
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

export interface PaginatedUsersResponse {
  total: number;
  page: number;
  page_size: number;
  users: AdminUser[];
}

export interface PaginatedSessionsResponse {
  total: number;
  page: number;
  page_size: number;
  sessions: SessionListItem[];
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
