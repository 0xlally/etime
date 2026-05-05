import React, { useEffect, useState } from 'react';
import { disciplineMode, DisciplineStatus } from '../native/disciplineMode';

export const Discipline: React.FC = () => {
  const [status, setStatus] = useState<DisciplineStatus | null>(null);
  const [limitMinutes, setLimitMinutes] = useState(120);
  const [password, setPassword] = useState('');
  const [disablePassword, setDisablePassword] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const refreshStatus = async () => {
    const nextStatus = await disciplineMode.getStatus();
    setStatus(nextStatus);
    if (nextStatus.limitMinutes > 0) {
      setLimitMinutes(nextStatus.limitMinutes);
    }
  };

  useEffect(() => {
    refreshStatus().catch(() => {
      setStatus(null);
      setMessage('无法读取自律模式状态');
    });
  }, []);

  const runAction = async (action: () => Promise<DisciplineStatus>, successMessage: string) => {
    setLoading(true);
    setMessage('');
    try {
      const nextStatus = await action();
      setStatus(nextStatus);
      setMessage(successMessage);
    } catch (error: any) {
      setMessage(error?.message || '操作失败');
    } finally {
      setLoading(false);
    }
  };

  const handleEnable = (event: React.FormEvent) => {
    event.preventDefault();
    runAction(
      () => disciplineMode.configure({ limitMinutes, password }),
      '自律模式已开启'
    ).then(() => setPassword(''));
  };

  const handleDisable = (event: React.FormEvent) => {
    event.preventDefault();
    runAction(
      () => disciplineMode.disable({ password: disablePassword }),
      '自律模式已关闭'
    ).then(() => setDisablePassword(''));
  };

  if (status && !status.supported) {
    return (
      <div className="discipline-page">
        <section className="discipline-panel">
          <h1>自律模式</h1>
          <p>自律模式仅支持 Android 客户端。</p>
        </section>
      </div>
    );
  }

  return (
    <div className="discipline-page">
      <section className="discipline-panel">
        <div className="discipline-head">
          <div>
            <h1>自律模式</h1>
            <p>统计今日手机使用时长，超过上限后显示悬浮提醒。</p>
          </div>
          <button type="button" onClick={refreshStatus} disabled={loading}>
            刷新
          </button>
        </div>

        <div className="discipline-status-grid">
          <div>
            <span>状态</span>
            <strong>{status?.enabled ? '已开启' : '未开启'}</strong>
          </div>
          <div>
            <span>今日使用</span>
            <strong>{status?.usageTodayMinutes ?? 0} 分钟</strong>
          </div>
          <div>
            <span>上限</span>
            <strong>{status?.limitMinutes ? `${status.limitMinutes} 分钟` : '未设置'}</strong>
          </div>
          <div>
            <span>后台监控</span>
            <strong>{status?.serviceRunning ? '运行中' : '未运行'}</strong>
          </div>
        </div>

        <div className="discipline-permissions">
          <div className={status?.usageAccessGranted ? 'ready' : ''}>
            <span>使用情况访问</span>
            <strong>{status?.usageAccessGranted ? '已授权' : '未授权'}</strong>
            <button
              type="button"
              onClick={() => runAction(disciplineMode.requestUsageAccess, '已打开系统授权页，授权后返回刷新状态')}
              disabled={loading}
            >
              去授权
            </button>
          </div>
          <div className={status?.overlayPermissionGranted ? 'ready' : ''}>
            <span>悬浮窗权限</span>
            <strong>{status?.overlayPermissionGranted ? '已授权' : '未授权'}</strong>
            <button
              type="button"
              onClick={() => runAction(disciplineMode.requestOverlayAccess, '已打开悬浮窗授权页，授权后返回刷新状态')}
              disabled={loading}
            >
              去授权
            </button>
          </div>
        </div>

        <form className="discipline-form" onSubmit={handleEnable}>
          <h2>设置提醒</h2>
          <label>
            每日最多手机使用时长（分钟）
            <input
              type="number"
              min={1}
              max={1440}
              value={limitMinutes}
              onChange={(event) => setLimitMinutes(Number(event.target.value))}
              required
            />
          </label>
          <label>
            解锁密码
            <input
              type="password"
              minLength={4}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </label>
          <button type="submit" disabled={loading}>
            保存并开启
          </button>
        </form>

        {status?.enabled && (
          <form className="discipline-form danger" onSubmit={handleDisable}>
            <h2>关闭自律模式</h2>
            <label>
              输入解锁密码
              <input
                type="password"
                value={disablePassword}
                onChange={(event) => setDisablePassword(event.target.value)}
                required
              />
            </label>
            <button type="submit" disabled={loading}>
              关闭
            </button>
          </form>
        )}

        {message && <p className="discipline-message">{message}</p>}
      </section>
    </div>
  );
};
