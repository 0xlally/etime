import React, { useState } from 'react';
import { Play, Square, Plus } from 'lucide-react';
import { apiClient } from '../api/client';

interface TimerControlsProps {
  categoryId?: number;
  onSessionStart?: () => void;
  onSessionEnd?: () => void;
}

export const TimerControls: React.FC<TimerControlsProps> = ({
  categoryId,
  onSessionStart,
  onSessionEnd,
}) => {
  const [running, setRunning] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState<number | null>(null);
  const [elapsed, setElapsed] = useState(0);

  React.useEffect(() => {
    let timer: number;
    if (running) {
      timer = window.setInterval(() => {
        setElapsed((e) => e + 1);
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [running]);

  const handleStart = async () => {
    if (!categoryId) {
      alert('请先选择分类');
      return;
    }
    try {
      const session = await apiClient.post<{ id: number }>('/sessions', {
        category_id: categoryId,
      });
      setCurrentSessionId(session.id);
      setRunning(true);
      setElapsed(0);
      onSessionStart?.();
    } catch (error) {
      console.error('开始计时失败', error);
    }
  };

  const handleStop = async () => {
    if (!currentSessionId) return;
    try {
      await apiClient.patch(`/sessions/${currentSessionId}`, {});
      setRunning(false);
      setCurrentSessionId(null);
      setElapsed(0);
      onSessionEnd?.();
    } catch (error) {
      console.error('结束计时失败', error);
    }
  };

  const formatTime = (seconds: number) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div className="timer-controls">
      <div className="timer-display">{formatTime(elapsed)}</div>
      <div className="timer-buttons">
        {!running ? (
          <button onClick={handleStart} disabled={!categoryId}>
            <Play size={20} /> 开始计时
          </button>
        ) : (
          <button onClick={handleStop} className="stop">
            <Square size={20} /> 停止
          </button>
        )}
      </div>
    </div>
  );
};
