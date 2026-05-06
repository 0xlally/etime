import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Play, Square } from 'lucide-react';
import { apiClient } from '../api/client';
import { ActiveSession, QuickStartStartResponse, Session } from '../types';
import {
  OfflineTimerRecord,
  OfflineTimerSnapshot,
  calculateElapsedSeconds,
  createRunningTimerRecord,
  finishRunningTimer,
  getOfflineTimerSnapshot,
  getRunningTimer,
  isNetworkOnline,
  markTemplateDurationCompleted,
  markTimerFailed,
  removeOfflineTimerRecord,
  saveRunningTimer,
  syncOfflineTimers,
  upsertOfflineTimerRecord,
} from '../utils/offlineTimer';

export interface TimerOfflineState extends OfflineTimerSnapshot {
  isOnline: boolean;
  syncing: boolean;
}

export interface QuickStartRequest {
  requestId: number;
  templateId?: number;
  categoryId: number;
  title: string;
  durationSeconds?: number | null;
  note?: string | null;
}

interface TimerControlsProps {
  categoryId?: number;
  quickStartRequest?: QuickStartRequest | null;
  syncSignal?: number;
  onSessionStart?: () => void;
  onSessionEnd?: () => void;
  onRunningChange?: (running: boolean, initialElapsed?: number) => void;
  onCategoryRestore?: (categoryId: number | undefined) => void;
  onOfflineStateChange?: (state: TimerOfflineState) => void;
  onRecoveredRunning?: (message: string) => void;
  onQuickStartHandled?: () => void;
}

const getErrorDetail = (error: unknown) => {
  const apiError = error as { response?: { data?: { detail?: unknown } }; message?: string };
  const detail = apiError.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  return apiError.message || '请求失败';
};

const isNetworkFailure = (error: unknown) => {
  const apiError = error as { response?: unknown };
  return !apiError.response;
};

const activeMatchesLocal = (active: ActiveSession, local: OfflineTimerRecord) => {
  if (local.server_session_id && local.server_session_id === active.id) return true;
  return Boolean(local.client_generated_id && local.client_generated_id === active.client_generated_id);
};

