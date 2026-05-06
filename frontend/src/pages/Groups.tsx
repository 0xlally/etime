import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Copy, LogOut, MessageCircle, Send, Share2, Users } from 'lucide-react';
import { apiClient } from '../api/client';
import { Group, GroupMember, GroupMessage, GroupStatusMetadata } from '../types';

const POLL_INTERVAL_MS = 7000;
const MAX_MESSAGE_LENGTH = 1000;

const formatSeconds = (seconds?: number) => {
  const total = Math.max(0, Math.floor(seconds || 0));
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  if (hours === 0) return `${minutes} 分钟`;
  if (minutes === 0) return `${hours} 小时`;
  return `${hours} 小时 ${minutes} 分钟`;
};

const formatTime = (value: string) =>
  new Date(value).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });

const roleLabel = (role?: string | null) => {
  if (role === 'owner') return '组长';
  if (role === 'admin') return '管理员';
  return '成员';
};

const StatusShareCard: React.FC<{ message: GroupMessage }> = ({ message }) => {
  const metadata = message.metadata_json as GroupStatusMetadata | null | undefined;
  const topName = metadata?.top_category?.category_name || '暂无';

  return (
    <div className="group-status-card">
      <div>
        <span>今日状态</span>
        <strong>{formatSeconds(metadata?.total_seconds)}</strong>
      </div>
      <p>{message.content}</p>
      <div className="group-status-grid">
        <span>目标 {metadata?.target_completed_count ?? 0}/{metadata?.target_total_count ?? 0}</span>
        <span>连续 {metadata?.streak_days ?? 0} 天</span>
        <span>Top {topName}</span>
      </div>
    </div>
  );
};

const MessageBubble: React.FC<{ message: GroupMessage }> = ({ message }) => {
  if (message.message_type === 'system') {
    return <div className="group-system-message">{message.content}</div>;
  }

  return (
    <article className={`group-message group-message-${message.message_type}`}>
      <header>
        <strong>{message.username}</strong>
        <time>{formatTime(message.created_at)}</time>
      </header>
      {message.message_type === 'status_share' ? (
        <StatusShareCard message={message} />
      ) : message.message_type === 'card_share' ? (
        <div className="group-card-share">
          <span>复盘卡片</span>
          <p>{message.content}</p>
        </div>
      ) : (
        <p>{message.content}</p>
      )}
    </article>
  );
};

