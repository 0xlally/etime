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
  const navigate = useNavigate();

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
        if (!resetToken) {
          const resp = await apiClient.post<{ reset_token?: string; message: string }>(
            '/auth/forgot-password',
            { email }
          );
          if (resp.reset_token) {
            setResetToken(resp.reset_token);
          }
          alert('重置链接已发送（当前会直接返回重置令牌供下一步使用）');
        } else {
          await apiClient.post('/auth/reset-password', {
            token: resetToken,
            new_password: newPassword,
          });
          alert('密码已重置，请使用新密码登录');
          setAuthMode('login');
          setResetToken('');
          setNewPassword('');
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
    <div className="login-page">
      <div className="login-card">
        <h1>ETime 时间追踪</h1>
        <form onSubmit={handleSubmit}>
          {authMode !== 'forgot' && (
            <div className="form-group">
              <label>用户名</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
            </div>
          )}

          {(authMode === 'register' || authMode === 'forgot') && (
            <div className="form-group">
              <label>邮箱</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
          )}

          {authMode === 'login' && (
            <div className="form-group">
              <label>密码</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
          )}

          {authMode === 'register' && (
            <div className="form-group">
              <label>密码</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
          )}

          {authMode === 'forgot' && resetToken && (
            <>
              <div className="form-group">
                <label>重置令牌（已自动填入，可复制留存）</label>
                <input type="text" value={resetToken} readOnly />
              </div>
              <div className="form-group">
                <label>新密码</label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                />
              </div>
            </>
          )}

          <button type="submit" disabled={loading}>
            {loading
              ? '处理中...'
              : authMode === 'register'
              ? '注册'
              : authMode === 'login'
              ? '登录'
              : resetToken
              ? '重置密码'
              : '获取重置链接'}
          </button>
        </form>

        <p className="toggle-mode">
          {authMode === 'login' ? '没有账号？' : authMode === 'register' ? '已有账号？' : '想起密码了？'}
          <a
            onClick={() => {
              setAuthMode(authMode === 'login' ? 'register' : 'login');
              setResetToken('');
              setNewPassword('');
            }}
          >
            {authMode === 'login' ? '去注册' : authMode === 'register' ? '去登录' : '去登录'}
          </a>
        </p>

        {authMode !== 'forgot' && (
          <p className="toggle-mode">
            忘记密码？
            <a
              onClick={() => {
                setAuthMode('forgot');
                setResetToken('');
                setNewPassword('');
              }}
            >
              找回密码
            </a>
          </p>
        )}
      </div>
    </div>
  );
};
