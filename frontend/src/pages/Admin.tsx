import React, { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import { AdminUser, Session, AuditLog, PaginatedResponse } from '../types';

export const Admin: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'users' | 'sessions' | 'logs'>('users');

  // 用户管理
  const [users, setUsers] = useState<PaginatedResponse<AdminUser> | null>(null);
  const [userSearch, setUserSearch] = useState('');
  const [userPage, setUserPage] = useState(1);

  // 会话管理
  const [sessions, setSessions] = useState<PaginatedResponse<Session> | null>(null);
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
      const data = await apiClient.get<PaginatedResponse<AdminUser>>('/admin/users', {
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

      const data = await apiClient.get<PaginatedResponse<Session>>('/admin/sessions', params);
      setSessions(data);
    } catch (error) {
      console.error('加载会话失败', error);
    }
  };

  const loadLogs = async () => {
    try {
      const data = await apiClient.get<AuditLog[]>('/admin/audit-logs');
      setLogs(data);
    } catch (error) {
      console.error('加载日志失败', error);
    }
  };

  const toggleUserActive = async (userId: number, isActive: boolean) => {
    try {
      await apiClient.patch(`/admin/users/${userId}`, { is_active: !isActive });
      loadUsers();
    } catch (error) {
      console.error('更新用户失败', error);
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

          {users && (
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
                  {users.data.map((user) => (
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

          {sessions && (
            <>
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>用户 ID</th>
                    <th>分类 ID</th>
                    <th>开始时间</th>
                    <th>结束时间</th>
                    <th>时长</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {sessions.data.map((session) => (
                    <tr key={session.id}>
                      <td>{session.id}</td>
                      <td>{session.user_id}</td>
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
