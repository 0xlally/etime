import React from 'react';
import { ShareSummary } from '../types';
import { PosterBackground } from './PosterBackground';
import { PosterCard } from './PosterCard';
import { PosterMetric } from './PosterMetric';
import { ShareBackgroundPreset } from './shareBackgroundPresets';

export type ShareCardStyle = 'minimal' | 'data' | 'heatmap';

interface ShareCardProps {
  summary: ShareSummary | null;
  styleType: ShareCardStyle;
  privateMode: boolean;
  hideTotal: boolean;
  backgroundPreset: ShareBackgroundPreset;
  onBackgroundReadyChange?: (ready: boolean) => void;
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

const rangeTitleLabels: Record<ShareSummary['range'], string> = {
  today: '今日复盘',
  week: '本周复盘',
  month: '本月复盘',
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
  if (seconds <= 0) return 'rgba(255, 255, 255, 0.22)';
  if (seconds < 1800) return 'rgba(255, 255, 255, 0.42)';
  if (seconds < 3600) return 'rgba(255, 255, 255, 0.58)';
  if (seconds < 3 * 3600) return 'rgba(255, 255, 255, 0.78)';
  return 'rgba(255, 255, 255, 0.96)';
};

const splitDurationParts = (seconds: number) => {
  const total = Math.max(0, Math.floor(seconds || 0));
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  return { hours, minutes };
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
  ({
    summary,
    styleType,
    privateMode,
    hideTotal,
    backgroundPreset,
    onBackgroundReadyChange,
  }, ref) => {
    const categories = summary?.by_category ?? [];
    const topCategory = categories[0] ?? null;
    const target = summary?.target_completion;
    const totalSeconds = summary?.total_seconds ?? 0;
    const hasData = totalSeconds > 0;
    const safeHideTotal = privateMode || hideTotal;
    const accentColor = backgroundPreset.accentColor;
    const posterTone = backgroundPreset.textTone;
    const categoryTotal = categories.reduce((sum, item) => sum + item.seconds, 0);
    const topPercent = topCategory ? formatPercent(topCategory.percent) : '0%';
    const rangeLabel = summary ? rangeLabels[summary.range] : '复盘卡片';
    const titleLabel = summary ? rangeTitleLabels[summary.range] : '复盘卡片';
    const heatmapLabel = summary?.range === 'today' ? '近 4 周' : rangeLabel;
    const heatmapPreview = summary?.heatmap_preview ?? [];
    const durationParts = splitDurationParts(totalSeconds);
    const heroDuration = safeHideTotal ? null : durationParts;
    const heroPrivateText = hasData ? '专注完成' : '慢慢开始';

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
      return `${Math.round(first.progress_ratio * 100)}%`;
    };

    return (
      <div
        ref={ref}
        className={`share-card share-card-style-${styleType} share-card-tone-${posterTone}`}
        style={{ '--poster-accent': accentColor } as React.CSSProperties}
      >
        <PosterBackground
          preset={backgroundPreset}
          onLoadStateChange={onBackgroundReadyChange}
        />

        <div className="poster-content">
          <header className="share-card-head">
            <div>
              <span>ETime</span>
              <strong>{titleLabel}</strong>
            </div>
            <time>{generatedLabel(summary?.generated_at)}</time>
          </header>

          <section className="share-card-hero">
            <div>
              <span>时间投入</span>
              <strong className={heroDuration ? 'share-card-duration' : 'share-card-private-title'}>
                {heroDuration ? (
                  <>
                    <b>{heroDuration.hours}</b><i>小时</i>
                    <b>{heroDuration.minutes}</b><i>分钟</i>
                  </>
                ) : (
                  heroPrivateText
                )}
              </strong>
              <small>{hasData ? '把今天认真放进时间里' : '从一次开始，也算开始'}</small>
            </div>
            <em>{styleLabels[styleType]}记录</em>
          </section>

          <section className="share-card-metrics">
            <PosterMetric
              label="目标状态"
              value={targetText()}
              hint={targetSubText()}
            />
            <PosterMetric
              label="连续记录"
              value={`${summary?.streak_days ?? 0} 天`}
              hint={hasData ? '节奏稳定' : '慢慢开始'}
            />
            <PosterMetric
              label="投入重心"
              value={topCategory ? categoryName(0, topCategory.category_name) : '暂无'}
              hint={topPercent}
            />
          </section>

          <PosterCard className="share-card-section share-card-category-block">
            <div className="share-card-section-head">
              <strong>分类占比</strong>
              <span>{categories.length} 项</span>
            </div>
            {categories.length === 0 ? (
              <div className="share-card-empty">还没有记录，先留下今天的第一笔时间。</div>
            ) : (
              <div className="share-card-category-summary">
                <div className="share-card-category-focus">
                  <span>{topCategory ? categoryName(0, topCategory.category_name) : '暂无'}</span>
                  <strong>{topCategory ? topPercent : '0%'}</strong>
                  <small>{safeHideTotal ? '主要投入' : formatDuration(categoryTotal)}</small>
                </div>
              </div>
            )}
          </PosterCard>

          <PosterCard className="share-card-section share-card-heatmap-block">
            <div className="share-card-section-head">
              <strong>热力预览</strong>
              <span>{heatmapLabel}</span>
            </div>
            <div className="share-poster-heatmap">
              {heatmapPreview.map((day) => (
                <span
                  key={day.date}
                  title={day.date}
                  style={{ background: heatmapColor(day.total_seconds) }}
                />
              ))}
            </div>
          </PosterCard>

          <footer className="share-card-foot">
            <span>ETime · 与时间认真相处</span>
            <strong>{privateMode ? '隐私模式' : '复盘海报'}</strong>
          </footer>
        </div>
      </div>
    );
  }
);

ShareCard.displayName = 'ShareCard';
