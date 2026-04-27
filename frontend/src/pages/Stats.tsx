import React, { useState, useEffect } from 'react';
import { StatsChart } from '../components/StatsChart';
import { apiClient } from '../api/client';
import { HeatmapDay, StatsSummary } from '../types';
import { addDays, format, min, parseISO, startOfWeek, subWeeks } from 'date-fns';

type Period = 'today' | 'week' | 'month' | 'custom';

interface WeeklyHistoryItem {
  weekStart: string;
  weekEnd: string;
  totalSeconds: number;
}

const HISTORY_WEEKS = 12;

export const Stats: React.FC = () => {
  const [period, setPeriod] = useState<Period>('today');
  const [customStart, setCustomStart] = useState('');
  const [customEnd, setCustomEnd] = useState('');
  const [summary, setSummary] = useState<StatsSummary | null>(null);
  const [weeklyHistory, setWeeklyHistory] = useState<WeeklyHistoryItem[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadStats();
  }, [period]);

  const loadStats = async () => {
    setLoading(true);
    try {
      if (period === 'custom' && (!customStart || !customEnd)) {
        setSummary(null);
      } else {
        const params: any = {};
        if (period === 'custom') {
          // 自定义范围：把日期扩展为当天的 00:00:00 - 23:59:59（UTC）
          params.start = `${customStart}T00:00:00Z`;
          params.end = `${customEnd}T23:59:59Z`;
        } else {
          params.range = period;
        }
        const data = await apiClient.get<StatsSummary>('/stats/summary', params);
        setSummary(data);
      }

      const weekHistoryData = await loadWeeklyHistory();
      setWeeklyHistory(weekHistoryData);
    } catch (error) {
      console.error('加载统计失败', error);
    } finally {
      setLoading(false);
    }
  };

  const loadWeeklyHistory = async (): Promise<WeeklyHistoryItem[]> => {
    const now = new Date();
    const currentWeekStart = startOfWeek(now, { weekStartsOn: 1 });
    const historyStart = subWeeks(currentWeekStart, HISTORY_WEEKS - 1);

    const heatmapData = await apiClient.get<HeatmapDay[]>('/heatmap', {
      start: format(historyStart, 'yyyy-MM-dd'),
      end: format(now, 'yyyy-MM-dd'),
    });

    const secondsByDate = new Map(
      heatmapData.map((item) => [item.date, item.total_seconds])
    );

    const history: WeeklyHistoryItem[] = [];

    for (let weekOffset = 0; weekOffset < HISTORY_WEEKS; weekOffset += 1) {
      const weekStartDate = subWeeks(currentWeekStart, weekOffset);
      const naturalWeekEnd = addDays(weekStartDate, 6);
      const weekEndDate = min([naturalWeekEnd, now]);

      let totalSeconds = 0;
      for (let dayOffset = 0; dayOffset < 7; dayOffset += 1) {
        const day = addDays(weekStartDate, dayOffset);
        if (day > now) break;
        const dayKey = format(day, 'yyyy-MM-dd');
        totalSeconds += secondsByDate.get(dayKey) || 0;
      }

      history.push({
        weekStart: format(weekStartDate, 'yyyy-MM-dd'),
        weekEnd: format(weekEndDate, 'yyyy-MM-dd'),
        totalSeconds,
      });
    }

    return history;
  };

  const aggregateStats = () => {
    if (!summary) return [];

    return summary.by_category.map((cat) => ({
      name: cat.category_name || '未分类',
      value: cat.seconds,
      color: cat.category_color || '#667eea',
    }));
  };

  const formatTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  return (
    <div className="stats-page">
      <h1>统计</h1>

      <div className="period-selector">
        <button
          className={period === 'today' ? 'active' : ''}
          onClick={() => setPeriod('today')}
        >
          今日
        </button>
        <button
          className={period === 'week' ? 'active' : ''}
          onClick={() => setPeriod('week')}
        >
          本周
        </button>
        <button
          className={period === 'month' ? 'active' : ''}
          onClick={() => setPeriod('month')}
        >
          本月
        </button>
        <button
          className={period === 'custom' ? 'active' : ''}
          onClick={() => setPeriod('custom')}
        >
          自定义
        </button>
      </div>

      {period === 'custom' && (
        <div className="custom-range">
          <input
            type="date"
            value={customStart}
            onChange={(e) => setCustomStart(e.target.value)}
          />
          <span>至</span>
          <input
            type="date"
            value={customEnd}
            onChange={(e) => setCustomEnd(e.target.value)}
          />
          <button onClick={loadStats}>查询</button>
        </div>
      )}

      {loading ? (
        <p>加载中...</p>
      ) : (
        <>
          {!summary || summary.total_seconds === 0 ? (
            <p>暂无数据</p>
          ) : (
            <StatsChart data={aggregateStats()} title="分类占比" />
          )}

          <div className="weekly-history">
            <h3>过往每周时长</h3>
            <table>
              <thead>
                <tr>
                  <th>周区间（周一到周日）</th>
                  <th>总时长</th>
                </tr>
              </thead>
              <tbody>
                {weeklyHistory.map((week) => (
                  <tr key={week.weekStart}>
                    <td>
                      {format(parseISO(week.weekStart), 'yyyy/MM/dd')} - {format(parseISO(week.weekEnd), 'yyyy/MM/dd')}
                    </td>
                    <td>{formatTime(week.totalSeconds)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
};
