import React, { useState } from 'react';
import { Play, Square } from 'lucide-react';
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
      await apiClient.post('/sessions/start', {
        category_id: categoryId,
      });
      setRunning(true);
      setElapsed(0);
      onSessionStart?.();
    } catch (error: any) {
      console.error('开始计时失败', error);
      const detail = error?.response?.data?.detail;
      alert(typeof detail === 'string' ? detail : '开始计时失败');
    }
  };

  const handleStop = async () => {
    try {
      await apiClient.post('/sessions/stop', {
        note: undefined,
      });
      setRunning(false);
      setElapsed(0);
      onSessionEnd?.();
    } catch (error: any) {
      console.error('结束计时失败', error);
      const detail = error?.response?.data?.detail;
      alert(typeof detail === 'string' ? detail : '结束计时失败');
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
          <button onClick={handleStart}>
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
