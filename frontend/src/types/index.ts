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
  color?: string | null;
  is_archived?: boolean;
  created_at: string;
}

export interface Session {
  id: number;
  user_id: number;
  category_id: number;
  start_time: string;
  end_time?: string;
  duration_seconds?: number;
  effective_seconds?: number;
  effectiveness_multiplier?: number;
  note?: string;
  client_generated_id?: string | null;
  created_at: string;
  category?: Category;
}

export interface ActiveSession {
  id: number;
  user_id: number;
  category_id?: number | null;
  start_time: string;
  note?: string | null;
  client_generated_id?: string | null;
  elapsed_seconds: number;
}

export interface QuickStartTemplate {
  id: number;
  user_id: number;
  title: string;
  category_id: number;
  category_name?: string | null;
  duration_seconds?: number | null;
  note_template?: string | null;
  sort_order: number;
  color?: string | null;
  icon?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface QuickStartStartResponse {
  template: QuickStartTemplate;
  session: Session;
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

export interface TimeTraceEntry {
  id: number;
  user_id: number;
  content: string;
  created_at: string;
}

export interface DayDetail {
  id: number;
  category_id: number | null;
  category_name: string | null;
  start_time: string;
  end_time: string;
  duration_seconds: number;
  effective_seconds?: number;
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
  updated_at?: string;
}

export interface WorkEvaluation {
  id: number;
  user_id: number;
  target_id: number;
  period_start: string;
  period_end: string;
  actual_seconds: number;
  target_seconds: number;
  status: 'met' | 'missed';
  deficit_seconds: number;
  created_at: string;
  target?: WorkTarget;
}

export interface TargetMetric {
  target_id: number;
  period: 'daily' | 'weekly' | 'monthly' | 'tomorrow';
  target_seconds: number;
  current_streak: number;
  best_streak: number;
  total_evaluations: number;
  met_evaluations: number;
  completion_rate: number;
  active_debt_seconds: number;
  suggested_compensation_seconds: number;
}

export interface TargetProgress {
  target_id: number;
  period: 'daily' | 'weekly' | 'monthly' | 'tomorrow';
  period_start: string;
  period_end: string;
  actual_seconds: number;
  target_seconds: number;
  remaining_seconds: number;
  progress_ratio: number;
}

export interface PunishmentEvent {
  id: number;
  user_id: number;
  evaluation_id: number;
  rule_type: 'time_debt' | 'compensation' | string;
  payload_json?: Record<string, any> | null;
  created_at: string;
}

export interface TargetDashboard {
  metrics: TargetMetric[];
  progress: TargetProgress[];
  events: PunishmentEvent[];
}

export interface NotificationItem {
  id: number;
  user_id: number;
  type: string;
  title: string;
  content?: string | null;
  created_at: string;
  read_at?: string | null;
}

export type GroupRole = 'owner' | 'admin' | 'member';
export type GroupVisibility = 'private' | 'invite_code';
export type GroupMessageType = 'text' | 'status_share' | 'card_share' | 'system';

export interface Group {
  id: number;
  name: string;
  description?: string | null;
  owner_id: number;
  invite_code: string;
  visibility: GroupVisibility;
  created_at: string;
  updated_at: string;
  member_count: number;
  my_role?: GroupRole | null;
}

export interface GroupMember {
  id: number;
  group_id: number;
  user_id: number;
  username: string;
  role: GroupRole;
  joined_at: string;
  muted_until?: string | null;
  is_active: boolean;
}

export interface GroupStatusMetadata {
  date?: string;
  total_seconds?: number;
  target_completed_count?: number;
  target_total_count?: number;
  streak_days?: number;
  top_category?: {
    category_id: number | null;
    category_name: string | null;
    category_color: string | null;
    seconds: number;
  } | null;
  by_category?: CategoryStatsSummaryItem[];
}

export interface GroupMessage {
  id: number;
  group_id: number;
  user_id: number;
  username: string;
  message_type: GroupMessageType;
  content: string;
  metadata_json?: GroupStatusMetadata & Record<string, unknown> | null;
  created_at: string;
  deleted_at?: string | null;
}

export interface ReviewCategoryItem {
  category_id: number | null;
  category_name: string | null;
  category_color: string | null;
  seconds: number;
  trend_delta_seconds: number;
}

export interface ReviewEvaluationItem {
  id: number;
  target_id: number;
  period: string;
  period_start: string;
  period_end: string;
  actual_seconds: number;
  target_seconds: number;
  status: 'met' | 'missed';
  deficit_seconds: number;
}

export interface ReviewTargetSummary {
  total_count: number;
  met_count: number;
  missed_count: number;
  remaining_seconds: number;
  evaluations: ReviewEvaluationItem[];
}

export interface ReviewDayTotal {
  date: string;
  total_seconds: number;
}

export interface DailyReview {
  date: string;
  total_seconds: number;
  top_category: ReviewCategoryItem | null;
  by_category: ReviewCategoryItem[];
  target_summary: ReviewTargetSummary;
  time_traces: TimeTraceEntry[];
  markdown: string;
}

export interface WeeklyReview {
  start_date: string;
  end_date: string;
  total_seconds: number;
  average_daily_seconds: number;
  best_day: ReviewDayTotal | null;
  gap_days: number;
  by_category: ReviewCategoryItem[];
  daily_totals: ReviewDayTotal[];
  target_summary: ReviewTargetSummary;
  time_traces: TimeTraceEntry[];
  markdown: string;
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
  refresh_token: string;
  token_type: string;
}
