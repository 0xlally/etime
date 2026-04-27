import React, { useEffect, useState } from 'react';
import { apiClient } from '../api/client';
import { TimeTraceEntry } from '../types';

export const TimeTrace: React.FC = () => {
  const [entries, setEntries] = useState<TimeTraceEntry[]>([]);
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [posting, setPosting] = useState(false);

  useEffect(() => {
    loadEntries();
  }, []);

  const loadEntries = async () => {
    setLoading(true);
    try {
      const data = await apiClient.get<TimeTraceEntry[]>('/time-traces');
      setEntries(data);
    } catch (error) {
      console.error('加载时痕失败', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = content.trim();
    if (!trimmed) {
      alert('请输入留言');
      return;
    }

    try {
      setPosting(true);
      const created = await apiClient.post<TimeTraceEntry>('/time-traces', { content: trimmed });
      setEntries((prev) => [created, ...prev]);
      setContent('');
    } catch (error: any) {
      const detail = error?.response?.data?.detail;
      alert(typeof detail === 'string' ? detail : '留言失败');
    } finally {
      setPosting(false);
    }
  };

  const formatTime = (value: string) =>
    new Date(value).toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });

  return (
    <div className="time-trace-page">
      <div className="time-trace-header">
        <h1>时痕</h1>
      </div>

      <form className="time-trace-form" onSubmit={handleSubmit}>
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          maxLength={2000}
          rows={4}
          placeholder="留下些什么"
        />
        <button type="submit" disabled={posting}>
          {posting ? '留下中...' : '留下时痕'}
        </button>
      </form>

      {loading ? (
        <p>加载中...</p>
      ) : entries.length === 0 ? (
        <div className="time-trace-empty">暂无时痕</div>
      ) : (
        <div className="time-trace-tree">
          {entries.map((entry) => (
            <article key={entry.id} className="time-trace-node">
              <div className="time-trace-dot" />
              <div className="time-trace-card">
                <time>{formatTime(entry.created_at)}</time>
                <p>{entry.content}</p>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
};
