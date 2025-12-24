import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../api/client';
import { AuthResponse } from '../types';

export const Login: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [authMode, setAuthMode] = useState<'login' | 'register' | 'forgot'>('login');
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [resetToken, setResetToken] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [tokenRequested, setTokenRequested] = useState(false);
  const navigate = useNavigate();
  const inputClass =
    'w-full rounded-lg border border-slate-200 bg-white/90 px-4 py-3 text-slate-800 shadow-sm transition focus:border-slate-500 focus:ring-2 focus:ring-slate-500/60 focus:outline-none';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (authMode === 'register') {
        // 注册使用 JSON 方式提交，字段与后端 UserRegister 保持一致
        await apiClient.post('/auth/register', { email, username, password });
        alert('注册成功，请登录');
        setAuthMode('login');
      } else if (authMode === 'login') {
        // 登录同样使用 JSON（后端 UserLogin 是 JSON body，而不是表单）
        const response = await apiClient.post<AuthResponse>('/auth/login', {
          username,
          password,
        });

        apiClient.setToken(response.access_token);
        navigate('/timer');
      } else {
        // 忘记密码流程
        if (!tokenRequested) {
          await apiClient.post('/auth/forgot-password', { email });
          alert('重置邮件已发送，请查收邮箱获取重置令牌');
          setTokenRequested(true);
        } else {
          if (!resetToken) {
            alert('请输入邮箱收到的重置令牌');
            return;
          }
          await apiClient.post('/auth/reset-password', {
            token: resetToken,
            new_password: newPassword,
          });
          alert('密码已重置，请使用新密码登录');
          setAuthMode('login');
          setResetToken('');
          setNewPassword('');
          setTokenRequested(false);
        }
      }
    } catch (error: any) {
      const detail = error?.response?.data?.detail;
      if (typeof detail === 'string') {
        alert(detail);
      } else if (Array.isArray(detail)) {
        // FastAPI 验证错误: detail 是数组，提取 msg 字段
        const msg = detail
          .map((item: any) => item?.msg || JSON.stringify(item))
          .join('\n');
        alert(msg || '操作失败');
      } else {
        alert('操作失败');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="relative min-h-screen bg-slate-900 px-4 py-10 flex items-center justify-center login-bg"
    >
      <div className="relative z-10 w-full max-w-xl">
        <div className="rounded-2xl bg-white/95 backdrop-blur border border-white/60 shadow-2xl px-6 py-8 sm:px-8">
          <h1 className="mb-6 text-center text-3xl font-semibold tracking-[0.08em] text-slate-800">
            ETime
          </h1>

          <form onSubmit={handleSubmit} className="space-y-4">
            {authMode !== 'forgot' && (
              <div className="space-y-2">
                <label className="block text-sm font-medium text-slate-700">用户名</label>
                <input
                  className={inputClass}
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                />
              </div>
            )}

            {(authMode === 'register' || authMode === 'forgot') && (
              <div className="space-y-2">
                <label className="block text-sm font-medium text-slate-700">邮箱</label>
                <input
                  className={inputClass}
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
            )}

            {authMode === 'login' && (
              <div className="space-y-2">
                <label className="block text-sm font-medium text-slate-700">密码</label>
                <input
                  className={inputClass}
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
            )}

            {authMode === 'register' && (
              <div className="space-y-2">
                <label className="block text-sm font-medium text-slate-700">密码</label>
                <input
                  className={inputClass}
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
            )}

            {authMode === 'forgot' && tokenRequested && (
              <>
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-slate-700">重置令牌</label>
                  <input
                    className={inputClass}
                    type="text"
                    value={resetToken}
                    onChange={(e) => setResetToken(e.target.value)}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-slate-700">新密码</label>
                  <input
                    className={inputClass}
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    required
                  />
                </div>
              </>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-xl bg-slate-800 px-4 py-3 text-white font-semibold tracking-wide shadow-lg transition hover:bg-slate-900 disabled:cursor-not-allowed disabled:bg-slate-400"
            >
              {loading
                ? '处理中...'
                : authMode === 'register'
                ? '注册'
                : authMode === 'login'
                ? '登录'
                : tokenRequested
                ? '重置密码'
                : '获取重置邮件'}
            </button>
          </form>

          <div className="mt-4 space-y-2 text-center text-sm text-slate-700">
            <p className="space-x-2">
              <span>{authMode === 'login' ? '没有账号？' : authMode === 'register' ? '已有账号？' : '想起密码了？'}</span>
              <button
                className="text-slate-900 font-semibold hover:underline"
                type="button"
                onClick={() => {
                  setAuthMode(authMode === 'login' ? 'register' : 'login');
                  setResetToken('');
                  setNewPassword('');
                }}
              >
                {authMode === 'login' ? '去注册' : authMode === 'register' ? '去登录' : '去登录'}
              </button>
            </p>

            {authMode !== 'forgot' && (
              <p className="space-x-2">
                <span>忘记密码？</span>
                <button
                  className="text-slate-900 font-semibold hover:underline"
                  type="button"
                  onClick={() => {
                    setAuthMode('forgot');
                    setResetToken('');
                    setNewPassword('');
                    setTokenRequested(false);
                  }}
                >
                  找回密码
                </button>
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
