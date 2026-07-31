import React from 'react';
import { format, eachDayOfInterval, parseISO } from 'date-fns';
import { HeatmapDay } from '../types';

interface HeatmapGridProps {
  start: string; // YYYY-MM-DD
  end: string;   // YYYY-MM-DD
  data: HeatmapDay[];
  onDayClick: (day: HeatmapDay) => void;
  showYearTimeline?: boolean;
}

export const HeatmapGrid: React.FC<HeatmapGridProps> = ({ start, end, data, onDayClick, showYearTimeline = false }) => {
  const startDate = parseISO(start);
  const endDate = parseISO(end);
  const days = eachDayOfInterval({ start: startDate, end: endDate });
  const monthSegments = days.reduce<Array<{ key: string; label: string; dayCount: number }>>((segments, day) => {
    const key = format(day, 'yyyy-MM');
    const current = segments[segments.length - 1];
    if (current?.key === key) {
      current.dayCount += 1;
    } else {
      segments.push({ key, label: format(day, 'M月'), dayCount: 1 });
    }
    return segments;
  }, []);

  const getColorIntensity = (seconds: number): string => {
    if (seconds === 0) return '#e9f5ec';
    if (seconds < 3600) return '#c7eed2';
    if (seconds < 3 * 3600) return '#85d69c';
    if (seconds < 8 * 3600) return '#35a853';
    return '#137333';
  };

  const dataMap = new Map(data.map((d) => [d.date, d]));

  return (
    <div className="heatmap-grid">
      <div className="months-container" aria-label="横向热力图">
        <div className="heatmap-scroll-track">
          {showYearTimeline && (
            <div className="heatmap-year-timeline" aria-label="年度月份时间线">
              {monthSegments.map((month) => (
                <span key={month.key} style={{ width: `${month.dayCount * 18}px` }}>
                  {month.label}
                </span>
              ))}
            </div>
          )}
          <div className="heatmap-days">
            {days.map((day) => {
              const dateStr = format(day, 'yyyy-MM-dd');
              const dayData = dataMap.get(dateStr) || { date: dateStr, total_seconds: 0 };
              return (
                <button
                  key={dateStr}
                  type="button"
                  className="grid-cell"
                  style={{ backgroundColor: getColorIntensity(dayData.total_seconds) }}
                  onClick={() => onDayClick(dayData)}
                  title={`${dateStr}: ${Math.floor(dayData.total_seconds / 60)} 分钟`}
                />
              );
            })}
          </div>
        </div>
      </div>
      <div className="legend">
        <span>少</span>
        <div style={{ backgroundColor: '#e9f5ec' }} />
        <div style={{ backgroundColor: '#c7eed2' }} />
        <div style={{ backgroundColor: '#85d69c' }} />
        <div style={{ backgroundColor: '#35a853' }} />
        <div style={{ backgroundColor: '#137333' }} />
        <span>多</span>
      </div>
    </div>
  );
};
