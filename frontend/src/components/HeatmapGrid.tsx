import React from 'react';
import { format, startOfYear, eachDayOfInterval, endOfYear } from 'date-fns';
import { HeatmapDay } from '../types';

interface HeatmapGridProps {
  year: number;
  data: HeatmapDay[];
  onDayClick: (day: HeatmapDay) => void;
}

export const HeatmapGrid: React.FC<HeatmapGridProps> = ({ year, data, onDayClick }) => {
  const start = startOfYear(new Date(year, 0, 1));
  const end = endOfYear(new Date(year, 0, 1));
  const days = eachDayOfInterval({ start, end });

  const getColorIntensity = (seconds: number): string => {
    if (seconds === 0) return '#ebedf0';
    if (seconds < 1800) return '#c6e48b'; // < 30min
    if (seconds < 3600) return '#7bc96f'; // < 1h
    if (seconds < 7200) return '#239a3b'; // < 2h
    return '#196127'; // >= 2h
  };

  const dataMap = new Map(data.map((d) => [d.date, d]));

  return (
    <div className="heatmap-grid">
      <div className="grid-container">
        {days.map((day) => {
          const dateStr = format(day, 'yyyy-MM-dd');
          const dayData = dataMap.get(dateStr) || { date: dateStr, total_seconds: 0 };
          return (
            <div
              key={dateStr}
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
        <div style={{ backgroundColor: '#ebedf0' }} />
        <div style={{ backgroundColor: '#c6e48b' }} />
        <div style={{ backgroundColor: '#7bc96f' }} />
        <div style={{ backgroundColor: '#239a3b' }} />
        <div style={{ backgroundColor: '#196127' }} />
        <span>多</span>
      </div>
    </div>
  );
};