export const TimerControls: React.FC<TimerControlsProps> = ({
  categoryId,
  quickStartRequest,
  syncSignal = 0,
  onSessionStart,
  onSessionEnd,
  onRunningChange,
  onCategoryRestore,
  onOfflineStateChange,
  onRecoveredRunning,
  onQuickStartHandled,
}) => {
  const [running, setRunning] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [multiplier, setMultiplier] = useState(1);
  const [busy, setBusy] = useState(false);
  const [currentTimer, setCurrentTimer] = useState<OfflineTimerRecord | null>(null);
  const [durationPrompt, setDurationPrompt] = useState<OfflineTimerRecord | null>(null);
  const handledQuickStartRef = useRef<number | null>(null);

  const emitOfflineState = useCallback((syncing: boolean, snapshot = getOfflineTimerSnapshot()) => {
    onOfflineStateChange?.({
      ...snapshot,
      isOnline: isNetworkOnline(),
      syncing,
    });
  }, [onOfflineStateChange]);

  const syncAndNotify = useCallback(async () => {
    emitOfflineState(true);
    const result = await syncOfflineTimers(apiClient);
    emitOfflineState(false, result);
    return result;
  }, [emitOfflineState]);

  const restoreFromActiveSession = useCallback((active: ActiveSession, showRecovery: boolean) => {
    const localRunning = getRunningTimer();
    if (localRunning && !activeMatchesLocal(active, localRunning)) {
      markTimerFailed(localRunning.local_timer_id, '服务端已有正在计时，已优先恢复服务端计时');
    }
    const matchingLocal = localRunning && activeMatchesLocal(active, localRunning) ? localRunning : null;

    const restored = saveRunningTimer(createRunningTimerRecord({
      categoryId: active.category_id,
      note: active.note,
      startedAt: active.start_time,
      createdOffline: false,
      serverSessionId: active.id,
      clientGeneratedId: active.client_generated_id,
      templateId: matchingLocal?.template_id,
      templateDurationSeconds: matchingLocal?.template_duration_seconds,
      templateCompletedAt: matchingLocal?.template_completed_at,
    }));

    const initialElapsed = active.elapsed_seconds ?? calculateElapsedSeconds(active.start_time);
    setCurrentTimer(restored);
    setRunning(true);
    setElapsed(initialElapsed);
    onCategoryRestore?.(active.category_id ?? undefined);
    onRunningChange?.(true, initialElapsed);
    if (showRecovery) {
      onRecoveredRunning?.('已为你恢复服务端正在计时');
    }
    emitOfflineState(false);
  }, [emitOfflineState, onCategoryRestore, onRecoveredRunning, onRunningChange]);

  const restoreFromLocalTimer = useCallback((local: OfflineTimerRecord, showRecovery: boolean) => {
    const initialElapsed = calculateElapsedSeconds(local.started_at);
    setCurrentTimer(local);
    setRunning(true);
    setElapsed(initialElapsed);
    onCategoryRestore?.(local.category_id);
    onRunningChange?.(true, initialElapsed);
    if (showRecovery) {
      onRecoveredRunning?.('已为你恢复上次计时');
    }
    emitOfflineState(false);
  }, [emitOfflineState, onCategoryRestore, onRecoveredRunning, onRunningChange]);

  const loadActiveOrLocal = useCallback(async (showRecovery: boolean) => {
    try {
      const active = await apiClient.get<ActiveSession | null>('/sessions/active');
      if (active) {
        restoreFromActiveSession(active, showRecovery);
        return;
      }
    } catch {
      // When the backend is unreachable, local running state is still authoritative.
    }

    const local = getRunningTimer();
    if (local) {
      restoreFromLocalTimer(local, showRecovery);
      return;
    }

    setCurrentTimer(null);
    setRunning(false);
    setElapsed(0);
    onRunningChange?.(false, 0);
    emitOfflineState(false);
  }, [emitOfflineState, onRunningChange, restoreFromActiveSession, restoreFromLocalTimer]);

  useEffect(() => {
    let cancelled = false;

    const initialize = async () => {
      await syncAndNotify();
      if (!cancelled) {
        await loadActiveOrLocal(true);
      }
    };

    const handleOnline = async () => {
      await syncAndNotify();
      if (!cancelled) {
        await loadActiveOrLocal(false);
      }
    };

    const handleOffline = () => emitOfflineState(false);

    initialize();
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      cancelled = true;
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [emitOfflineState, loadActiveOrLocal, syncAndNotify]);

  useEffect(() => {
    if (syncSignal > 0) {
      loadActiveOrLocal(false);
    }
  }, [loadActiveOrLocal, syncSignal]);

  useEffect(() => {
    let timer: number | undefined;
    if (running) {
      timer = window.setInterval(() => {
        setElapsed((seconds) => seconds + 1);
      }, 1000);
    }
    return () => {
      if (timer !== undefined) {
        clearInterval(timer);
      }
    };
  }, [running]);

  useEffect(() => {
    if (!running) {
      setDurationPrompt(null);
      return;
    }

    const timer = currentTimer ?? getRunningTimer();
    if (!timer?.template_duration_seconds) {
      setDurationPrompt(null);
      return;
    }
    if (timer.template_completed_at) {
      return;
    }

    if (elapsed >= timer.template_duration_seconds) {
      const updated = markTemplateDurationCompleted(timer.local_timer_id);
      const completedTimer = updated ?? timer;
      setCurrentTimer(completedTimer);
      setDurationPrompt(completedTimer);
    } else {
      setDurationPrompt(null);
    }
  }, [currentTimer, elapsed, running]);

  const startTimer = useCallback(async (input: {
    categoryId?: number;
    note?: string | null;
    templateId?: number;
    durationSeconds?: number | null;
  }) => {
    if (!input.categoryId) {
      alert('请先选择分类');
      return;
    }

    if (running || getRunningTimer()) {
      alert('当前已有计时，请先停止后再开始新的模板。');
      return;
    }

    setBusy(true);
    const local = saveRunningTimer(createRunningTimerRecord({
      categoryId: input.categoryId,
      note: input.note,
      templateId: input.templateId,
      templateDurationSeconds: input.durationSeconds,
      createdOffline: !isNetworkOnline(),
    }));

    setCurrentTimer(local);
    setRunning(true);
    setElapsed(0);
    onRunningChange?.(true, 0);
    onCategoryRestore?.(input.categoryId);
    emitOfflineState(false);

    if (!isNetworkOnline()) {
      setBusy(false);
      onSessionStart?.();
      return;
    }

    try {
      const started = input.templateId
        ? (await apiClient.post<QuickStartStartResponse>(`/quick-start-templates/${input.templateId}/start`, {
            client_generated_id: local.client_generated_id ?? local.local_timer_id,
            started_at: local.started_at,
          })).session
        : await apiClient.post<Session>('/sessions/start', {
            category_id: input.categoryId,
            note: input.note,
            client_generated_id: local.client_generated_id ?? local.local_timer_id,
            started_at: local.started_at,
          });

      const updated = saveRunningTimer({
        ...local,
        started_at: started.start_time,
        server_session_id: started.id,
        client_generated_id: started.client_generated_id ?? local.client_generated_id,
        created_offline: false,
      });
      setCurrentTimer(updated);
      onSessionStart?.();
    } catch (error) {
      if (isNetworkFailure(error)) {
        const offline = upsertOfflineTimerRecord({
          ...local,
          created_offline: true,
          status: 'running',
        });
        setCurrentTimer(offline);
        onSessionStart?.();
      } else {
        removeOfflineTimerRecord(local.local_timer_id);
        setCurrentTimer(null);
        setRunning(false);
        setElapsed(0);
        onRunningChange?.(false, 0);
        alert(getErrorDetail(error));
        await loadActiveOrLocal(false);
      }
    } finally {
      setBusy(false);
      emitOfflineState(false);
    }
  }, [emitOfflineState, loadActiveOrLocal, onCategoryRestore, onRunningChange, onSessionStart, running]);

  const handleStart = async () => {
    await startTimer({ categoryId });
  };

  useEffect(() => {
    if (!quickStartRequest || handledQuickStartRef.current === quickStartRequest.requestId) {
      return;
    }

    handledQuickStartRef.current = quickStartRequest.requestId;
    onQuickStartHandled?.();
    void startTimer({
      categoryId: quickStartRequest.categoryId,
      note: quickStartRequest.note,
      templateId: quickStartRequest.templateId,
      durationSeconds: quickStartRequest.durationSeconds,
    });
  }, [onQuickStartHandled, quickStartRequest, startTimer]);

  const handleStop = async () => {
    const timer = currentTimer ?? getRunningTimer();
    if (!timer) {
      setRunning(false);
      setElapsed(0);
      onRunningChange?.(false, 0);
      return;
    }

    setBusy(true);
    const ended = finishRunningTimer(timer.local_timer_id, {
      multiplier,
    }) ?? upsertOfflineTimerRecord({
      ...timer,
      ended_at: new Date().toISOString(),
      multiplier,
      status: 'ended',
    });

    setCurrentTimer(null);
    setRunning(false);
    setElapsed(0);
    onRunningChange?.(false, 0);
    emitOfflineState(false);

    if (isNetworkOnline()) {
      const result = await syncAndNotify();
      if (result.syncedCount > 0) {
        onSessionEnd?.();
      }
    } else {
      onSessionEnd?.();
    }

    if (ended.status === 'failed') {
      emitOfflineState(false);
    }
    setBusy(false);
  };

  const handleContinueAfterDuration = () => {
    setDurationPrompt(null);
  };

  const handleStopAfterDuration = async () => {
    setDurationPrompt(null);
    await handleStop();
  };

  const formatTime = (seconds: number) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const activeDurationSeconds = currentTimer?.template_duration_seconds;
  const remainingSeconds = activeDurationSeconds ? Math.max(0, activeDurationSeconds - elapsed) : null;

  return (
    <div className="timer-controls">
      {remainingSeconds !== null && (
        <div className={`template-countdown ${remainingSeconds === 0 ? 'done' : ''}`}>
          <span>模板剩余</span>
          <strong>{formatTime(remainingSeconds)}</strong>
        </div>
      )}
      <div className="timer-display">{formatTime(elapsed)}</div>
      <div className="timer-footer">
        <div className="multiplier-control">
          <label>
            系数
            <input
              type="number"
              step="0.1"
              min="0"
              max="10"
              value={multiplier}
              disabled={busy}
              onChange={(e) => setMultiplier(parseFloat(e.target.value) || 0)}
            />
          </label>
          <span className="multiplier-hint">结束后按系数折算有效时长（取整到分钟）</span>
        </div>
        <div className="timer-buttons">
          {!running ? (
            <button onClick={handleStart} disabled={busy}>
              <Play size={20} /> 开始计时
            </button>
          ) : (
            <button onClick={handleStop} className="stop" disabled={busy}>
              <Square size={20} /> 停止
            </button>
          )}
        </div>
      </div>
      {durationPrompt && (
        <div className="template-duration-modal" role="dialog" aria-modal="true" aria-label="模板时间已完成">
          <div className="template-duration-dialog">
            <h3>本次模板时间已完成</h3>
            <p>是否继续计时？继续后本次记录会保留当前计时，停止会立即结束当前 session。</p>
            <div>
              <button type="button" onClick={handleContinueAfterDuration}>
                继续计时
              </button>
              <button type="button" className="stop" onClick={handleStopAfterDuration} disabled={busy}>
                结束
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
