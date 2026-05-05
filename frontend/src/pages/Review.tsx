import React, { useEffect, useMemo, useState } from 'react';
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { Clipboard, CalendarDays, TrendingUp } from 'lucide-react';
import { apiClient } from '../api/client';
import { DailyReview, ReviewCategoryItem, WeeklyReview } from '../types';

type ReviewMode = 'daily' | 'weekly';

const toDateInputValue = (date: Date) => {
  const copy = new Date(date);
  copy.setMinutes(copy.getMinutes() - copy.getTimezoneOffset());
  return copy.toISOString().slice(0, 10);
};

const formatTime = (seconds: number) => {
  const total = Math.max(0, Math.floor(seconds || 0));
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  if (hours === 0) return `${minutes} 分钟`;
  return `${hours} 小时 ${minutes} 分钟`;
};

const trendText = (seconds: number) => {
  if (seconds === 0) return '持平';
  const sign = seconds > 0 ? '+' : '-';
  return `${sign}${formatTime(Math.abs(seconds))}`;
};

const CategoryRows: React.FC<{ items: ReviewCategoryItem[] }> = ({ items }) => {
  if (items.length === 0) return <p>暂无分类记录</p>;

  return (
    <div className="review-category-list">
      {items.slice(0, 6).map((item) => (
        <div key={item.category_id ?? 'none'} className="review-category-row">
          <span style={{ background: item.category_color || '#64748b' }} />
          <strong>{item.category_name || '未分类'}</strong>
          <em>{formatTime(item.seconds)}</em>
          <small>{trendText(item.trend_delta_seconds)}</small>
        </div>
      ))}
    </div>
  );
};

export const Review: React.FC = () => {
  const [mode, setMode] = useState<ReviewMode>('daily');
  const [date, setDate] = useState(toDateInputValue(new Date()));
  const [daily, setDaily] = useState<DailyReview | null>(null);
  const [weekly, setWeekly] = useState<WeeklyReview | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadReview();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode, date]);

  const loadReview = async () => {
    setLoading(true);
    try {
      if (mode === 'daily') {
        const data = await apiClient.get<DailyReview>('/reviews/daily', { date });
        setDaily(data);
      } else {
        const data = await apiClient.get<WeeklyReview>('/reviews/weekly', { date });
        setWeekly(data);
      }
    } catch (error) {
      console.error('加载复盘失败', error);
    } finally {
      setLoading(false);
    }
  };

  const currentMarkdown = mode === 'daily' ? daily?.markdown : weekly?.markdown;

  const handleCopy = async () => {
    if (!currentMarkdown) return;
    await navigator.clipboard.writeText(currentMarkdown);
    alert('Markdown 已复制');
  };

  const dailyChartData = useMemo(() => {
    return (daily?.by_category ?? []).map((item) => ({
      name: item.category_name || '未分类',
      hours: Number((item.seconds / 3600).toFixed(2)),
      color: item.category_color || '#1f2a44',
    }));
  }, [daily]);

  const weeklyChartData = useMemo(() => {
    return (weekly?.daily_totals ?? []).map((item) => ({
      date: item.date.slice(5),
      hours: Number((item.total_seconds / 3600).toFixed(2)),
    }));
  }, [weekly]);

  const renderDaily = () => {
    if (!daily) return null;

    return (
      <>
        <div className="review-metric-grid">
          <div>
            <span>今日总计</span>
            <strong>{formatTime(daily.total_seconds)}</strong>
          </div>
          <div>
            <span>最多分类</span>
            <strong>{daily.top_category?.category_name || '无'}</strong>
          </div>
          <div>
            <span>目标达成</span>
            <strong>{daily.target_summary.met_count}/{daily.target_summary.total_count}</strong>
          </div>
          <div>
            <span>仍需补足</span>
            <strong>{formatTime(daily.target_summary.remaining_seconds)}</strong>
          </div>
        </div>

        <div className="review-grid">
          <section className="review-panel">
            <h2><TrendingUp size={18} /> 分类洞察</h2>
            <CategoryRows items={daily.by_category} />
          </section>
          <section className="review-panel">
            <h2><CalendarDays size={18} /> 分类分布</h2>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={dailyChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip formatter={(value: number) => `${value} 小时`} />
                <Bar dataKey="hours" fill="#1f2a44" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </section>
        </div>

        <section className="review-panel">
          <h2>时痕关联</h2>
          {daily.time_traces.length === 0 ? (
            <p>暂无时痕</p>
          ) : (
            <div className="review-traces">
              {daily.time_traces.map((trace) => (
                <article key={trace.id}>
                  <time>{new Date(trace.created_at).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}</time>
                  <p>{trace.content}</p>
                </article>
              ))}
            </div>
          )}
        </section>
      </>
    );
  };

  const renderWeekly = () => {
    if (!weekly) return null;

    return (
      <>
        <div className="review-metric-grid">
          <div>
            <span>本周总时长</span>
            <strong>{formatTime(weekly.total_seconds)}</strong>
          </div>
          <div>
            <span>平均每天</span>
            <strong>{formatTime(weekly.average_daily_seconds)}</strong>
          </div>
          <div>
            <span>最高效一天</span>
            <strong>{weekly.best_day ? weekly.best_day.date.slice(5) : '无'}</strong>
          </div>
          <div>
            <span>断档天数</span>
            <strong>{weekly.gap_days}</strong>
          </div>
        </div>

        <div className="review-grid">
          <section className="review-panel">
            <h2><TrendingUp size={18} /> 分类趋势</h2>
            <CategoryRows items={weekly.by_category} />
          </section>
          <section className="review-panel">
            <h2><CalendarDays size={18} /> 每日节奏</h2>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={weeklyChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip formatter={(value: number) => `${value} 小时`} />
                <Bar dataKey="hours" fill="#2f855a" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </section>
        </div>

        <section className="review-panel">
          <h2>周内时痕</h2>
          {weekly.time_traces.length === 0 ? (
            <p>暂无时痕</p>
          ) : (
            <div className="review-traces">
              {weekly.time_traces.slice(0, 12).map((trace) => (
                <article key={trace.id}>
                  <time>{new Date(trace.created_at).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })}</time>
                  <p>{trace.content}</p>
                </article>
              ))}
            </div>
          )}
        </section>
      </>
    );
  };

  return (
    <div className="review-page">
      <div className="review-header">
        <div>
          <h1>复盘</h1>
          <p>{mode === 'daily' ? '日报' : '周报'}把统计、目标和时痕串在一起。</p>
        </div>
        <button onClick={handleCopy} disabled={!currentMarkdown}>
          <Clipboard size={17} /> 导出 Markdown
        </button>
      </div>

      <div className="review-toolbar">
        <div className="period-selector">
          <button className={mode === 'daily' ? 'active' : ''} onClick={() => setMode('daily')}>每日复盘</button>
          <button className={mode === 'weekly' ? 'active' : ''} onClick={() => setMode('weekly')}>周报</button>
        </div>
        <input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
      </div>

      {loading ? <p>加载中...</p> : mode === 'daily' ? renderDaily() : renderWeekly()}

      {currentMarkdown && (
        <section className="review-panel markdown-panel">
          <h2>Markdown 预览</h2>
          <pre>{currentMarkdown}</pre>
        </section>
      )}
    </div>
  );
};
