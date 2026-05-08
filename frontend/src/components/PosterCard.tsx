import React from 'react';

interface PosterCardProps {
  children: React.ReactNode;
  className?: string;
}

export const PosterCard: React.FC<PosterCardProps> = ({ children, className }) => (
  <section className={['poster-card', className].filter(Boolean).join(' ')}>
    {children}
  </section>
);
