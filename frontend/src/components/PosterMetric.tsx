import React from 'react';

interface PosterMetricProps {
  label: string;
  value: React.ReactNode;
  hint?: React.ReactNode;
}

export const PosterMetric: React.FC<PosterMetricProps> = ({ label, value, hint }) => (
  <div className="poster-metric">
    <span>{label}</span>
    <strong>{value}</strong>
    {hint && <small>{hint}</small>}
  </div>
);
