import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  addDays,
  addMonths,
  addWeeks,
  eachDayOfInterval,
  endOfMonth,
  endOfWeek,
  format,
  isSameDay,
  startOfMonth,
  startOfWeek,
  subMonths,
  subWeeks,
} from 'date-fns';
import { useNavigate } from 'react-router-dom';
import { Capacitor } from '@capacitor/core';
import {
  Bell,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Clock,
  Play,
  Plus,
  RotateCcw,
  XCircle,
} from 'lucide-react';
import { apiClient } from '../api/client';
import {
  ActiveSession,
  CalendarTask,
  CalendarTaskPayload,
  CalendarTaskPriority,
  CalendarTaskStatus,
  Category,
  TargetDashboard,
  WorkEvaluation,
  WorkTarget,
} from '../types';
import { getRunningTimer } from '../utils/offlineTimer';
import { Button, Card, EmptyState, LoadingState, PageShell, SectionHeader, StatCard } from '../components/ui';

type PlannerView = 'month' | 'week' | 'day';
type TargetPeriod = 'daily' | 'weekly' | 'monthly' | 'tomorrow';

interface TaskFormState {
  title: string;
  description: string;
  category_id: string;
  priority: CalendarTaskPriority;
  estimated_minutes: string;
  date: string;
  start_time: string;
  end_time: string;
  reminder_enabled: boolean;
  reminder_minutes_before: string;
}

const priorityLabels: Record<CalendarTaskPriority, string> = {
  low: '低',
  medium: '中',
  high: '高',
};

const statusLabels: Record<CalendarTaskStatus, string> = {
  unscheduled: '待安排',
  scheduled: '已安排',
  done: '完成',
  cancelled: '取消',
};

const reminderOptions = [5, 10, 15, 30, 60];

const emptyForm = (date = format(new Date(), 'yyyy-MM-dd')): TaskFormState => ({
  title: '',
  description: '',
  category_id: '',
  priority: 'medium',
  estimated_minutes: '',
  date,
  start_time: '',
  end_time: '',
  reminder_enabled: true,
  reminder_minutes_before: '10',
});

const toLocalDateTimeInput = (value?: string | null) => {
  if (!value) return { date: '', time: '' };
  const date = new Date(value);
  return {
    date: format(date, 'yyyy-MM-dd'),
    time: format(date, 'HH:mm'),
  };
};

const combineLocalDateTime = (date: string, time: string) => {
  if (!date || !time) return null;
  return new Date(`${date}T${time}:00`).toISOString();
};

const formatTime = (seconds?: number | null) => {
  if (seconds === undefined || seconds === null) return '未估算';
  const total = Math.max(0, Math.floor(seconds));
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  if (hours === 0) return `${minutes} 分钟`;
  if (minutes === 0) return `${hours} 小时`;
  return `${hours} 小时 ${minutes} 分钟`;
};

const taskDateKey = (task: CalendarTask) => (
  task.scheduled_start ? format(new Date(task.scheduled_start), 'yyyy-MM-dd') : ''
);

const taskTimeLabel = (task: CalendarTask) => {
  if (!task.scheduled_start || !task.scheduled_end) return '未安排';
  return `${format(new Date(task.scheduled_start), 'HH:mm')} - ${format(new Date(task.scheduled_end), 'HH:mm')}`;
};

const toLocalInputValue = (date: Date) => {
  const copy = new Date(date);
  copy.setMinutes(copy.getMinutes() - copy.getTimezoneOffset());
  return copy.toISOString().slice(0, 16);
};

const tomorrowStartInputValue = () => {
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  tomorrow.setHours(0, 0, 0, 0);
  return toLocalInputValue(tomorrow);
};

const periodLabel = (period: string) => {
  if (period === 'tomorrow') return '明日计划';
  if (period === 'daily') return '每日';
  if (period === 'weekly') return '每周';
  if (period === 'monthly') return '每月';
  return period;
};