export const Groups: React.FC = () => {
  const [groups, setGroups] = useState<Group[]>([]);
  const [publicGroups, setPublicGroups] = useState<Group[]>([]);
  const [selectedGroupId, setSelectedGroupId] = useState<number | null>(null);
  const [members, setMembers] = useState<GroupMember[]>([]);
  const [messages, setMessages] = useState<GroupMessage[]>([]);
  const [messageText, setMessageText] = useState('');
  const [inviteCode, setInviteCode] = useState('');
  const [requestName, setRequestName] = useState('');
  const [requestDescription, setRequestDescription] = useState('');
  const [loadingGroups, setLoadingGroups] = useState(false);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [posting, setPosting] = useState(false);
  const [notice, setNotice] = useState('');
  const messageEndRef = useRef<HTMLDivElement | null>(null);

  const selectedGroup = useMemo(
    () => groups.find((group) => group.id === selectedGroupId) ?? null,
    [groups, selectedGroupId],
  );

  useEffect(() => {
    loadGroups();
  }, []);

  useEffect(() => {
    if (groups.length === 0) {
      setSelectedGroupId(null);
      return;
    }
    if (!selectedGroupId || !groups.some((group) => group.id === selectedGroupId)) {
      setSelectedGroupId(groups[0].id);
    }
  }, [groups, selectedGroupId]);

  useEffect(() => {
    if (!selectedGroupId) {
      setMembers([]);
      setMessages([]);
      return;
    }

    let cancelled = false;
    const loadCurrent = async (showLoading = false) => {
      if (showLoading) setLoadingMessages(true);
      try {
        const [memberData, messageData] = await Promise.all([
          apiClient.get<GroupMember[]>(`/groups/${selectedGroupId}/members`),
          apiClient.get<GroupMessage[]>(`/groups/${selectedGroupId}/messages`, { limit: 50 }),
        ]);
        if (!cancelled) {
          setMembers(memberData);
          setMessages(messageData);
        }
      } catch (error) {
        if (!cancelled) {
          console.error('加载小组消息失败', error);
          setNotice('加载小组消息失败');
        }
      } finally {
        if (!cancelled && showLoading) setLoadingMessages(false);
      }
    };

    void loadCurrent(true);
    const timer = window.setInterval(() => {
      void loadCurrent(false);
    }, POLL_INTERVAL_MS);

    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [selectedGroupId]);

  useEffect(() => {
    messageEndRef.current?.scrollIntoView({ block: 'end' });
  }, [messages.length, selectedGroupId]);

  const loadGroups = async () => {
    setLoadingGroups(true);
    try {
      const [data, publicData] = await Promise.all([
        apiClient.get<Group[]>('/groups'),
        apiClient.get<Group[]>('/groups/public'),
      ]);
      setGroups(data);
      setPublicGroups(publicData);
    } catch (error) {
      console.error('加载小组失败', error);
      setNotice('加载小组失败');
    } finally {
      setLoadingGroups(false);
    }
  };

  const refreshCurrent = async () => {
    if (!selectedGroupId) return;
    const [groupData, memberData, messageData] = await Promise.all([
      apiClient.get<Group>(`/groups/${selectedGroupId}`),
      apiClient.get<GroupMember[]>(`/groups/${selectedGroupId}/members`),
      apiClient.get<GroupMessage[]>(`/groups/${selectedGroupId}/messages`, { limit: 50 }),
    ]);
    setGroups((prev) => prev.map((group) => (group.id === groupData.id ? groupData : group)));
    setMembers(memberData);
    setMessages(messageData);
  };

  const handleRequestPublicGroup = async (event: React.FormEvent) => {
    event.preventDefault();
    const name = requestName.trim();
    if (!name) {
      setNotice('请输入小组名称');
      return;
    }

    try {
      await apiClient.post('/groups/public-requests', {
        name,
        description: requestDescription.trim() || null,
      });
      setRequestName('');
      setRequestDescription('');
      setNotice('申请已提交给管理员');
    } catch (error: any) {
      setNotice(error?.response?.data?.detail || '提交申请失败');
    }
  };

  const joinByInviteCode = async (code: string) => {
    if (!code) {
      setNotice('请输入邀请码');
      return;
    }

    try {
      const group = await apiClient.post<Group>('/groups/join', { invite_code: code });
      setGroups((prev) => {
        const exists = prev.some((item) => item.id === group.id);
        return exists ? prev.map((item) => (item.id === group.id ? group : item)) : [group, ...prev];
      });
      setPublicGroups((prev) => prev.map((item) => (item.id === group.id ? group : item)));
      setSelectedGroupId(group.id);
      setInviteCode('');
      setNotice('已加入小组');
    } catch (error: any) {
      setNotice(error?.response?.data?.detail || '加入小组失败');
    }
  };

  const handleJoinGroup = async (event: React.FormEvent) => {
    event.preventDefault();
    await joinByInviteCode(inviteCode.trim());
  };

  const handleJoinPublicGroup = async (group: Group) => {
    await joinByInviteCode(group.invite_code);
  };

  const handleSendMessage = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!selectedGroupId) return;
    const content = messageText.trim();
    if (!content) return;
    if (content.length > MAX_MESSAGE_LENGTH) {
      setNotice(`消息不能超过 ${MAX_MESSAGE_LENGTH} 字`);
      return;
    }

    try {
      setPosting(true);
      await apiClient.post<GroupMessage>(`/groups/${selectedGroupId}/messages`, { content });
      setMessageText('');
      await refreshCurrent();
    } catch (error: any) {
      setNotice(error?.response?.data?.detail || '发送失败');
    } finally {
      setPosting(false);
    }
  };

  const handleShareStatus = async () => {
    if (!selectedGroupId) return;
    try {
      setPosting(true);
      await apiClient.post<GroupMessage>(`/groups/${selectedGroupId}/share-status`);
      await refreshCurrent();
      setNotice('今日状态已分享到小组');
    } catch (error: any) {
      setNotice(error?.response?.data?.detail || '分享今日状态失败');
    } finally {
      setPosting(false);
    }
  };

  const handleShareCard = async () => {
    if (!selectedGroupId) return;
    try {
      setPosting(true);
      await apiClient.post<GroupMessage>(`/groups/${selectedGroupId}/share-card`, {
        content: '分享了一张今日复盘卡片',
        metadata_json: {
          source: 'groups_mvp',
          shared_at: new Date().toISOString(),
        },
      });
      await refreshCurrent();
      setNotice('复盘卡片摘要已分享到小组');
    } catch (error: any) {
      setNotice(error?.response?.data?.detail || '分享复盘卡片失败');
    } finally {
      setPosting(false);
    }
  };

  const handleCopyInviteCode = async () => {
    if (!selectedGroup) return;
    await navigator.clipboard.writeText(selectedGroup.invite_code);
    setNotice('邀请码已复制');
  };

  const handleLeaveGroup = async () => {
    if (!selectedGroup || selectedGroup.my_role === 'owner') {
      setNotice('MVP 阶段组长不能直接退出小组');
      return;
    }
    if (!window.confirm(`确认退出「${selectedGroup.name}」？`)) return;
    try {
      await apiClient.post(`/groups/${selectedGroup.id}/leave`);
      setGroups((prev) => prev.filter((group) => group.id !== selectedGroup.id));
      setNotice('已退出小组');
    } catch (error: any) {
      setNotice(error?.response?.data?.detail || '退出小组失败');
    }
  };

  return (
    <div className="groups-page">
      <aside className="groups-sidebar">
        <div className="groups-sidebar-head">
          <div>
            <span>轻量学习群</span>
            <h1>小组</h1>
          </div>
          <Users size={24} />
        </div>

        <div className="public-groups">
          <strong>公开邀请码</strong>
          {publicGroups.length === 0 ? (
            <p>暂无公开小组</p>
          ) : (
            publicGroups.map((group) => (
              <article key={group.id} className="public-group-card">
                <div>
                  <span>{group.name}</span>
                  <code>{group.invite_code}</code>
                  <small>{group.member_count} 人 · {group.my_role ? '已加入' : '公开'}</small>
                </div>
                <button type="button" onClick={() => handleJoinPublicGroup(group)} disabled={Boolean(group.my_role)}>
                  {group.my_role ? '已加入' : '申请加入'}
                </button>
              </article>
            ))
          )}
        </div>

        <form className="group-mini-form" onSubmit={handleJoinGroup}>
          <strong>加入小组</strong>
          <input
            value={inviteCode}
            onChange={(event) => setInviteCode(event.target.value.toUpperCase())}
            maxLength={32}
            placeholder="输入邀请码"
          />
          <button type="submit">加入</button>
        </form>

        <form className="group-mini-form" onSubmit={handleRequestPublicGroup}>
          <strong>申请公开小组</strong>
          <input
            value={requestName}
            onChange={(event) => setRequestName(event.target.value)}
            maxLength={100}
            placeholder="想公开的小组名"
          />
          <textarea
            value={requestDescription}
            onChange={(event) => setRequestDescription(event.target.value)}
            maxLength={500}
            rows={2}
            placeholder="申请说明，可选"
          />
          <button type="submit">提交申请</button>
        </form>

        <div className="groups-list">
          {loadingGroups ? (
            <p>加载中...</p>
          ) : groups.length === 0 ? (
            <div className="groups-empty">
              <MessageCircle size={26} />
              <p>暂无小组。可以加入左侧公开考研小组，或输入邀请码加入同伴。</p>
            </div>
          ) : (
            groups.map((group) => (
              <button
                key={group.id}
                type="button"
                className={group.id === selectedGroupId ? 'active' : ''}
                onClick={() => setSelectedGroupId(group.id)}
              >
                <strong>{group.name}</strong>
                <span>{group.member_count} 人 · {roleLabel(group.my_role)}</span>
              </button>
            ))
          )}
        </div>
      </aside>

      <section className="group-chat-panel">
        {!selectedGroup ? (
          <div className="group-chat-empty">
            <MessageCircle size={40} />
            <h2>先加入一个小组</h2>
            <p>公开的考研小组已经放在左侧，可以直接申请加入。</p>
          </div>
        ) : (
          <>
            <header className="group-chat-header">
              <div>
                <span>邀请码 {selectedGroup.invite_code}</span>
                <h2>{selectedGroup.name}</h2>
                <p>{selectedGroup.description || '暂无小组说明'}</p>
              </div>
              <div className="group-header-actions">
                <button type="button" onClick={handleCopyInviteCode}>
                  <Copy size={16} /> 复制邀请码
                </button>
                <button type="button" onClick={handleLeaveGroup} disabled={selectedGroup.my_role === 'owner'}>
                  <LogOut size={16} /> 退出
                </button>
              </div>
            </header>

            <div className="group-meta-row">
              <div>
                <strong>{selectedGroup.member_count}</strong>
                <span>成员</span>
              </div>
              <div>
                <strong>{roleLabel(selectedGroup.my_role)}</strong>
                <span>我的角色</span>
              </div>
              <div>
                <strong>{members.slice(0, 4).map((member) => member.username).join('、') || '暂无'}</strong>
                <span>成员预览</span>
              </div>
            </div>

            <aside className="group-member-list">
              <strong>成员列表</strong>
              {members.map((member) => (
                <span key={member.id}>{member.username} · {roleLabel(member.role)}</span>
              ))}
            </aside>

            {notice && <div className="group-notice">{notice}</div>}

            <div className="group-share-row">
              <button type="button" onClick={handleShareStatus} disabled={posting}>
                <Share2 size={16} /> 分享今日状态
              </button>
              <button type="button" onClick={handleShareCard} disabled={posting}>
                分享复盘卡片
              </button>
            </div>

            <div className="group-messages" aria-live="polite">
              {loadingMessages ? (
                <p className="group-muted">消息加载中...</p>
              ) : messages.length === 0 ? (
                <div className="group-messages-empty">还没有消息，发一句开始小组交流。</div>
              ) : (
                messages.map((message) => <MessageBubble key={message.id} message={message} />)
              )}
              <div ref={messageEndRef} />
            </div>

            <form className="group-composer" onSubmit={handleSendMessage}>
              <input
                value={messageText}
                onChange={(event) => setMessageText(event.target.value)}
                maxLength={MAX_MESSAGE_LENGTH}
                placeholder="像群聊一样发一条消息..."
              />
              <button type="submit" disabled={posting || !messageText.trim()}>
                <Send size={17} /> 发送
              </button>
            </form>
          </>
        )}
      </section>
    </div>
  );
};
