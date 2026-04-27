import React, { useEffect, useState } from 'react';
import { StatsChart } from '../components/StatsChart';
import { apiClient } from '../api/client';
import { StatsSummary } from '../types';

type Period = 'today' | 'week' | 'month' | 'custom';
type HistoryItem = {
  label: string;
  start: string;
  end: string;
  total_seconds: number;
  by_category: StatsSummary['by_category'];
};

const toDateInputValue = (date: Date) => {
  const copy = new Date(date);
  copy.setMinutes(copy.getMinutes() - copy.getTimezoneOffset());
  return copy.toISOString().slice(0, 10);
};

const addDays = (date: Date, days: number) => {
  const copy = new Date(date);
  copy.setDate(copy.getDate() + days);
  return copy;
};

const startOfWeek = (date: Date) => {
  const day = date.getDay();
  const mondayOffset = day === 0 ? -6 : 1 - day;
  return addDays(date, mondayOffset);
};

const getCurrentRange = (period: Exclude<Period, 'custom'>) => {
  const now = new Date();
  if (period === 'today') {
    return { start: now, end: now };
  }
  if (period === 'week') {
    const start = startOfWeek(now);
    return { start, end: addDays(start, 6) };
  }
  const start = new Date(now.getFullYear(), now.getMonth(), 1);
  const end = new Date(now.getFullYear(), now.getMonth() + 1, 0);
  return { start, end };
};

const rangeParams = (start: Date, end: Date) => ({
  start: `${toDateInputValue(start)}T00:00:00`,
  end: `${toDateInputValue(end)}T23:59:59`,
});

const shortDate = (date: Date) => `${date.getMonth() + 1}/${date.getDate()}`;

const buildHistoryRanges = (period: Exclude<Period, 'custom'>) => {
  const now = new Date();
  if (period === 'today') {
    return Array.from({ length: 7 }, (_, index) => {
      const day = addDays(now, -index);
      return {
        label: index === 0 ? '今日' : index === 1 ? '昨天' : `${day.getMonth() + 1}月${day.getDate()}日`,
        start: day,
        end: day,
      };
    });
  }

  if (period === 'week') {
    const currentStart = startOfWeek(now);
    return Array.from({ length: 8 }, (_, index) => {
      const start = addDays(currentStart, -7 * index);
      const end = addDays(start, 6);
      return {
        label: index === 0 ? '本周' : `${shortDate(start)}-${shortDate(end)}`,
        start,
        end,
      };
    });
  }

  const currentStart = new Date(now.getFullYear(), now.getMonth(), 1);
  return Array.from({ length: 12 }, (_, index) => {
    const start = new Date(currentStart.getFullYear(), currentStart.getMonth() - index, 1);
    const end = new Date(start.getFullYear(), start.getMonth() + 1, 0);
    return {
      label: index === 0 ? '本月' : `${start.getFullYear()}年${start.getMonth() + 1}月`,
      start,
      end,
    };
  });
};