export const Planner: React.FC = () => {
  const navigate = useNavigate();
  const nativePlatform = Capacitor.isNativePlatform();
  const firedReminderIds = useRef<Set<number>>(new Set());
  const [view, setView] = useState<PlannerView>('month');
  const [anchorDate, setAnchorDate] = useState(new Date());
  const [tasks, setTasks] = useState<CalendarTask[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [targets, setTargets] = useState<WorkTarget[]>([]);
  const [evaluations, setEvaluations] = useState<WorkEvaluation[]>([]);
  const [targetDashboard, setTargetDashboard] = useState<TargetDashboard | null>(null);
  const [loading, setLoading] = useState(false);
  const [targetLoading, setTargetLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [targetFormOpen, setTargetFormOpen] = useState(false);
  const [editingTask, setEditingTask] = useState<CalendarTask | null>(null);
  const [form, setForm] = useState<TaskFormState>(emptyForm());
  const [targetForm, setTargetForm] = useState({
    target_type: 'daily' as TargetPeriod,
    target_seconds: 3600,
    category_ids: [] as number[],
    effective_from: toLocalInputValue(new Date()),
  });
  const [toast, setToast] = useState('');

  const range = useMemo(() => {
    if (view === 'day') {
      return { start: anchorDate, end: anchorDate };
    }
    if (view === 'week') {
      return {
        start: startOfWeek(anchorDate, { weekStartsOn: 1 }),
        end: endOfWeek(anchorDate, { weekStartsOn: 1 }),
      };
    }
    return {
      start: startOfMonth(anchorDate),
      end: endOfMonth(anchorDate),
    };
  }, [anchorDate, view]);

  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [range.start, range.end]);

  useEffect(() => {
    loadTargetData();
  }, []);

  useEffect(() => {
    void checkDueReminders();
    const timer = window.setInterval(() => {
      void checkDueReminders();
    }, 60_000);

    return () => window.clearInterval(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [taskData, categoryData] = await Promise.all([
        apiClient.get<CalendarTask[]>('/calendar-tasks', {
          start: range.start.toISOString(),
          end: range.end.toISOString(),
          include_unscheduled: true,
        }),
        apiClient.get<Category[]>('/categories'),
      ]);
      setTasks(taskData);
      setCategories(categoryData);
    } catch (error) {
      console.error('加载计划失败', error);
      setToast('计划加载失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  const loadTargetData = async () => {
    setTargetLoading(true);
    try {
      const [targetData, evaluationData, dashboardData] = await Promise.all([
        apiClient.get<WorkTarget[]>('/targets'),
        apiClient.get<WorkEvaluation[]>('/evaluations'),
        apiClient.get<TargetDashboard>('/targets/dashboard'),
      ]);
      setTargets(targetData);
      setEvaluations(evaluationData);
      setTargetDashboard(dashboardData);
    } catch (error) {
      console.error('加载目标数据失败', error);
      setToast('目标数据加载失败');
    } finally {
      setTargetLoading(false);
    }
  };

  const notifyTask = async (task: CalendarTask) => {
    if (firedReminderIds.current.has(task.id)) return;
    firedReminderIds.current.add(task.id);

    const body = `${taskTimeLabel(task)} · ${task.title}`;
    let shown = false;

    if ('Notification' in window) {
      const permission = Notification.permission === 'default'
        ? await Notification.requestPermission()
        : Notification.permission;
      if (permission === 'granted') {
        new Notification('ETime 计划提醒', { body });
        shown = true;
      }
    }

    // TODO: If @capacitor/local-notifications is added later, schedule native
    // notifications at create/update time. The foreground fallback keeps Android
    // usable while the app is open.
    if (!shown || nativePlatform) {
      setToast(`提醒：${body}`);
    }

    await apiClient.post(`/calendar-tasks/${task.id}/reminder-fired`);
    await loadData();
  };

  const checkDueReminders = async () => {
    try {
      const due = await apiClient.get<CalendarTask[]>('/calendar-tasks/reminders/due');
      for (const task of due) {
        await notifyTask(task);
      }
    } catch (error) {
      console.error('检查提醒失败', error);
    }
  };

  const scheduledTasks = tasks.filter((task) => task.scheduled_start && task.status !== 'cancelled');
  const unscheduledTasks = tasks.filter((task) => task.status === 'unscheduled');
  const todayTasks = scheduledTasks.filter((task) => isSameDay(new Date(task.scheduled_start!), new Date()));

  const scheduledByDate = useMemo(() => {
    const map = new Map<string, CalendarTask[]>();
    scheduledTasks.forEach((task) => {
      const key = taskDateKey(task);
      map.set(key, [...(map.get(key) ?? []), task]);
    });
    return map;
  }, [scheduledTasks]);

  const todaySummary = {
    total: todayTasks.length,
    done: todayTasks.filter((task) => task.status === 'done').length,
    focusSeconds: todayTasks.reduce((sum, task) => sum + (task.estimated_seconds || 0), 0),
  };

  const metricByTarget = useMemo(() => {
    const map = new Map<number, TargetDashboard['metrics'][number]>();
    targetDashboard?.metrics.forEach((metric) => map.set(metric.target_id, metric));
    return map;
  }, [targetDashboard]);

  const targetById = useMemo(() => {
    const map = new Map<number, WorkTarget>();
    targets.forEach((target) => map.set(target.id, target));
    return map;
  }, [targets]);

  const targetOverview = useMemo(() => {
    const metrics = targetDashboard?.metrics ?? [];
    const totalEvaluations = metrics.reduce((sum, item) => sum + item.total_evaluations, 0);
    const metEvaluations = metrics.reduce((sum, item) => sum + item.met_evaluations, 0);
    return {
      currentStreak: Math.max(0, ...metrics.map((item) => item.current_streak)),
      bestStreak: Math.max(0, ...metrics.map((item) => item.best_streak)),
      completionRate: totalEvaluations === 0 ? 0 : metEvaluations / totalEvaluations,
      activeDebt: metrics.reduce((sum, item) => sum + item.active_debt_seconds, 0),
    };
  }, [targetDashboard]);

  const openCreate = (date = anchorDate) => {
    setEditingTask(null);
    setForm(emptyForm(format(date, 'yyyy-MM-dd')));
    setModalOpen(true);
  };

  const handleTargetPeriodChange = (period: TargetPeriod) => {
    setTargetForm((prev) => ({
      ...prev,
      target_type: period,
      effective_from: period === 'tomorrow' ? tomorrowStartInputValue() : prev.effective_from,
    }));
  };

  const openEdit = (task: CalendarTask) => {
    const start = toLocalDateTimeInput(task.scheduled_start);
    const end = toLocalDateTimeInput(task.scheduled_end);
    setEditingTask(task);
    setForm({
      title: task.title,
      description: task.description ?? '',
      category_id: task.category_id ? String(task.category_id) : '',
      priority: task.priority,
      estimated_minutes: task.estimated_seconds ? String(Math.round(task.estimated_seconds / 60)) : '',
      date: start.date || format(anchorDate, 'yyyy-MM-dd'),
      start_time: start.time,
      end_time: end.time,
      reminder_enabled: task.reminder_enabled,
      reminder_minutes_before: String(task.reminder_minutes_before ?? 10),
    });
    setModalOpen(true);
  };

  const buildPayload = (): CalendarTaskPayload | null => {
    const title = form.title.trim();
    if (!title) {
      alert('请输入事项标题');
      return null;
    }

    const hasAnySchedule = Boolean(form.start_time || form.end_time);
    const hasFullSchedule = Boolean(form.date && form.start_time && form.end_time);
    if (hasAnySchedule && !hasFullSchedule) {
      alert('安排时间需要同时填写日期、开始和结束时间');
      return null;
    }

    const start = hasFullSchedule ? combineLocalDateTime(form.date, form.start_time) : null;
    const end = hasFullSchedule ? combineLocalDateTime(form.date, form.end_time) : null;
    if (start && end && new Date(end) <= new Date(start)) {
      alert('结束时间必须晚于开始时间');
      return null;
    }

    const estimatedMinutes = form.estimated_minutes === '' ? null : Number(form.estimated_minutes);
    if (estimatedMinutes !== null && (!Number.isFinite(estimatedMinutes) || estimatedMinutes < 1)) {
      alert('预计耗时至少 1 分钟');
      return null;
    }

    return {
      title,
      description: form.description.trim() || null,
      category_id: form.category_id ? Number(form.category_id) : null,
      priority: form.priority,
      estimated_seconds: estimatedMinutes === null ? null : Math.round(estimatedMinutes * 60),
      scheduled_start: start,
      scheduled_end: end,
      status: start && end ? 'scheduled' : 'unscheduled',
      reminder_enabled: Boolean(start && end && form.reminder_enabled),
      reminder_minutes_before: start && end && form.reminder_enabled ? Number(form.reminder_minutes_before) : null,
    };
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    const payload = buildPayload();
    if (!payload) return;

    try {
      if (editingTask) {
        await apiClient.patch(`/calendar-tasks/${editingTask.id}`, payload);
      } else {
        await apiClient.post('/calendar-tasks', payload);
      }
      setModalOpen(false);
      await loadData();
    } catch (error: any) {
      const detail = error?.response?.data?.detail;
      alert(typeof detail === 'string' ? detail : '保存计划失败');
    }
  };

  const handleTargetSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    try {
      const effective = targetForm.effective_from.includes(':')
        ? `${targetForm.effective_from}:00`
        : targetForm.effective_from;

      await apiClient.post<WorkTarget>('/targets', {
        period: targetForm.target_type,
        target_seconds: targetForm.target_seconds,
        include_category_ids: targetForm.category_ids.length > 0 ? targetForm.category_ids : null,
        effective_from: effective,
      });
      setTargetFormOpen(false);
      setTargetForm({
        target_type: 'daily',
        target_seconds: 3600,
        category_ids: [],
        effective_from: toLocalInputValue(new Date()),
      });
      await loadTargetData();
      setToast('目标创建成功');
    } catch (error: any) {
      const detail = error?.response?.data?.detail;
      setToast(typeof detail === 'string' ? detail : '创建目标失败');
    }
  };

  const toggleTarget = async (id: number, isActive: boolean) => {
    try {
      await apiClient.patch(`/targets/${id}`, { is_active: !isActive });
      await loadTargetData();
    } catch (error: any) {
      setToast(error?.response?.data?.detail || '更新目标失败');
    }
  };

  const deleteTarget = async (id: number) => {
    if (!window.confirm('确认删除该目标吗？')) return;
    try {
      await apiClient.delete(`/targets/${id}`);
      await loadTargetData();
    } catch (error: any) {
      setToast(error?.response?.data?.detail || '删除目标失败');
    }
  };

  const updateTaskStatus = async (task: CalendarTask, statusValue: CalendarTaskStatus) => {
    try {
      await apiClient.patch(`/calendar-tasks/${task.id}`, { status: statusValue });
      await loadData();
    } catch (error: any) {
      alert(error?.response?.data?.detail || '更新失败');
    }
  };

  const completeTask = async (task: CalendarTask, createSession = false) => {
    try {
      await apiClient.post(`/calendar-tasks/${task.id}/complete${createSession ? '?create_session=true' : ''}`);
      await loadData();
      setToast(createSession ? '已完成并转成时间记录' : '已标记完成');
    } catch (error: any) {
      alert(error?.response?.data?.detail || '完成事项失败');
    }
  };

  const startTimerFromTask = async (task: CalendarTask) => {
    if (!task.category_id) {
      alert('请先为事项选择分类，再开始计时');
      return;
    }

    if (getRunningTimer()) {
      alert('当前已有本地计时，请先停止后再开始新的事项');
      return;
    }

    const active = await apiClient.get<ActiveSession | null>('/sessions/active');
    if (active) {
      alert('当前已有正在进行的计时，请先停止后再开始新的事项');
      return;
    }

    const note = [task.title, task.description].filter(Boolean).join('\n');
    navigate(`/timer?category_id=${task.category_id}&note=${encodeURIComponent(note)}&auto_start=1`);
  };

  const moveRange = (direction: -1 | 1) => {
    if (view === 'month') setAnchorDate((date) => direction > 0 ? addMonths(date, 1) : subMonths(date, 1));
    if (view === 'week') setAnchorDate((date) => direction > 0 ? addWeeks(date, 1) : subWeeks(date, 1));
    if (view === 'day') setAnchorDate((date) => addDays(date, direction));
  };

  const categoryNames = (ids: number[]) => {
    if (ids.length === 0) return '全部';
    return ids
      .map((id) => categories.find((category) => category.id === id)?.name)
      .filter(Boolean)
      .join(', ') || '全部';
  };

  const renderTask = (task: CalendarTask, compact = false) => (
    <article key={task.id} className={`planner-task priority-${task.priority} status-${task.status}`}>
      <button type="button" onClick={() => openEdit(task)} className="planner-task-main">
        <span>{taskTimeLabel(task)}</span>
        <strong>{task.title}</strong>
        {!compact && <small>{task.category_name || '未分类'} · {formatTime(task.estimated_seconds)}</small>}
      </button>
      <div className="planner-task-actions">
        {task.status !== 'done' && (
          <button type="button" title="完成" onClick={() => completeTask(task)}>
            <CheckCircle2 size={16} />
          </button>
        )}
        {task.status === 'scheduled' && (
          <button type="button" title="开始计时" onClick={() => startTimerFromTask(task)}>
            <Play size={16} />
          </button>
        )}
        {task.status === 'scheduled' && !task.converted_session_id && (
          <button type="button" title="转时间记录" onClick={() => completeTask(task, true)}>
            <RotateCcw size={16} />
          </button>
        )}
        {task.status !== 'cancelled' && task.status !== 'done' && (
          <button type="button" title="取消" onClick={() => updateTaskStatus(task, 'cancelled')}>
            <XCircle size={16} />
          </button>
        )}
      </div>
    </article>
  );

  const monthDays = eachDayOfInterval({
    start: startOfWeek(startOfMonth(anchorDate), { weekStartsOn: 1 }),
    end: endOfWeek(endOfMonth(anchorDate), { weekStartsOn: 1 }),
  });

  const weekDays = eachDayOfInterval({
    start: startOfWeek(anchorDate, { weekStartsOn: 1 }),
    end: endOfWeek(anchorDate, { weekStartsOn: 1 }),
  });

  const daysToRender = view === 'month' ? monthDays : view === 'week' ? weekDays : [anchorDate];

  return (
    <PageShell
      className="planner-page"
      eyebrow="我的时间地图"
      title="计划日历"
      description="把事项、目标和完成节奏放在同一张时间地图里。"
      action={(
        <Button onClick={() => openCreate()}>
          <Plus size={17} /> 新增事项
        </Button>
      )}
    >

      {toast && (
        <div className="planner-toast">
          <Bell size={17} />
          <span>{toast}</span>
          <Button variant="secondary" onClick={() => setToast('')}>知道了</Button>
        </div>
      )}

      <section className="planner-summary">
        <StatCard label="今日事项" value={todaySummary.total} hint="一件一件来" />
        <StatCard label="已完成" value={todaySummary.done} hint="节奏正在形成" />
        <StatCard label="预计投入" value={formatTime(todaySummary.focusSeconds)} hint="给时间一个边界" />
        <StatCard label="待安排池" value={unscheduledTasks.length} hint="暂时放在这里" />
        <StatCard label="目标完成率" value={`${Math.round(targetOverview.completionRate * 100)}%`} hint="当前目标趋势" />
        <StatCard label="当前连胜" value={targetOverview.currentStreak} hint={`最佳 ${targetOverview.bestStreak}`} />
      </section>

      <div className="planner-toolbar">
        <div className="planner-view-switch">
          <button className={view === 'month' ? 'active' : ''} onClick={() => setView('month')}>月</button>
          <button className={view === 'week' ? 'active' : ''} onClick={() => setView('week')}>周</button>
          <button className={view === 'day' ? 'active' : ''} onClick={() => setView('day')}>日</button>
        </div>
        <div className="planner-range-nav">
          <button type="button" onClick={() => moveRange(-1)}><ChevronLeft size={18} /></button>
          <strong>
            {view === 'month' && format(anchorDate, 'yyyy 年 MM 月')}
            {view === 'week' && `${format(range.start, 'MM/dd')} - ${format(range.end, 'MM/dd')}`}
            {view === 'day' && format(anchorDate, 'yyyy/MM/dd')}
          </strong>
          <button type="button" onClick={() => moveRange(1)}><ChevronRight size={18} /></button>
        </div>
      </div>

      <div className="planner-layout">
        <main className={`planner-calendar planner-${view}`}>
          {loading ? (
            <LoadingState className="planner-loading" />
          ) : (
            <div className="planner-days">
              {daysToRender.map((day) => {
                const key = format(day, 'yyyy-MM-dd');
                const dayTasks = scheduledByDate.get(key) ?? [];
                const outsideMonth = view === 'month' && day.getMonth() !== anchorDate.getMonth();

                return (
                  <section
                    className={`planner-day ${outsideMonth ? 'muted' : ''} ${isSameDay(day, new Date()) ? 'today' : ''}`}
                    key={key}
                  >
                    <button type="button" className="planner-day-head" onClick={() => openCreate(day)}>
                      <span>{format(day, view === 'month' ? 'd' : 'MM/dd')}</span>
                      <small>{format(day, 'EEE')}</small>
                    </button>
                    <div className="planner-day-list">
                      {dayTasks.length === 0 ? (
                        <p>留白也算计划</p>
                      ) : (
                        dayTasks.map((task) => renderTask(task, view === 'month'))
                      )}
                    </div>
                  </section>
                );
              })}
            </div>
          )}
        </main>

        <Card as="aside" className="planner-pool">
          <SectionHeader
            title="待安排池"
            description="还没有日期的想法，先温柔收纳。"
            action={(
              <Button variant="secondary" onClick={() => openCreate()}>
                <Plus size={16} />
              </Button>
            )}
          />
          {unscheduledTasks.length === 0 ? (
            <EmptyState compact className="planner-empty" title="没有待安排事项" description="当下很清爽。" />
          ) : (
            <div className="planner-pool-list">
              {unscheduledTasks.map((task) => (
                <article key={task.id} className={`planner-pool-item priority-${task.priority}`}>
                  <button type="button" onClick={() => openEdit(task)}>
                    <strong>{task.title}</strong>
                    <span>{priorityLabels[task.priority]}优先级 · {formatTime(task.estimated_seconds)}</span>
                  </button>
                  <Button onClick={() => openEdit(task)}>安排时间</Button>
                </article>
              ))}
            </div>
          )}
        </Card>
      </div>

      <section className="planner-target-section">
        <div className="planner-target-head">
          <div>
            <span>目标机制</span>
            <h2>目标与完成率</h2>
            <p>日程负责安排，目标负责衡量。完成率和连胜会跟随评估结果更新。</p>
          </div>
          <Button variant={targetFormOpen ? 'ghost' : 'primary'} onClick={() => setTargetFormOpen(!targetFormOpen)}>
            {targetFormOpen ? '收起' : '新建目标'}
          </Button>
        </div>

        <div className="target-overview planner-target-overview">
          <StatCard label="当前连胜" value={targetOverview.currentStreak} hint="连续达标周期" />
          <StatCard label="最佳连胜" value={targetOverview.bestStreak} hint="历史最好状态" />
          <StatCard label="完成率" value={`${Math.round(targetOverview.completionRate * 100)}%`} hint="全部评估统计" />
          <StatCard label="时间债务" value={formatTime(targetOverview.activeDebt)} hint="慢慢补回" />
        </div>

        {targetDashboard?.progress && targetDashboard.progress.length > 0 && (
          <div className="target-progress-grid">
            {targetDashboard.progress.map((item) => (
              <article key={`${item.target_id}-${item.period_start}`} className="target-progress-card">
                <div>
                  <span>{periodLabel(item.period)}</span>
                  <strong>{Math.round(item.progress_ratio * 100)}%</strong>
                </div>
                <div className="target-progress-bar">
                  <span style={{ width: `${Math.min(100, Math.max(0, item.progress_ratio * 100))}%` }} />
                </div>
                <p>
                  已完成 {formatTime(item.actual_seconds)}，还差 {formatTime(item.remaining_seconds)}
                </p>
              </article>
            ))}
          </div>
        )}

        {targetFormOpen && (
          <Card as="form" onSubmit={handleTargetSubmit} className="target-form planner-target-form">
            <div className="form-group">
              <label>周期</label>
              <select value={targetForm.target_type} onChange={(e) => handleTargetPeriodChange(e.target.value as TargetPeriod)}>
                <option value="tomorrow">明日计划</option>
                <option value="daily">每日</option>
                <option value="weekly">每周</option>
                <option value="monthly">每月</option>
              </select>
            </div>
            <div className="form-group">
              <label>生效时间</label>
              <input
                type="datetime-local"
                step="60"
                value={targetForm.effective_from}
                onChange={(e) => setTargetForm({ ...targetForm, effective_from: e.target.value })}
                required
              />
            </div>
            <div className="form-group">
              <label>目标时长（小时）</label>
              <input
                type="number"
                min="0.5"
                step="0.5"
                value={targetForm.target_seconds / 3600}
                onChange={(e) => setTargetForm({ ...targetForm, target_seconds: Number(e.target.value) * 3600 })}
              />
            </div>
            <div className="form-group">
              <label>包含分类</label>
              <div className="category-checkboxes">
                {categories.map((category) => (
                  <label key={category.id}>
                    <input
                      type="checkbox"
                      checked={targetForm.category_ids.includes(category.id)}
                      onChange={(e) => {
                        const categoryIds = e.target.checked
                          ? [...targetForm.category_ids, category.id]
                          : targetForm.category_ids.filter((id) => id !== category.id);
                        setTargetForm({ ...targetForm, category_ids: categoryIds });
                      }}
                    />
                    {category.name}
                  </label>
                ))}
              </div>
            </div>
            <Button type="submit">创建目标</Button>
          </Card>
        )}

        <Card className="targets-list planner-target-list">
          <h2>目标列表</h2>
          {targetLoading ? (
            <LoadingState text="正在整理目标进度..." />
          ) : targets.length === 0 ? (
            <EmptyState title="还没有目标" description="可以先设一个很小的每日目标。" />
          ) : (
            <table>
              <thead>
                <tr>
                  <th>周期</th>
                  <th>目标时长</th>
                  <th>分类</th>
                  <th>连胜</th>
                  <th>完成率</th>
                  <th>状态</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {targets.map((target) => {
                  const isActive = target.is_active ?? target.is_enabled ?? true;
                  const period = target.period ?? target.target_type ?? 'daily';
                  const categoryIds = target.include_category_ids ?? target.category_ids ?? [];
                  const metric = metricByTarget.get(target.id);

                  return (
                    <tr key={target.id}>
                      <td>{periodLabel(period)}</td>
                      <td>{formatTime(target.target_seconds)}</td>
                      <td>{categoryNames(categoryIds)}</td>
                      <td>{metric ? `${metric.current_streak} / ${metric.best_streak}` : '0 / 0'}</td>
                      <td>{metric ? `${Math.round(metric.completion_rate * 100)}%` : '0%'}</td>
                      <td>{isActive ? '启用' : '停用'}</td>
                      <td>
                        <Button variant="ghost" onClick={() => toggleTarget(target.id, isActive)}>
                          {isActive ? '停用' : '启用'}
                        </Button>
                        <Button variant="danger" style={{ marginLeft: 8 }} onClick={() => deleteTarget(target.id)}>
                          删除
                        </Button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </Card>

        <Card className="evaluations-list planner-evaluation-list">
          <h2>最近评估</h2>
          {targetLoading ? (
            <LoadingState text="正在查看最近评估..." />
          ) : evaluations.length === 0 ? (
            <EmptyState title="暂无评估记录" description="目标走过一个周期后，这里会出现结果。" />
          ) : (
            <table>
              <thead>
                <tr>
                  <th>周期</th>
                  <th>范围</th>
                  <th>目标</th>
                  <th>实际</th>
                  <th>结果</th>
                </tr>
              </thead>
              <tbody>
                {evaluations.slice(0, 8).map((evaluation) => {
                  const target = targetById.get(evaluation.target_id);
                  return (
                    <tr key={evaluation.id}>
                      <td>{periodLabel(target?.period ?? 'daily')}</td>
                      <td>
                        {new Date(evaluation.period_start).toLocaleDateString()} - {new Date(evaluation.period_end).toLocaleDateString()}
                      </td>
                      <td>{formatTime(evaluation.target_seconds)}</td>
                      <td>{formatTime(evaluation.actual_seconds)}</td>
                      <td className={evaluation.status === 'met' ? 'pass' : 'fail'}>
                        {evaluation.status === 'met' ? '达标' : `未达标，差 ${formatTime(evaluation.deficit_seconds)}`}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </Card>
      </section>

      {modalOpen && (
        <div className="planner-modal" role="dialog" aria-modal="true">
          <form className="planner-dialog" onSubmit={handleSubmit}>
            <header>
              <div>
                <span>{editingTask ? statusLabels[editingTask.status] : '新事项'}</span>
                <h2>{editingTask ? '编辑事项' : '新增事项'}</h2>
              </div>
              <Button variant="ghost" onClick={() => setModalOpen(false)}>关闭</Button>
            </header>

            <div className="planner-form-grid">
              <label className="wide">
                标题
                <input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
              </label>
              <label className="wide">
                描述
                <textarea rows={3} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
              </label>
              <label>
                分类
                <select value={form.category_id} onChange={(e) => setForm({ ...form, category_id: e.target.value })}>
                  <option value="">未分类</option>
                  {categories.map((category) => (
                    <option key={category.id} value={category.id}>{category.name}</option>
                  ))}
                </select>
              </label>
              <label>
                优先级
                <select value={form.priority} onChange={(e) => setForm({ ...form, priority: e.target.value as CalendarTaskPriority })}>
                  <option value="low">低</option>
                  <option value="medium">中</option>
                  <option value="high">高</option>
                </select>
              </label>
              <label>
                预计耗时（分钟）
                <input
                  type="number"
                  min="1"
                  step="1"
                  value={form.estimated_minutes}
                  onChange={(e) => setForm({ ...form, estimated_minutes: e.target.value })}
                />
              </label>
              <label>
                日期
                <input type="date" value={form.date} onChange={(e) => setForm({ ...form, date: e.target.value })} />
              </label>
              <label>
                开始
                <input type="time" value={form.start_time} onChange={(e) => setForm({ ...form, start_time: e.target.value })} />
              </label>
              <label>
                结束
                <input type="time" value={form.end_time} onChange={(e) => setForm({ ...form, end_time: e.target.value })} />
              </label>
              <label className="planner-checkbox wide">
                <input
                  type="checkbox"
                  checked={form.reminder_enabled}
                  onChange={(e) => setForm({ ...form, reminder_enabled: e.target.checked })}
                />
                <span><Bell size={16} /> 临近提醒</span>
              </label>
              <label>
                提前提醒
                <select
                  value={form.reminder_minutes_before}
                  disabled={!form.reminder_enabled}
                  onChange={(e) => setForm({ ...form, reminder_minutes_before: e.target.value })}
                >
                  {reminderOptions.map((minutes) => (
                    <option key={minutes} value={minutes}>{minutes} 分钟</option>
                  ))}
                </select>
              </label>
            </div>

            <footer>
              {editingTask && editingTask.status !== 'done' && (
                <Button variant="secondary" className="planner-dialog-complete" onClick={() => completeTask(editingTask)}>
                  <CheckCircle2 size={17} /> 完成
                </Button>
              )}
              <Button variant="ghost" className="planner-dialog-secondary" onClick={() => setModalOpen(false)}>取消</Button>
              <Button type="submit" className="planner-dialog-primary">
                <Clock size={17} /> 保存
              </Button>
            </footer>
          </form>
        </div>
      )}
    </PageShell>
  );
};
