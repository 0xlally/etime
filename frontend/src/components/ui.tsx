import React from 'react';

const joinClassNames = (...values: Array<string | false | null | undefined>) =>
  values.filter(Boolean).join(' ');

type PageShellProps = {
  eyebrow?: string;
  title: string;
  description?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
};

export const PageShell: React.FC<PageShellProps> = ({
  eyebrow,
  title,
  description,
  action,
  children,
  className,
}) => (
  <div className={joinClassNames('ui-page-shell', className)}>
    <header className="ui-page-header">
      <div>
        {eyebrow && <span className="ui-eyebrow">{eyebrow}</span>}
        <h1>{title}</h1>
        {description && <p>{description}</p>}
      </div>
      {action && <div className="ui-page-action">{action}</div>}
    </header>
    {children}
  </div>
);

type CardProps = React.HTMLAttributes<HTMLElement> & {
  as?: 'div' | 'article' | 'section' | 'aside' | 'main' | 'form';
  quiet?: boolean;
};

export const Card: React.FC<CardProps> = ({
  as: Component = 'section',
  className,
  quiet = false,
  children,
  ...props
}) => (
  <Component className={joinClassNames('ui-card', quiet && 'ui-card-quiet', className)} {...props}>
    {children}
  </Component>
);

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
};

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  className,
  type = 'button',
  children,
  ...props
}) => (
  <button type={type} className={joinClassNames('ui-button', `ui-button-${variant}`, className)} {...props}>
    {children}
  </button>
);

type SectionHeaderProps = {
  eyebrow?: string;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
};

export const SectionHeader: React.FC<SectionHeaderProps> = ({
  eyebrow,
  title,
  description,
  action,
  className,
}) => (
  <div className={joinClassNames('ui-section-header', className)}>
    <div>
      {eyebrow && <span className="ui-eyebrow">{eyebrow}</span>}
      <h2>{title}</h2>
      {description && <p>{description}</p>}
    </div>
    {action && <div className="ui-section-action">{action}</div>}
  </div>
);

type EmptyStateProps = {
  title: string;
  description?: string;
  action?: React.ReactNode;
  compact?: boolean;
  className?: string;
};

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  action,
  compact = false,
  className,
}) => (
  <div className={joinClassNames('ui-empty-state', compact && 'ui-empty-state-compact', className)}>
    <strong>{title}</strong>
    {description && <p>{description}</p>}
    {action && <div>{action}</div>}
  </div>
);

type StatCardProps = {
  label: string;
  value: React.ReactNode;
  hint?: string;
  className?: string;
};

export const StatCard: React.FC<StatCardProps> = ({ label, value, hint, className }) => (
  <Card as="article" className={joinClassNames('ui-stat-card', className)}>
    <span>{label}</span>
    <strong>{value}</strong>
    {hint && <small>{hint}</small>}
  </Card>
);

type TagProps = {
  children: React.ReactNode;
  tone?: 'neutral' | 'accent' | 'success' | 'warning' | 'danger';
  className?: string;
};

export const Tag: React.FC<TagProps> = ({ children, tone = 'neutral', className }) => (
  <span className={joinClassNames('ui-tag', `ui-tag-${tone}`, className)}>{children}</span>
);

type ProgressProps = {
  value: number;
  max?: number;
  label?: string;
  className?: string;
};

export const Progress: React.FC<ProgressProps> = ({ value, max = 100, label, className }) => {
  const percent = max <= 0 ? 0 : Math.min(100, Math.max(0, (value / max) * 100));

  return (
    <div className={joinClassNames('ui-progress', className)} aria-label={label}>
      <span style={{ width: `${percent}%` }} />
    </div>
  );
};

export const LoadingState: React.FC<{ text?: string; className?: string }> = ({
  text = '正在轻轻整理时间...',
  className,
}) => (
  <div className={joinClassNames('ui-loading', className)}>
    <span />
    <p>{text}</p>
  </div>
);
