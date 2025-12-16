import React, { useState, useEffect } from 'react';
import { HeatmapGrid } from '../components/HeatmapGrid';
import { apiClient } from '../api/client';
import { HeatmapDay, Session } from '../types';

export const Heatmap: React.FC = () => {
  const [year, setYear] = useState(new Date().getFullYear());
  const [data, setData] = useState<HeatmapDay[]>([]);
  const [selectedDay, setSelectedDay] = useState<HeatmapDay | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadHeatmap();
  }, [year]);

  const loadHeatmap = async () => {
    setLoading(true);
    try {
      const heatmapData = await apiClient.get<HeatmapDay[]>(`/heatmap/${year}`);
      setData(heatmapData);
    } catch (error) {
      console.error('加载热力图失败', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDayClick = async (day: HeatmapDay) => {
    if (day.total_seconds === 0) return;

    try {
      const sessions = await apiClient.get<Session[]>('/sessions', {
        start_time: `${day.date}T00:00:00`,
        end_time: `${day.date}T23:59:59`,
      });
      setSelectedDay({ ...day, sessions });
    } catch (error) {
      console.error('加载明细失败', error);
    }
  };

  const formatTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  return (
    <div className="heatmap-page">
      <h1>年度热力图</h1>

      <div className="year-selector">
        <button onClick={() => setYear(year - 1)}>← {year - 1}</button>
        <span>{year}</span>
        <button onClick={() => setYear(year + 1)}>{year + 1} →</button>
      </div>

      {loading ? (
        <p>加载中...</p>
      ) : (
        <HeatmapGrid year={year} data={data} onDayClick={handleDayClick} />
      )}

      {selectedDay && (
        <div className="day-detail-modal" onClick={() => setSelectedDay(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>{selectedDay.date} 详情</h3>
            <p>总时长: {formatTime(selectedDay.total_seconds)}</p>

            {selectedDay.sessions && selectedDay.sessions.length > 0 && (
              <table>
                <thead>
                  <tr>
                    <th>分类</th>
                    <th>开始时间</th>
                    <th>结束时间</th>
                    <th>时长</th>
                    <th>备注</th>
                  </tr>
                </thead>
                <tbody>
                  {selectedDay.sessions.map((session) => (
                    <tr key={session.id}>
                      <td>{session.category?.name}</td>
                      <td>{new Date(session.start_time).toLocaleTimeString()}</td>
                      <td>
                        {session.end_time
                          ? new Date(session.end_time).toLocaleTimeString()
                          : '进行中'}
                      </td>
                      <td>{formatTime(session.duration_seconds || 0)}</td>
                      <td>{session.note || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            <button onClick={() => setSelectedDay(null)}>关闭</button>
          </div>
        </div>
      )}
    </div>
  );
};