export const Classification: React.FC = () => {
  const [period, setPeriod] = useState<Period>('week');
  const [customStart, setCustomStart] = useState('');
  const [customEnd, setCustomEnd] = useState('');
  const [summary, setSummary] = useState<StatsSummary | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);

  useEffect(() => {
    if (period === 'custom' && (!customStart || !customEnd)) {
      setHistory([]);
      return;
    }
    loadStats();
    loadHistory();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [period]);

  const loadStats = async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      if (period === 'custom') {
        if (!customStart || !customEnd) {
          setSummary(null);
          setLoading(false);
          return;
        }
        params.start = `${customStart}T00:00:00`;
        params.end = `${customEnd}T23:59:59`;
      } else {
        const currentRange = getCurrentRange(period);
        Object.assign(params, rangeParams(currentRange.start, currentRange.end));
      }

      const data = await apiClient.get<StatsSummary>('/stats/summary', params);
      setSummary(data);
    } catch (error) {
      console.error('加载分类统计失败', error);
      setSummary(null);
    } finally {
      setLoading(false);
    }
  };

  const loadHistory = async () => {
    if (period === 'custom') {
      setHistory([]);
      return;
    }

    setHistoryLoading(true);
    try {
      const ranges = buildHistoryRanges(period);
      const data = await Promise.all(
        ranges.map(async (range) => {
          const summary = await apiClient.get<StatsSummary>(
            '/stats/summary',
            rangeParams(range.start, range.end),
          );
          return {
            label: range.label,
            start: toDateInputValue(range.start),
            end: toDateInputValue(range.end),
            total_seconds: summary.total_seconds,
            by_category: summary.by_category,
          };
        }),
      );
      setHistory(data);
    } catch (error) {
      console.error('加载历史统计失败', error);
      setHistory([]);
    } finally {
      setHistoryLoading(false);
    }
  };

  const formatTime = (seconds: number) => {
    const total = Math.max(0, Math.floor(seconds));
    const h = Math.floor(total / 3600);
    const m = Math.floor((total % 3600) / 60);
    if (h === 0) return `${m} 分钟`;
    return `${h} 小时 ${m} 分钟`;
  };

  const rows = (summary?.by_category || []).slice().sort((a, b) => (b.seconds || 0) - (a.seconds || 0));

  const chartData = rows.map((cat) => ({
    name: cat.category_name || '未分类',
    value: cat.seconds,
    color: cat.category_color || '#667eea',
  }));

  const percent = (seconds: number) => {
    if (!summary || summary.total_seconds === 0) return '0%';
    return `${((seconds / summary.total_seconds) * 100).toFixed(1)}%`;
  };

  const historyTitle =
    period === 'today' ? '近几天时长' : period === 'week' ? '过往周时长' : '过往月时长';

  const categoryBreakdown = (item: HistoryItem) => {
    const top = item.by_category
      .filter((cat) => cat.seconds > 0)
      .slice()
      .sort((a, b) => b.seconds - a.seconds)
      .slice(0, 3);

    if (top.length === 0) return '暂无分类';
    return top
      .map((cat) => `${cat.category_name || '未分类'} ${formatTime(cat.seconds)}`)
      .join(' / ');
  };

  return (
    <div className="stats-page">
      <h1>分类统计</h1>

      <div className="period-selector">
        <button className={period === 'today' ? 'active' : ''} onClick={() => setPeriod('today')}>
          今日
        </button>
        <button className={period === 'week' ? 'active' : ''} onClick={() => setPeriod('week')}>
          本周
        </button>
        <button className={period === 'month' ? 'active' : ''} onClick={() => setPeriod('month')}>
          本月
        </button>
        <button className={period === 'custom' ? 'active' : ''} onClick={() => setPeriod('custom')}>
          自定义
        </button>
      </div>

      {period === 'custom' && (
        <div className="custom-range">
          <input type="date" value={customStart} onChange={(e) => setCustomStart(e.target.value)} />
          <span>至</span>
          <input type="date" value={customEnd} onChange={(e) => setCustomEnd(e.target.value)} />
          <button onClick={loadStats}>查询</button>
        </div>
      )}

      <div className="stats-current">
        {loading ? (
          <p>加载中...</p>
        ) : !summary || summary.total_seconds === 0 ? (
          <p>暂无数据</p>
        ) : (
          <>
            <StatsChart data={chartData} title="分类占比" />
            <div className="summary-table">
              <div className="summary-total">总计：{formatTime(summary.total_seconds)}</div>
              <table>
                <thead>
                  <tr>
                    <th>分类</th>
                    <th>时长</th>
                    <th>占比</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((cat) => (
                    <tr key={cat.category_id ?? -1}>
                      <td>
                        <span
                          style={{
                            display: 'inline-block',
                            width: 10,
                            height: 10,
                            borderRadius: '50%',
                            background: cat.category_color || '#999',
                            marginRight: 8,
                          }}
                        />
                        {cat.category_name || '未分类'}
                      </td>
                      <td>{formatTime(cat.seconds)}</td>
                      <td>{percent(cat.seconds)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>

      {period !== 'custom' && (
        <div className="history-panel">
          <h2>{historyTitle}</h2>
          {historyLoading ? (
            <p>加载中...</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>时间</th>
                  <th>范围</th>
                  <th>总时长</th>
                  <th>主要分类</th>
                </tr>
              </thead>
              <tbody>
                {history.map((item) => (
                  <tr key={`${item.start}-${item.end}`}>
                    <td>{item.label}</td>
                    <td>{item.start === item.end ? item.start : `${item.start} 至 ${item.end}`}</td>
                    <td>{formatTime(item.total_seconds)}</td>
                    <td>{categoryBreakdown(item)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
};
