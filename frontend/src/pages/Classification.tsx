import React, { useEffect, useState } from 'react';
import { StatsChart } from '../components/StatsChart';
import { apiClient } from '../api/client';
import { StatsSummary } from '../types';

type Period = 'today' | 'week' | 'month' | 'custom';

export const Classification: React.FC = () => {
  const [period, setPeriod] = useState<Period>('week');
  const [customStart, setCustomStart] = useState('');
  const [customEnd, setCustomEnd] = useState('');
  const [summary, setSummary] = useState<StatsSummary | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (period === 'custom' && (!customStart || !customEnd)) return;
    loadStats();
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
        params.start = `${customStart}T00:00:00Z`;
        params.end = `${customEnd}T23:59:59Z`;
      } else {
        params.range = period;
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
  );
};
