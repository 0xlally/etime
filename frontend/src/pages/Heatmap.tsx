import React, { useState, useEffect, useRef } from 'react';
import { HeatmapGrid } from '../components/HeatmapGrid';
import { CategorySelect } from '../components/CategorySelect';
import { apiClient } from '../api/client';
import { HeatmapDay } from '../types';

interface DayDetail {
  id: number;
  category_id: number | null;
  category_name: string | null;
  start_time: string;
  end_time: string;
  duration_seconds: number;
  note: string | null;
  source: string;
}

export const Heatmap: React.FC = () => {
  const currentYear = new Date().getFullYear();
  const today = new Date();
  const initialEnd = today.toISOString().slice(0, 10);
  const initialStart = new Date(today.getTime() - 180 * 24 * 60 * 60 * 1000)
    .toISOString()
    .slice(0, 10);

  const [year, setYear] = useState(currentYear);
  const [start, setStart] = useState(initialStart);
  const [end, setEnd] = useState(initialEnd);
  const [categoryId, setCategoryId] = useState<number | undefined>();
  const [data, setData] = useState<HeatmapDay[]>([]);
  const [selectedDay, setSelectedDay] = useState<(HeatmapDay & { sessions?: DayDetail[] }) | null>(null);
  const [loading, setLoading] = useState(false);
  const yearSyncSkipped = useRef(false);

  useEffect(() => {
    // 跳过首次挂载，之后年份切换才重置为整年范围
    if (!yearSyncSkipped.current) {
      yearSyncSkipped.current = true;
      return;
    }
    setStart(`${year}-01-01`);
    setEnd(`${year}-12-31`);
  }, [year]);

  useEffect(() => {
    loadHeatmap();
  }, [start, end, categoryId]);

  const loadHeatmap = async () => {
    setLoading(true);
    try {
      const params: any = { start, end };
      if (categoryId) {
        params.category_id = categoryId;
      }
      const heatmapData = await apiClient.get<HeatmapDay[]>('/heatmap', params);
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
      const params: any = { date: day.date };
      if (categoryId) {
        params.category_id = categoryId;
      }
      const sessions = await apiClient.get<DayDetail[]>('/heatmap/day', params);
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
      <h1>时间热力图</h1>

      <div className="year-selector">
        <button onClick={() => setYear(year - 1)}>← {year - 1}</button>
        <span>{year}</span>
        <button onClick={() => setYear(year + 1)}>{year + 1} →</button>
      </div>

      <div className="custom-range">
        <input
          type="date"
          value={start}
          onChange={(e) => setStart(e.target.value)}
        />
        <span>至</span>
        <input
          type="date"
          value={end}
          onChange={(e) => setEnd(e.target.value)}
        />
        <button onClick={loadHeatmap}>查询</button>
      </div>

      <div className="filter-section">
        <CategorySelect
          value={categoryId}
          onChange={setCategoryId}
          allowEmpty
          showCreate={false}
          label="按分类查看（可选）"
        />
      </div>

      {loading ? (
        <p>加载中...</p>
      ) : (
        <HeatmapGrid start={start} end={end} data={data} onDayClick={handleDayClick} />
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
                      <td>{session.category_name || '未分类'}</td>
                      <td>{new Date(session.start_time).toLocaleTimeString()}</td>
                      <td>{new Date(session.end_time).toLocaleTimeString()}</td>
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
