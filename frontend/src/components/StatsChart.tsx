import React from 'react';
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface StatsData {
  name: string;
  value: number;
  color: string;
}

interface StatsChartProps {
  data: StatsData[];
  title?: string;
}

export const StatsChart: React.FC<StatsChartProps> = ({ data, title }) => {
  const formatTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  return (
    <div className="stats-chart">
      {title && <h3>{title}</h3>}
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            outerRadius={100}
            label={(entry) => `${entry.name}: ${formatTime(entry.value)}`}
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip formatter={(value: number) => formatTime(value)} />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};
