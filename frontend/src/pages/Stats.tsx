import React, { useState, useEffect } from 'react';
import { StatsChart } from '../components/StatsChart';
import { apiClient } from '../api/client';
import { StatsSummary } from '../types';

type Period = 'today' | 'week' | 'month' | 'custom';

export const Stats: React.FC = () => {
  const [period, setPeriod] = useState<Period>('today');
  const [customStart, setCustomStart] = useState('');
  const [customEnd, setCustomEnd] = useState('');
  const [summary, setSummary] = useState<StatsSummary | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadStats();
  }, [period]);

  const loadStats = async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (period === 'custom') {
        if (!customStart || !customEnd) {
          setSummary(null);
          return;
        }
        // 自定义范围：把日期扩展为当天的 00:00:00 - 23:59:59（UTC）
        params.start = `${customStart}T00:00:00Z`;
        params.end = `${customEnd}T23:59:59Z`;
      } else {
        params.range = period;
      }

      const data = await apiClient.get<StatsSummary>('/stats/summary', params);
      setSummary(data);
    } catch (error) {
      console.error('加载统计失败', error);
    } finally {
      setLoading(false);
    }
  };

  const aggregateStats = () => {
    if (!summary) return [];

    return summary.by_category.map((cat) => ({
      name: cat.category_name || '未分类',
      value: cat.seconds,
      color: cat.category_color || '#667eea',
    }));
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
      ) : !summary || summary.total_seconds === 0 ? (
        <p>暂无数据</p>
      ) : (
        <StatsChart data={aggregateStats()} title="分类占比" />
      )}
    </div>
  );
};
