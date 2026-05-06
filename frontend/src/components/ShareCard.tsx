import React from 'react';
import { ShareSummary } from '../types';

export type ShareCardStyle = 'minimal' | 'data' | 'heatmap';

interface ShareCardProps {
  summary: ShareSummary | null;
  styleType: ShareCardStyle;
  privateMode: boolean;
  hideTotal: boolean;
}

const rangeLabels: Record<ShareSummary['range'], string> = {
  today: '今日',
  week: '本周',
  month: '本月',
};

const styleLabels: Record<ShareCardStyle, string> = {
  minimal: '简洁',
  data: '数据感',
  heatmap: '热力图',
};

const formatDuration = (seconds: number) => {
  const total = Math.max(0, Math.floor(seconds || 0));
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  if (hours === 0) return `${minutes} 分钟`;
  if (minutes === 0) return `${hours} 小时`;
  return `${hours} 小时 ${minutes} 分钟`;
};

const formatPercent = (value: number) => `${Math.round(value * 100)}%`;

const categoryAlias = (index: number) => `分类 ${String.fromCharCode(65 + index)}`;

const heatmapColor = (seconds: number) => {
  if (seconds <= 0) return '#ece9df';
  if (seconds < 1800) return '#d9ddcf';
  if (seconds < 3600) return '#b8c2a9';
  if (seconds < 3 * 3600) return '#879678';
  return '#596d58';
};

const generatedLabel = (value?: string) => {
  const date = value ? new Date(value) : new Date();
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  });
};

export const ShareCard = React.forwardRef<HTMLDivElement, ShareCardProps>(
  ({ summary, styleType, privateMode, hideTotal }, ref) => {
    const categories = summary?.by_category ?? [];
    const topCategory = categories[0] ?? null;
    const target = summary?.target_completion;
    const totalSeconds = summary?.total_seconds ?? 0;
    const hasData = totalSeconds > 0;
    const safeHideTotal = privateMode && hideTotal;

    const categoryName = (index: number, name?: string | null) => {
      if (privateMode) return categoryAlias(index);
      return name || '未分类';
    };

    const targetText = () => {
      if (!target || target.status === 'no_target') return '未设置';
      if (target.status === 'completed') return '已完成';
      return `${target.completed_count}/${target.total_count}`;
    };

    const targetSubText = () => {
      if (!target || target.status === 'no_target') return '目标保持空白';
      const first = target.items[0];
      if (!first) return '目标保持空白';
      if (safeHideTotal) return `${Math.round(first.progress_ratio * 100)}%`;
      return `${formatDuration(first.actual_seconds)} / ${formatDuration(first.target_seconds)}`;
    };

    return (
      <div ref={ref} className={`share-card share-card-${styleType}`}>
        <header className="share-card-head">
          <div>
            <span>ETime</span>
            <strong>{summary ? rangeLabels[summary.range] : '复盘卡片'}</strong>
          </div>
          <time>{generatedLabel(summary?.generated_at)}</time>
        </header>

        <section className="share-card-hero">
          <div>
            <span>时间投入</span>
            <strong>{safeHideTotal ? '已隐藏' : formatDuration(totalSeconds)}</strong>
          </div>
          <small>{styleLabels[styleType]}记录</small>
        </section>

        <section className="share-card-metrics">
          <div>
            <span>最多分类</span>
            <strong>{topCategory ? categoryName(0, topCategory.category_name) : '暂无'}</strong>
            <small>{topCategory ? formatPercent(topCategory.percent) : '0%'}</small>
          </div>
          <div>
            <span>目标状态</span>
            <strong>{targetText()}</strong>
            <small>{targetSubText()}</small>
          </div>
          <div>
            <span>连续记录</span>
            <strong>{summary?.streak_days ?? 0} 天</strong>
            <small>{hasData ? '节奏稳定' : '慢慢开始'}</small>
          </div>
        </section>

        <section className="share-card-section">
          <div className="share-card-section-head">
            <strong>分类占比</strong>
            <span>{categories.length} 项</span>
          </div>
          {categories.length === 0 ? (
            <div className="share-card-empty">还没有记录，开始和时间做朋友。</div>
          ) : (
            <div className="share-card-categories">
              {categories.slice(0, 5).map((item, index) => (
                <div className="share-card-category" key={item.category_id ?? `none-${index}`}>
                  <div>
                    <span style={{ background: item.category_color || '#64748b' }} />
                    <strong>{categoryName(index, item.category_name)}</strong>
                    <em>{safeHideTotal ? formatPercent(item.percent) : formatDuration(item.seconds)}</em>
                  </div>
                  <progress value={Math.max(0.02, item.percent)} max={1} />
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="share-card-section share-card-heatmap-block">
          <div className="share-card-section-head">
            <strong>热力预览</strong>
            <span>{summary ? rangeLabels[summary.range] : ''}</span>
          </div>
          <div className="share-card-heatmap">
            {(summary?.heatmap_preview ?? []).map((day) => (
              <span
                key={day.date}
                title={day.date}
                style={{ background: heatmapColor(day.total_seconds) }}
              />
            ))}
          </div>
        </section>

        <footer className="share-card-foot">
          <span>生成自 ETime</span>
          <strong>{privateMode ? '隐私模式' : '复盘海报'}</strong>
        </footer>
      </div>
    );
  }
);

ShareCard.displayName = 'ShareCard';
