import React, { useEffect, useRef, useState } from 'react';
import { Download, Image as ImageIcon, Share2, ShieldCheck } from 'lucide-react';
import { Button, Card, LoadingState, PageShell, SectionHeader } from '../components/ui';
import { apiClient } from '../api/client';
import { ShareCard, ShareCardStyle } from '../components/ShareCard';
import { ShareRange, ShareSummary } from '../types';
import {
  blobToObjectUrl,
  downloadBlob,
  isNativeShareEnvironment,
  renderShareCardBlob,
  shareOrDownloadBlob,
} from '../utils/shareImage';

const rangeOptions: Array<{ value: ShareRange; label: string }> = [
  { value: 'today', label: '今日' },
  { value: 'week', label: '本周' },
  { value: 'month', label: '本月' },
];

const styleOptions: Array<{ value: ShareCardStyle; label: string }> = [
  { value: 'minimal', label: '简洁' },
  { value: 'data', label: '数据感' },
  { value: 'heatmap', label: '热力图' },
];

const rangeFilenameLabel: Record<ShareRange, string> = {
  today: 'today',
  week: 'week',
  month: 'month',
};

export const Share: React.FC = () => {
  const cardRef = useRef<HTMLDivElement>(null);
  const objectUrlRef = useRef<string | null>(null);
  const [range, setRange] = useState<ShareRange>('today');
  const [styleType, setStyleType] = useState<ShareCardStyle>('minimal');
  const [privateMode, setPrivateMode] = useState(true);
  const [hideTotal, setHideTotal] = useState(false);
  const [summary, setSummary] = useState<ShareSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [rendering, setRendering] = useState(false);
  const [status, setStatus] = useState('');
  const [generatedImageUrl, setGeneratedImageUrl] = useState<string | null>(null);
  const isNative = isNativeShareEnvironment();

  useEffect(() => {
    loadSummary();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [range]);

  useEffect(() => {
    return () => {
      if (objectUrlRef.current) {
        URL.revokeObjectURL(objectUrlRef.current);
      }
    };
  }, []);

  const loadSummary = async () => {
    setLoading(true);
    setStatus('');
    try {
      const data = await apiClient.get<ShareSummary>('/share/summary', { range });
      setSummary(data);
      setGeneratedImageUrl(null);
    } catch (error) {
      console.error('加载分享摘要失败', error);
      setStatus('加载失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  const refreshGeneratedImage = (blob: Blob) => {
    if (objectUrlRef.current) {
      URL.revokeObjectURL(objectUrlRef.current);
    }
    const url = blobToObjectUrl(blob);
    objectUrlRef.current = url;
    setGeneratedImageUrl(url);
  };

  const buildImageBlob = async () => {
    if (!cardRef.current) {
      throw new Error('分享卡片尚未就绪');
    }

    setRendering(true);
    setStatus('正在生成 PNG...');
    try {
      const blob = await renderShareCardBlob(cardRef.current);
      refreshGeneratedImage(blob);
      return blob;
    } finally {
      setRendering(false);
    }
  };

  const filename = () => {
    const date = new Date().toISOString().slice(0, 10);
    return `etime-share-${rangeFilenameLabel[range]}-${date}.png`;
  };

  const handleDownload = async () => {
    try {
      const blob = await buildImageBlob();
      downloadBlob(blob, filename());
      setStatus('PNG 已生成');
    } catch (error) {
      console.error('下载分享图失败', error);
      setStatus('生成失败，请稍后重试');
    }
  };

  const handleNativeShare = async () => {
    try {
      const blob = await buildImageBlob();
      const result = await shareOrDownloadBlob(blob, filename(), 'ETime 复盘海报');
      setStatus(result === 'shared' ? '已打开系统分享' : '已生成 PNG，可长按图片保存');
    } catch (error: any) {
      if (error?.name === 'AbortError') {
        setStatus('已取消分享');
        return;
      }
      console.error('分享图片失败', error);
      setStatus('分享失败，已保留图片预览');
    }
  };

  const togglePrivateMode = (enabled: boolean) => {
    setPrivateMode(enabled);
    if (!enabled) {
      setHideTotal(false);
    }
  };

  return (
    <PageShell
      className="share-page"
      eyebrow="分享卡片"
      title="复盘海报"
      description="把一段时间做成安静、克制、适合截图的卡片。"
      action={(
        <Button variant="secondary" onClick={loadSummary} disabled={loading}>
          <ImageIcon size={17} /> 刷新
        </Button>
      )}
    >

      <div className="share-layout">
        <Card as="aside" className="share-controls">
          <section>
            <SectionHeader title="范围" />
            <div className="share-segment">
              {rangeOptions.map((item) => (
                <button
                  key={item.value}
                  className={range === item.value ? 'active' : ''}
                  onClick={() => setRange(item.value)}
                >
                  {item.label}
                </button>
              ))}
            </div>
          </section>

          <section>
            <SectionHeader title="样式" description="不炫耀，只把节奏讲清楚。" />
            <div className="share-segment">
              {styleOptions.map((item) => (
                <button
                  key={item.value}
                  className={styleType === item.value ? 'active' : ''}
                  onClick={() => setStyleType(item.value)}
                >
                  {item.label}
                </button>
              ))}
            </div>
          </section>

          <section className="share-privacy">
            <label>
              <input
                type="checkbox"
                checked={privateMode}
                onChange={(event) => togglePrivateMode(event.target.checked)}
              />
              <span><ShieldCheck size={17} /> 隐私模式</span>
            </label>
            <label>
              <input
                type="checkbox"
                checked={privateMode && hideTotal}
                disabled={!privateMode}
                onChange={(event) => setHideTotal(event.target.checked)}
              />
              <span>隐藏总时长</span>
            </label>
          </section>

          <section className="share-actions">
            <Button onClick={handleDownload} disabled={loading || rendering || !summary}>
              <Download size={17} /> 下载 PNG
            </Button>
            {isNative && (
              <Button variant="secondary" onClick={handleNativeShare} disabled={loading || rendering || !summary}>
                <Share2 size={17} /> Android 分享
              </Button>
            )}
            {status && <p>{status}</p>}
          </section>
        </Card>

        <Card as="main" className="share-preview-panel">
          {loading ? (
            <LoadingState className="share-preview-loading" />
          ) : (
            <div className="share-preview-shell">
              <ShareCard
                ref={cardRef}
                summary={summary}
                styleType={styleType}
                privateMode={privateMode}
                hideTotal={hideTotal}
              />
            </div>
          )}

          {generatedImageUrl && (
            <div className="share-output">
              <img src={generatedImageUrl} alt="生成的 ETime 复盘海报" />
            </div>
          )}
        </Card>
      </div>
    </PageShell>
  );
};
