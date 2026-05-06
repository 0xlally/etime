import React from 'react';
import { format, eachDayOfInterval, parseISO } from 'date-fns';
import { HeatmapDay } from '../types';

interface HeatmapGridProps {
  start: string; // YYYY-MM-DD
  end: string;   // YYYY-MM-DD
  data: HeatmapDay[];
  onDayClick: (day: HeatmapDay) => void;
}

export const HeatmapGrid: React.FC<HeatmapGridProps> = ({ start, end, data, onDayClick }) => {
  const startDate = parseISO(start);
  const endDate = parseISO(end);
  const days = eachDayOfInterval({ start: startDate, end: endDate });

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
