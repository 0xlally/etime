import React, { useEffect, useRef, useState } from 'react';
import { CategorySelect } from '../components/CategorySelect';
import { TimerControls } from '../components/TimerControls';
import { apiClient } from '../api/client';
import { StatsSummary, WorkTarget } from '../types';

export const Timer: React.FC = () => {
  const [categoryId, setCategoryId] = useState<number | undefined>();
  const [manualMode, setManualMode] = useState(false);
  const [manualData, setManualData] = useState({
    start_time: '',
    end_time: '',
    note: '',
  });
  const [highlightTarget, setHighlightTarget] = useState<WorkTarget | null>(null);
  const [progress, setProgress] = useState<{ actual: number; target: number; start: Date; end: Date } | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const intervalRef = useRef<number | null>(null);

  useEffect(() => {
    loadTargetsAndProgress();
  }, []);

  useEffect(() => {
    if (!isRunning) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      return;
    }

    intervalRef.current = window.setInterval(() => {
      setProgress((prev) => {
        if (!prev) return prev;
        return { ...prev, actual: prev.actual + 1 };
      });
    }, 1000);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [isRunning]);

  const loadTargetsAndProgress = async () => {
    try {
      const targetList = await apiClient.get<WorkTarget[]>('/targets');

      const activeTargets = targetList.filter((t) => (t.is_active ?? t.is_enabled ?? true));
      if (activeTargets.length === 0) {
        setHighlightTarget(null);
        setProgress(null);
        return;
      }

      const now = new Date();
      const pick = activeTargets.reduce<WorkTarget | null>((best, t) => {
        const eff = t.effective_from ? new Date(t.effective_from) : now;
        if (!best) return t;
        const bestEff = best.effective_from ? new Date(best.effective_from) : now;
        // pick the one starting soonest from now (future earliest), otherwise latest past
        const tFuture = eff.getTime() >= now.getTime();
        const bestFuture = bestEff.getTime() >= now.getTime();
        if (tFuture && bestFuture) {
          return eff < bestEff ? t : best;
        }
        if (tFuture && !bestFuture) return t;
        if (!tFuture && bestFuture) return best;
        return eff > bestEff ? t : best; // both past: choose most recent
      }, null);

      if (!pick) return;
      setHighlightTarget(pick);

      const window = computeWindow(pick, now);
      const stats = await apiClient.get<StatsSummary>('/stats/summary', {
        start: window.start.toISOString(),
        end: window.end.toISOString(),
      });

      const includeIds = pick.include_category_ids ?? pick.category_ids ?? [];
      const actual = includeIds.length > 0
        ? stats.by_category
            .filter((c) => includeIds.includes(c.category_id ?? -1))
            .reduce((sum, c) => sum + c.seconds, 0)
        : stats.total_seconds;

      setProgress({ actual, target: pick.target_seconds, start: window.start, end: window.end });
    } catch (error) {
      console.error('加载目标/进度失败', error);
      setHighlightTarget(null);
      setProgress(null);
    }
  };

  const computeWindow = (t: WorkTarget, now: Date) => {
    const eff = t.effective_from ? new Date(t.effective_from) : now;
    const period = t.period ?? t.target_type ?? 'daily';

    const startOfDay = (d: Date) => new Date(d.getFullYear(), d.getMonth(), d.getDate(), 0, 0, 0, 0);
    const endOfDay = (d: Date) => new Date(d.getFullYear(), d.getMonth(), d.getDate(), 23, 59, 59, 999);

    if (period === 'tomorrow') {
      const base = startOfDay(eff > now ? eff : new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1));
      return { start: base, end: endOfDay(base) };
    }

    if (period === 'daily') {
      const base = eff > now ? startOfDay(eff) : startOfDay(now);
      return { start: base, end: endOfDay(base) };
    }

    if (period === 'weekly') {
      const ref = eff > now ? eff : now;
      const day = ref.getDay(); // 0 Sunday
      const mondayOffset = day === 0 ? -6 : 1 - day;
      const monday = new Date(ref);
      monday.setHours(0, 0, 0, 0);
      monday.setDate(ref.getDate() + mondayOffset);
      const sunday = new Date(monday);
      sunday.setDate(monday.getDate() + 6);
      sunday.setHours(23, 59, 59, 999);
      return { start: monday, end: sunday };
    }

    // monthly
    const ref = eff > now ? eff : now;
    const first = new Date(ref.getFullYear(), ref.getMonth(), 1, 0, 0, 0, 0);
    const last = new Date(ref.getFullYear(), ref.getMonth() + 1, 0, 23, 59, 59, 999);
    return { start: first, end: last };
  };

  const formatTime = (seconds: number) => {
    const total = Math.max(0, Math.floor(seconds));
    const h = Math.floor(total / 3600);
    const m = Math.floor((total % 3600) / 60);
    if (h === 0) return `${m} 分钟`;
    return `${h} 小时 ${m} 分钟`;
  };

  const handleManualSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!categoryId) {
      alert('请选择分类');
      return;
    }

    if (!manualData.start_time || !manualData.end_time) {
      alert('请选择开始和结束时间');
      return;
    }

    try {
      // Keep local time (browser) but append seconds for backend parsing
      const startStr = manualData.start_time.includes(':')
        ? `${manualData.start_time}:00`
        : manualData.start_time;
      const endStr = manualData.end_time.includes(':')
        ? `${manualData.end_time}:00`
        : manualData.end_time;

      await apiClient.post('/sessions/manual', {
        category_id: categoryId,
        start_time: startStr,
        end_time: endStr,
        note: manualData.note || undefined,
      });
      alert('手动补录成功');
      setManualData({ start_time: '', end_time: '', note: '' });
    } catch (error: any) {
      const detail = error?.response?.data?.detail;
      if (Array.isArray(detail)) {
        alert(detail.map((d: any) => d.msg).join(', '));
      } else {
        alert(typeof detail === 'string' ? detail : '补录失败');
      }
    }
  };

  return (
    <div className="timer-page">
      <h1>计时器</h1>

      <p className="mb-6 rounded-xl border-l-4 border-slate-800 bg-gradient-to-r from-white/90 to-slate-50 px-4 py-3 text-slate-800 shadow">
        运用认知的力量，保持耐心与饥渴，和时间做朋友
      </p>

      {highlightTarget && progress && (
        <div className="target-highlight">
          <div className="target-ring" style={{
            background: `conic-gradient(#27ae60 ${Math.min(100, (progress.actual / progress.target) * 100)}%, #e5e7eb 0)`
          }}>
            <div className="target-ring-inner">
              <div className="target-value">
                {formatTime(progress.target - progress.actual > 0 ? progress.target - progress.actual : 0)}
              </div>
              <div className="target-label">剩余</div>
            </div>
          </div>
          <div className="target-meta">
            <div className="target-title">待完成目标：{(highlightTarget.period ?? highlightTarget.target_type ?? 'daily') === 'tomorrow' ? '明天' : (highlightTarget.period ?? highlightTarget.target_type ?? 'daily') === 'daily' ? '每日' : (highlightTarget.period ?? highlightTarget.target_type ?? 'daily') === 'weekly' ? '每周' : '每月'}</div>
            <div className="target-desc">
              目标 {formatTime(highlightTarget.target_seconds)} · 窗口 {progress.start.toLocaleDateString()} - {progress.end.toLocaleDateString()}
            </div>
            <div className="target-progress">已完成 {formatTime(progress.actual)} / {formatTime(progress.target)}</div>
          </div>
        </div>
      )}

      <div className="timer-section">
        <CategorySelect value={categoryId} onChange={setCategoryId} />

        <div className="mode-toggle">
          <button
            className={!manualMode ? 'active' : ''}
            onClick={() => setManualMode(false)}
          >
            实时计时
          </button>
          <button
            className={manualMode ? 'active' : ''}
            onClick={() => setManualMode(true)}
          >
            手动补录
          </button>
        </div>

        {!manualMode ? (
          <TimerControls
            categoryId={categoryId}
            onSessionStart={loadTargetsAndProgress}
            onSessionEnd={loadTargetsAndProgress}
            onRunningChange={(running, initialElapsed = 0) => {
              setIsRunning(running);
              if (running && initialElapsed > 0) {
                setProgress((prev) =>
                  prev ? { ...prev, actual: prev.actual + initialElapsed } : prev,
                );
              }
              if (!running) {
                setProgress((prev) => (prev ? { ...prev } : prev));
              }
            }}
          />
        ) : (
          <form onSubmit={handleManualSubmit} className="manual-form">
            <div className="form-group">
              <label>开始时间</label>
              <input
                type="datetime-local"
                step="60"
                value={manualData.start_time}
                onChange={(e) =>
                  setManualData({ ...manualData, start_time: e.target.value })
                }
                required
              />
            </div>

            <div className="form-group">
              <label>结束时间</label>
              <input
                type="datetime-local"
                step="60"
                value={manualData.end_time}
                onChange={(e) =>
                  setManualData({ ...manualData, end_time: e.target.value })
                }
                required
              />
            </div>

            <div className="form-group">
              <label>备注（可选）</label>
              <textarea
                value={manualData.note}
                onChange={(e) => setManualData({ ...manualData, note: e.target.value })}
                rows={3}
              />
            </div>

            <button type="submit">提交补录</button>
          </form>
        )}
      </div>
    </div>
  );
};
