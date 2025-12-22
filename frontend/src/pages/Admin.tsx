import React, { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import { AuditLog, PaginatedSessionsResponse, PaginatedUsersResponse } from '../types';

export const Admin: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'users' | 'sessions' | 'logs'>('users');

  // 用户管理
  const [users, setUsers] = useState<PaginatedUsersResponse | null>(null);
  const [userSearch, setUserSearch] = useState('');
  const [userPage, setUserPage] = useState(1);

  // 会话管理
  const [sessions, setSessions] = useState<PaginatedSessionsResponse | null>(null);
  const [sessionFilters, setSessionFilters] = useState({
    user_id: '',
    start: '',
    end: '',
  });
  const [sessionPage, setSessionPage] = useState(1);

  // 审计日志
  const [logs, setLogs] = useState<AuditLog[]>([]);

  useEffect(() => {
    if (activeTab === 'users') loadUsers();
    if (activeTab === 'sessions') loadSessions();
    if (activeTab === 'logs') loadLogs();
  }, [activeTab, userPage, sessionPage]);

  const loadUsers = async () => {
    try {
      const data = await apiClient.get<PaginatedUsersResponse>('/admin/users', {
        search: userSearch || undefined,
        page: userPage,
        page_size: 20,
      });
      setUsers(data);
    } catch (error) {
      console.error('加载用户失败', error);
    }
  };

  const loadSessions = async () => {
    try {
      const params: any = { page: sessionPage, page_size: 20 };
      if (sessionFilters.user_id) params.user_id = sessionFilters.user_id;
      if (sessionFilters.start) params.start = sessionFilters.start;
      if (sessionFilters.end) params.end = sessionFilters.end;

      const data = await apiClient.get<PaginatedSessionsResponse>('/admin/sessions', params);
      setSessions(data);
    } catch (error) {
      console.error('加载会话失败', error);
    }
  };

  const loadLogs = async () => {
    try {
      const data = await apiClient.get<AuditLog[]>('/admin/audit-logs');
      setLogs(data);
    } catch (error: any) {
      console.error('加载日志失败', error);
      if (error?.response?.status === 403) {
        alert('没有权限访问审计日志');
      }
    }
  };

  const toggleUserActive = async (userId: number, isActive: boolean) => {
    try {
      await apiClient.patch(`/admin/users/${userId}`, { is_active: !isActive });
      alert('用户状态已更新');
      loadUsers();
    } catch (error: any) {
      alert(error?.response?.data?.detail || '更新用户失败');
    }
  };

  const resetUserPassword = async (userId: number, username: string) => {
    const newPassword = prompt(`为用户 ${username} 设置新密码：`);
    if (!newPassword || newPassword.trim().length < 6) {
      alert('密码至少需要 6 位字符');
      return;
    }
    if (!confirm(`确认为用户 ${username} 重置密码？`)) return;

    try {
      await apiClient.post(`/admin/users/${userId}/reset-password`, {
        new_password: newPassword,
      });
      alert('密码已重置');
    } catch (error: any) {
      alert(error?.response?.data?.detail || '重置密码失败');
    }
  };

  const deleteUser = async (userId: number, username: string) => {
    if (!confirm(`确认删除用户 ${username}？此操作不可恢复！`)) return;
    const confirmText = prompt('请输入用户名以确认删除：');
    if (confirmText !== username) {
      alert('用户名不匹配，取消删除');
      return;
    }

    try {
      await apiClient.delete(`/admin/users/${userId}`);
      alert('用户已删除');
      loadUsers();
    } catch (error: any) {
      alert(error?.response?.data?.detail || '删除用户失败');
    }
  };

  const deleteSession = async (sessionId: number) => {
    if (!confirm('确认删除此会话？')) return;
    try {
      await apiClient.delete(`/admin/sessions/${sessionId}`);
      loadSessions();
    } catch (error) {
      console.error('删除会话失败', error);
    }
  };

  return (
    <div className="admin-page">
      <h1>管理员面板</h1>

      <div className="tabs">
        <button
          className={activeTab === 'users' ? 'active' : ''}
          onClick={() => setActiveTab('users')}
        >
          用户管理
        </button>
        <button
          className={activeTab === 'sessions' ? 'active' : ''}
          onClick={() => setActiveTab('sessions')}
        >
          会话管理
        </button>
        <button
          className={activeTab === 'logs' ? 'active' : ''}
          onClick={() => setActiveTab('logs')}
        >
          审计日志
        </button>
      </div>

      {activeTab === 'users' && (
        <div className="users-tab">
          <div className="search-bar">
            <input
              type="text"
              placeholder="搜索用户名或邮箱..."
              value={userSearch}
              onChange={(e) => setUserSearch(e.target.value)}
            />
            <button onClick={loadUsers}>搜索</button>
          </div>

          {users && users.users && users.users.length > 0 ? (
            <>
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>用户名</th>
                    <th>邮箱</th>
                    <th>角色</th>
                    <th>状态</th>
                    <th>创建时间</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {users.users.map((user) => (
                    <tr key={user.id}>
                      <td>{user.id}</td>
                      <td>{user.username}</td>
                      <td>{user.email}</td>
                      <td>{user.role}</td>
                      <td>{user.is_active ? '启用' : '禁用'}</td>
                      <td>{new Date(user.created_at).toLocaleDateString()}</td>
                      <td>
                        <button onClick={() => toggleUserActive(user.id, user.is_active)}>
                          {user.is_active ? '禁用' : '启用'}
                        </button>
                        {' '}
                        <button onClick={() => resetUserPassword(user.id, user.username)}>
                          重置密码
                        </button>
                        {' '}
                        <button onClick={() => deleteUser(user.id, user.username)} style={{ background: '#e74c3c' }}>
                          删除
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <div className="pagination">
                <button disabled={userPage === 1} onClick={() => setUserPage(userPage - 1)}>
                  上一页
                </button>
                <span>
                  第 {userPage} 页 / 共 {Math.ceil(users.total / 20)} 页
                </span>
                <button
                  disabled={userPage >= Math.ceil(users.total / 20)}
                  onClick={() => setUserPage(userPage + 1)}
                >
                  下一页
                </button>
              </div>
            </>
          ) : (
            <p>暂无用户数据</p>
          )}
        </div>
      )}

      {activeTab === 'sessions' && (
        <div className="sessions-tab">
          <div className="filters">
            <input
              type="number"
              placeholder="用户 ID"
              value={sessionFilters.user_id}
              onChange={(e) =>
                setSessionFilters({ ...sessionFilters, user_id: e.target.value })
              }
            />
            <input
              type="datetime-local"
              value={sessionFilters.start}
              onChange={(e) => setSessionFilters({ ...sessionFilters, start: e.target.value })}
            />
            <input
              type="datetime-local"
              value={sessionFilters.end}
              onChange={(e) => setSessionFilters({ ...sessionFilters, end: e.target.value })}
            />
            <button onClick={loadSessions}>查询</button>
          </div>

          {sessions && sessions.sessions && sessions.sessions.length > 0 ? (
            <>
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>用户</th>
                    <th>分类 ID</th>
                    <th>开始时间</th>
                    <th>结束时间</th>
                    <th>时长</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {sessions.sessions.map((session) => (
                    <tr key={session.id}>
                      <td>{session.id}</td>
                      <td>{session.username ? `${session.username} (ID:${session.user_id})` : session.user_id}</td>
                      <td>{session.category_id}</td>
                      <td>{new Date(session.start_time).toLocaleString()}</td>
                      <td>
                        {session.end_time
                          ? new Date(session.end_time).toLocaleString()
                          : '进行中'}
                      </td>
                      <td>{Math.floor((session.duration_seconds || 0) / 60)} 分钟</td>
                      <td>
                        <button onClick={() => deleteSession(session.id)}>删除</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <div className="pagination">
                <button
                  disabled={sessionPage === 1}
                  onClick={() => setSessionPage(sessionPage - 1)}
                >
                  上一页
                </button>
                <span>
                  第 {sessionPage} 页 / 共 {Math.ceil(sessions.total / 20)} 页
                </span>
                <button
                  disabled={sessionPage >= Math.ceil(sessions.total / 20)}
                  onClick={() => setSessionPage(sessionPage + 1)}
                >
                  下一页
                </button>
              </div>
            </>
          ) : (
            <p>暂无会话数据</p>
          )}
        </div>
      )}

      {activeTab === 'logs' && (
        <div className="logs-tab">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>管理员 ID</th>
                <th>操作</th>
                <th>目标类型</th>
                <th>目标 ID</th>
                <th>时间</th>
                <th>详情</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id}>
                  <td>{log.id}</td>
                  <td>{log.admin_user_id}</td>
                  <td>{log.action}</td>
                  <td>{log.target_type}</td>
                  <td>{log.target_id}</td>
                  <td>{new Date(log.created_at).toLocaleString()}</td>
                  <td>
                    <pre>{JSON.stringify(log.detail_json, null, 2)}</pre>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
