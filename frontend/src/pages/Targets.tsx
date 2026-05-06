import React, { useEffect, useMemo, useState } from 'react';
import { Button, Card, EmptyState, LoadingState, PageShell, Progress, StatCard } from '../components/ui';
import { apiClient } from '../api/client';
import { Category, TargetDashboard, WorkEvaluation, WorkTarget } from '../types';

type TargetPeriod = 'daily' | 'weekly' | 'monthly' | 'tomorrow';

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

const formatTime = (seconds: number) => {
  const total = Math.max(0, Math.floor(seconds || 0));
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  if (hours === 0) return `${minutes} 分钟`;
  return `${hours} 小时 ${minutes} 分钟`;
};

const formatDateTime = (value?: string) => {
  if (!value) return '立即生效';
  return new Date(value).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
};

export const Targets: React.FC = () => {
  const [targets, setTargets] = useState<WorkTarget[]>([]);
  const [evaluations, setEvaluations] = useState<WorkEvaluation[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [dashboard, setDashboard] = useState<TargetDashboard | null>(null);
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    target_type: 'daily' as TargetPeriod,
    target_seconds: 3600,
    category_ids: [] as number[],
    effective_from: toLocalInputValue(new Date()),
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [targetsData, evaluationsData, categoriesData, dashboardData] = await Promise.all([
        apiClient.get<WorkTarget[]>('/targets'),
        apiClient.get<WorkEvaluation[]>('/evaluations'),
        apiClient.get<Category[]>('/categories'),
        apiClient.get<TargetDashboard>('/targets/dashboard'),
      ]);
      setTargets(targetsData);
      setEvaluations(evaluationsData);
      setCategories(categoriesData);
      setDashboard(dashboardData);
    } catch (error) {
      console.error('加载目标数据失败', error);
    } finally {
      setLoading(false);
    }
  };

  const metricByTarget = useMemo(() => {
    const map = new Map<number, TargetDashboard['metrics'][number]>();
    dashboard?.metrics.forEach((metric) => map.set(metric.target_id, metric));
    return map;
  }, [dashboard]);

  const targetById = useMemo(() => {
    const map = new Map<number, WorkTarget>();
    targets.forEach((target) => map.set(target.id, target));
    return map;
  }, [targets]);

  const overview = useMemo(() => {
    const metrics = dashboard?.metrics ?? [];
    const totalEvaluations = metrics.reduce((sum, item) => sum + item.total_evaluations, 0);
    const metEvaluations = metrics.reduce((sum, item) => sum + item.met_evaluations, 0);
    return {
      currentStreak: Math.max(0, ...metrics.map((item) => item.current_streak)),
      bestStreak: Math.max(0, ...metrics.map((item) => item.best_streak)),
      completionRate: totalEvaluations === 0 ? 0 : metEvaluations / totalEvaluations,
      activeDebt: metrics.reduce((sum, item) => sum + item.active_debt_seconds, 0),
      suggestedCompensation: metrics.reduce((sum, item) => sum + item.suggested_compensation_seconds, 0),
    };
  }, [dashboard]);

  const handlePeriodChange = (period: TargetPeriod) => {
    setFormData((prev) => ({
      ...prev,
      target_type: period,
      effective_from: period === 'tomorrow' ? tomorrowStartInputValue() : prev.effective_from,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const effective = formData.effective_from.includes(':')
        ? `${formData.effective_from}:00`
        : formData.effective_from;

      await apiClient.post<WorkTarget>('/targets', {
        period: formData.target_type,
        target_seconds: formData.target_seconds,
        include_category_ids: formData.category_ids.length > 0 ? formData.category_ids : null,
        effective_from: effective,
      });
      setShowForm(false);
      setFormData({
        target_type: 'daily',
        target_seconds: 3600,
        category_ids: [],
        effective_from: toLocalInputValue(new Date()),
      });
      await loadData();
      alert('目标创建成功');
    } catch (error: any) {
      const detail = error?.response?.data?.detail;
      if (Array.isArray(detail)) {
        alert(detail.map((item: any) => item.msg).join(', '));
      } else {
        alert(typeof detail === 'string' ? detail : '创建失败');
      }
    }
  };

  const toggleTarget = async (id: number, isActive: boolean) => {
    try {
      await apiClient.patch(`/targets/${id}`, { is_active: !isActive });
      await loadData();
    } catch (error: any) {
      alert(error?.response?.data?.detail || '更新失败');
    }
  };

  const deleteTarget = async (id: number) => {
    if (!window.confirm('确认删除该目标吗？')) return;
    try {
      await apiClient.delete(`/targets/${id}`);
      await loadData();
    } catch (error: any) {
      alert(error?.response?.data?.detail || '删除失败');
    }
  };

  const categoryNames = (ids: number[]) => {
    if (ids.length === 0) return '全部';
    return ids
      .map((id) => categories.find((category) => category.id === id)?.name)
      .filter(Boolean)
      .join(', ') || '全部';
  };

  const renderEventTitle = (event: TargetDashboard['events'][number]) => {
    if (event.rule_type === 'compensation') return '补回记录';
    if (event.payload_json?.break_record) return '断签 / 欠债';
    if (event.rule_type === 'time_debt') return '欠债记录';
    return event.rule_type;
  };

  return (
    <PageShell
      className="targets-page"
      eyebrow="目标工作台"
      title="目标页"
      description="目标不是催促，是帮你看见时间去向的温和边界。"
      action={(
        <Button variant={showForm ? 'ghost' : 'primary'} onClick={() => setShowForm(!showForm)}>
          {showForm ? '收起' : '+ 新建目标'}
        </Button>
      )}
    >

      <div className="target-overview">
        <StatCard label="当前连胜" value={overview.currentStreak} hint="保持一种轻节奏" />
        <StatCard label="最佳连胜" value={overview.bestStreak} hint="你曾经做到过" />
        <StatCard label="完成率" value={`${Math.round(overview.completionRate * 100)}%`} hint="只看趋势" />
        <StatCard label="时间债务" value={formatTime(overview.activeDebt)} hint="慢慢补回" />
        <StatCard label="建议补回" value={formatTime(overview.suggestedCompensation)} hint="留一个缓冲" />
      </div>

      {dashboard?.progress && dashboard.progress.length > 0 && (
        <div className="target-progress-grid">
          {dashboard.progress.map((item) => (
            <article key={`${item.target_id}-${item.period_start}`} className="target-progress-card">
              <div>
                <span>{periodLabel(item.period)}</span>
                <strong>{Math.round(item.progress_ratio * 100)}%</strong>
              </div>
              <Progress value={item.progress_ratio} max={1} className="target-progress-bar" />
              <p>
                已完成 {formatTime(item.actual_seconds)}，还差 {formatTime(item.remaining_seconds)}
              </p>
            </article>
          ))}
        </div>
      )}

      {showForm && (
        <Card as="form" onSubmit={handleSubmit} className="target-form">
          <div className="form-group">
            <label>周期</label>
            <select value={formData.target_type} onChange={(e) => handlePeriodChange(e.target.value as TargetPeriod)}>
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
              value={formData.effective_from}
              onChange={(e) => setFormData({ ...formData, effective_from: e.target.value })}
              required
            />
            <small>
              {formData.target_type === 'tomorrow'
                ? '明日计划默认从明天 00:00 开始，并只评估一次。'
                : '周目标在周日评估，月目标在月末评估。'}
            </small>
          </div>

          <div className="form-group">
            <label>目标时长（小时）</label>
            <input
              type="number"
              min="0.5"
              step="0.5"
              value={formData.target_seconds / 3600}
              onChange={(e) => setFormData({ ...formData, target_seconds: Number(e.target.value) * 3600 })}
            />
          </div>

          <div className="form-group">
            <label>包含分类</label>
            <div className="category-checkboxes">
              {categories.map((category) => (
                <label key={category.id}>
                  <input
                    type="checkbox"
                    checked={formData.category_ids.includes(category.id)}
                    onChange={(e) => {
                      const categoryIds = e.target.checked
                        ? [...formData.category_ids, category.id]
                        : formData.category_ids.filter((id) => id !== category.id);
                      setFormData({ ...formData, category_ids: categoryIds });
                    }}
                  />
                  {category.name}
                </label>
              ))}
            </div>
          </div>

          <Button type="submit">创建</Button>
        </Card>
      )}

      <Card className="targets-list">
        <h2>我的目标</h2>
        {loading ? (
          <LoadingState text="正在整理目标进度..." />
        ) : targets.length === 0 ? (
          <EmptyState title="还没有目标" description="可以先设一个很小的每日目标，让系统陪你开始。" />
        ) : (
          <table>
            <thead>
              <tr>
                <th>周期</th>
                <th>目标时长</th>
                <th>生效时间</th>
                <th>分类</th>
                <th>连胜</th>
                <th>完成率</th>
                <th>债务</th>
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
                    <td>{formatDateTime(target.effective_from)}</td>
                    <td>{categoryNames(categoryIds)}</td>
                    <td>
                      {metric ? `${metric.current_streak} / ${metric.best_streak}` : '0 / 0'}
                    </td>
                    <td>{metric ? `${Math.round(metric.completion_rate * 100)}%` : '0%'}</td>
                    <td>{formatTime(metric?.active_debt_seconds ?? 0)}</td>
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

      <Card className="evaluations-list">
        <h2>最近评估结果</h2>
        {loading ? (
          <LoadingState text="正在查看最近评估..." />
        ) : evaluations.length === 0 ? (
          <EmptyState title="暂无评估记录" description="等目标走过一个周期，这里会出现复盘结果。" />
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
              {evaluations.slice(0, 10).map((evaluation) => {
                const target = targetById.get(evaluation.target_id);
                return (
                  <tr key={evaluation.id}>
                    <td>{periodLabel(target?.period ?? 'daily')}</td>
                    <td>
                      {new Date(evaluation.period_start).toLocaleDateString()} -{' '}
                      {new Date(evaluation.period_end).toLocaleDateString()}
                    </td>
                    <td>{formatTime(evaluation.target_seconds)}</td>
                    <td>{formatTime(evaluation.actual_seconds)}</td>
                    <td className={evaluation.status === 'met' ? 'pass' : 'fail'}>
                      {evaluation.status === 'met'
                        ? '达标'
                        : `未达标，差 ${formatTime(evaluation.deficit_seconds)}`}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </Card>

      <Card className="target-events">
        <h2>补回与提醒</h2>
        {loading ? (
          <LoadingState text="正在查看补回记录..." />
        ) : !dashboard || dashboard.events.length === 0 ? (
          <EmptyState title="暂无事件" description="没有需要补回的时间，也是一种稳定。" />
        ) : (
          <div className="target-event-list">
            {dashboard.events.slice(0, 20).map((event) => {
              const payload = event.payload_json ?? {};
              const amount =
                event.rule_type === 'compensation'
                  ? payload.applied_seconds
                  : payload.outstanding_seconds ?? payload.deficit_seconds;
              return (
                <article key={event.id} className={`target-event ${event.rule_type}`}>
                  <div>
                    <strong>{renderEventTitle(event)}</strong>
                    <span>{new Date(event.created_at).toLocaleString()}</span>
                  </div>
                  <p>
                    {periodLabel(payload.period || '')}
                    {amount ? ` · ${formatTime(amount)}` : ''}
                    {payload.suggested_compensation_seconds
                      ? ` · 建议补回 ${formatTime(payload.suggested_compensation_seconds)}`
                      : ''}
                  </p>
                </article>
              );
            })}
          </div>
        )}
      </Card>
    </PageShell>
  );
};
