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
    if (seconds === 0) return '#ece9df';
    if (seconds < 3600) return '#d9ddcf';
    if (seconds < 3 * 3600) return '#b8c2a9';
    if (seconds < 8 * 3600) return '#879678';
    return '#596d58';
  };

  const dataMap = new Map(data.map((d) => [d.date, d]));

  // 按月份分组日期，用于在网格上方显示月份标签
  const monthMap = new Map<string, Date[]>();
  days.forEach((day) => {
    const monthKey = format(day, 'yyyy-MM');
    if (!monthMap.has(monthKey)) {
      monthMap.set(monthKey, []);
    }
    monthMap.get(monthKey)!.push(day);
  });

  return (
    <div className="heatmap-grid">
      <div className="months-container">
        {Array.from(monthMap.entries()).map(([monthKey, monthDays]) => (
          <div className="month-block" key={monthKey}>
            <div className="month-label">{monthKey}</div>
            <div className="grid-container">
              {monthDays.map((day) => {
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
          </div>
        ))}
      </div>
      <div className="legend">
        <span>少</span>
        <div style={{ backgroundColor: '#ece9df' }} />
        <div style={{ backgroundColor: '#d9ddcf' }} />
        <div style={{ backgroundColor: '#b8c2a9' }} />
        <div style={{ backgroundColor: '#879678' }} />
        <div style={{ backgroundColor: '#596d58' }} />
        <span>多</span>
      </div>
    </div>
  );
};
