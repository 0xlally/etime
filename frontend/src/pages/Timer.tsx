import React, { useState } from 'react';
import { CategorySelect } from '../components/CategorySelect';
import { TimerControls } from '../components/TimerControls';
import { apiClient } from '../api/client';

export const Timer: React.FC = () => {
  const [categoryId, setCategoryId] = useState<number>();
  const [manualMode, setManualMode] = useState(false);
  const [manualData, setManualData] = useState({
    start_time: '',
    end_time: '',
    note: '',
  });

  const handleManualSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!categoryId) {
      alert('请选择分类');
      return;
    }

    try {
      await apiClient.post('/sessions/manual', {
        category_id: categoryId,
        start_time: manualData.start_time,
        end_time: manualData.end_time,
        note: manualData.note || undefined,
      });
      alert('手动补录成功');
      setManualData({ start_time: '', end_time: '', note: '' });
    } catch (error: any) {
      alert(error.response?.data?.detail || '补录失败');
    }
  };

  return (
    <div className="timer-page">
      <h1>计时器</h1>

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
          <TimerControls categoryId={categoryId} />
        ) : (
          <form onSubmit={handleManualSubmit} className="manual-form">
            <div className="form-group">
              <label>开始时间</label>
              <input
                type="datetime-local"
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
