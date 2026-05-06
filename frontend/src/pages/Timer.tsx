import React, { useCallback, useEffect, useRef, useState } from 'react';
import { CategorySelect } from '../components/CategorySelect';
import { TimerControls, type TimerOfflineState } from '../components/TimerControls';
import { apiClient } from '../api/client';
import { StatsSummary, WorkTarget } from '../types';
import { getOfflineTimerSnapshot, isNetworkOnline, syncOfflineTimers } from '../utils/offlineTimer';

const getLocalDateInputValue = () => {
  const now = new Date();
  now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
  return now.toISOString().slice(0, 10);
};

export const Timer: React.FC = () => {
  const [categoryId, setCategoryId] = useState<number | undefined>();
  const [manualMode, setManualMode] = useState(false);
  const [manualData, setManualData] = useState({
    entry_date: getLocalDateInputValue(),
    hours: '',
    minutes: '',
    note: '',
  });
  const [highlightTarget, setHighlightTarget] = useState<WorkTarget | null>(null);
  const [progress, setProgress] = useState<{ actual: number; target: number; start: Date; end: Date } | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [offlineState, setOfflineState] = useState<TimerOfflineState>({
    ...getOfflineTimerSnapshot(),
    isOnline: isNetworkOnline(),
    syncing: false,
  });
  const [restoreMessage, setRestoreMessage] = useState('');
  const [syncSignal, setSyncSignal] = useState(0);
  const intervalRef = useRef<number | null>(null);
  const wasRunningRef = useRef(false);

  useEffect(() => {
    loadTargetsAndProgress();
  }, []);

  useEffect(() => {
    const refreshNetworkState = () => {
      setOfflineState((prev) => ({
        ...prev,
        ...getOfflineTimerSnapshot(),
        isOnline: isNetworkOnline(),
      }));
    };

    refreshNetworkState();
    window.addEventListener('online', refreshNetworkState);
    window.addEventListener('offline', refreshNetworkState);

    return () => {
      window.removeEventListener('online', refreshNetworkState);
      window.removeEventListener('offline', refreshNetworkState);
    };
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
        const tFuture = eff.getTime() >= now.getTime();
        const bestFuture = bestEff.getTime() >= now.getTime();
        if (tFuture && bestFuture) {
          return eff < bestEff ? t : best;
        }
        if (tFuture && !bestFuture) return t;
        if (!tFuture && bestFuture) return best;
        return eff > bestEff ? t : best;
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
      const day = ref.getDay();
      const mondayOffset = day === 0 ? -6 : 1 - day;
      const monday = new Date(ref);
      monday.setHours(0, 0, 0, 0);
      monday.setDate(ref.getDate() + mondayOffset);
      const sunday = new Date(monday);
      sunday.setDate(monday.getDate() + 6);
      sunday.setHours(23, 59, 59, 999);
      return { start: monday, end: sunday };
    }

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

    if (!manualData.entry_date) {
      alert('请选择日期');
      return;
    }

    const hours = manualData.hours === '' ? 0 : Number(manualData.hours);
    const minutes = manualData.minutes === '' ? 0 : Number(manualData.minutes);
    if (
      !Number.isFinite(hours) ||
      !Number.isFinite(minutes) ||
      hours < 0 ||
      minutes < 0 ||
      hours > 24 ||
      minutes > 59
    ) {
      alert('请输入有效的小时和分钟');
      return;
    }
    if (hours === 0 && minutes === 0) {
      alert('补录时长必须大于 0');
      return;
    }

    try {
      await apiClient.post('/sessions/manual', {
        category_id: categoryId,
        entry_date: manualData.entry_date,
        hours,
        minutes,
        note: manualData.note || undefined,
      });
      alert('手动补录成功');
      setManualData({ entry_date: getLocalDateInputValue(), hours: '', minutes: '', note: '' });
      loadTargetsAndProgress();
    } catch (error: any) {
      const detail = error?.response?.data?.detail;
      if (Array.isArray(detail)) {
        alert(detail.map((d: any) => d.msg).join(', '));
      } else {
        alert(typeof detail === 'string' ? detail : '补录失败');
      }
    }
  };

  const handleRetrySync = async () => {
    setOfflineState((prev) => ({
      ...prev,
      isOnline: isNetworkOnline(),
      syncing: true,
    }));

    const result = await syncOfflineTimers(apiClient);
    setOfflineState({
      ...result,
      isOnline: isNetworkOnline(),
      syncing: false,
    });
    setSyncSignal((value) => value + 1);
    loadTargetsAndProgress();
  };

  const handleRunningChange = useCallback((running: boolean, initialElapsed = 0) => {
    const wasRunning = wasRunningRef.current;
    wasRunningRef.current = running;
    setIsRunning(running);

    if (running && !wasRunning && initialElapsed > 0) {
      setProgress((prev) =>
        prev ? { ...prev, actual: prev.actual + initialElapsed } : prev,
      );
    }
    if (!running) {
      setProgress((prev) => (prev ? { ...prev } : prev));
    }
  }, []);

  return (
    <div className="timer-page">
      <div className="timer-shell">
        <div className="timer-header">
          <p className="timer-banner">运用认知的力量，保持耐心，和时间做朋友</p>
        </div>

        <div className="timer-sync-bar">
          <span className={`sync-pill ${offlineState.isOnline ? 'online' : 'offline'}`}>
            {offlineState.isOnline ? '在线' : '离线'}
          </span>
          {offlineState.syncing && <span className="sync-text">正在同步</span>}
          {offlineState.pendingCount > 0 && (
            <span className="sync-text">有 {offlineState.pendingCount} 条待同步记录</span>
          )}
          {offlineState.failedCount > 0 && (
            <button type="button" onClick={handleRetrySync} disabled={offlineState.syncing}>
              重试同步
            </button>
          )}
          {restoreMessage && <strong>{restoreMessage}</strong>}
        </div>

        <div className="timer-grid">
          {highlightTarget && progress && (
            <div className="ui-card target-card">
              <div
                className="target-ring"
                style={{
                  background: `conic-gradient(#27ae60 ${Math.min(100, (progress.actual / progress.target) * 100)}%, #e5e7eb 0)`,
                }}
              >
                <div className="target-ring-inner">
                  <div className="target-value">
                    {formatTime(progress.target - progress.actual > 0 ? progress.target - progress.actual : 0)}
                  </div>
                  <div className="target-label">剩余</div>
                </div>
              </div>

              <div className="target-meta">
                <div className="target-title">
                  待完成目标：
                  {(highlightTarget.period ?? highlightTarget.target_type ?? 'daily') === 'tomorrow'
                    ? '明天'
                    : (highlightTarget.period ?? highlightTarget.target_type ?? 'daily') === 'daily'
                    ? '每日'
                    : (highlightTarget.period ?? highlightTarget.target_type ?? 'daily') === 'weekly'
                    ? '每周'
                    : '每月'}
                </div>
                <div className="target-desc">
                  目标 {formatTime(highlightTarget.target_seconds)} · 窗口 {progress.start.toLocaleDateString()} - {progress.end.toLocaleDateString()}
                </div>
                <div className="target-progress">已完成 {formatTime(progress.actual)} / {formatTime(progress.target)}</div>
              </div>
            </div>
          )}

          <div className="category-split">
            <div className="ui-card category-card">
              <div className="card-head">
                <div>
                  <div className="card-eyebrow">分类</div>
                  <h3 className="card-title">选择分类</h3>
                </div>
              </div>
              <CategorySelect
                value={categoryId}
                onChange={setCategoryId}
                showCreate={false}
              />
            </div>

            <div className="ui-card category-card">
              <div className="card-head">
                <div>
                  <div className="card-eyebrow">分类</div>
                  <h3 className="card-title">新建分类</h3>
                </div>
              </div>
              <CategorySelect
                value={categoryId}
                onChange={setCategoryId}
                showSelect={false}
                showCreate
                showEdit={false}
              />
            </div>
          </div>
        </div>

        <div className="ui-card timer-card">
          <div className="mode-toggle">
            <button className={!manualMode ? 'active' : ''} onClick={() => setManualMode(false)}>
              实时计时
            </button>
            <button className={manualMode ? 'active' : ''} onClick={() => setManualMode(true)}>
              手动补录
            </button>
          </div>

          {!manualMode ? (
            <TimerControls
              categoryId={categoryId}
              syncSignal={syncSignal}
              onSessionStart={loadTargetsAndProgress}
              onSessionEnd={loadTargetsAndProgress}
              onRunningChange={handleRunningChange}
              onCategoryRestore={setCategoryId}
              onOfflineStateChange={setOfflineState}
              onRecoveredRunning={setRestoreMessage}
            />
          ) : (
            <form onSubmit={handleManualSubmit} className="manual-form">
              <div className="manual-category-field">
                <CategorySelect
                  value={categoryId}
                  onChange={setCategoryId}
                  showCreate={false}
                  label="分类"
                />
              </div>

              <div className="form-group">
                <label>日期</label>
                <input
                  type="date"
                  value={manualData.entry_date}
                  onChange={(e) =>
                    setManualData({ ...manualData, entry_date: e.target.value })
                  }
                  required
                />
              </div>

              <div className="form-group">
                <label>小时</label>
                <input
                  type="number"
                  min="0"
                  max="24"
                  step="1"
                  placeholder="0"
                  value={manualData.hours}
                  onChange={(e) =>
                    setManualData({ ...manualData, hours: e.target.value })
                  }
                />
              </div>

              <div className="form-group">
                <label>分钟</label>
                <input
                  type="number"
                  min="0"
                  max="59"
                  step="1"
                  placeholder="0"
                  value={manualData.minutes}
                  onChange={(e) => setManualData({ ...manualData, minutes: e.target.value })}
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
    </div>
  );
};
