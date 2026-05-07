import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { Bell } from 'lucide-react';
import { apiClient } from '../api/client';
import { NotificationItem, TargetDashboard } from '../types';

const formatTime = (seconds: number) => {
  const total = Math.max(0, Math.floor(seconds || 0));
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  if (hours === 0) return `${minutes} 分钟`;
  return `${hours} 小时 ${minutes} 分钟`;
};

export const NotificationBell: React.FC = () => {
  const location = useLocation();
  const rootRef = useRef<HTMLDivElement | null>(null);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [dashboard, setDashboard] = useState<TargetDashboard | null>(null);
  const [showDropdown, setShowDropdown] = useState(false);

  useEffect(() => {
    loadNotifications();
    const interval = setInterval(loadNotifications, 60000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    setShowDropdown(false);
  }, [location.pathname]);

  useEffect(() => {
    if (!showDropdown) return;

    const handlePointerDown = (event: PointerEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) {
        setShowDropdown(false);
      }
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setShowDropdown(false);
      }
    };

    document.addEventListener('pointerdown', handlePointerDown);
    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('pointerdown', handlePointerDown);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [showDropdown]);

  const loadNotifications = async () => {
    try {
      const [notificationData, dashboardData] = await Promise.all([
        apiClient.get<NotificationItem[]>('/notifications'),
        apiClient.get<TargetDashboard>('/targets/dashboard'),
      ]);
      setNotifications(notificationData);
      setDashboard(dashboardData);
    } catch (error) {
      console.error('加载通知失败', error);
    }
  };

  const unreadCount = notifications.filter((notification) => !notification.read_at).length;

  const remaining = useMemo(() => {
    const progress = dashboard?.progress ?? [];
    return {
      today: progress
        .filter((item) => item.period === 'daily' || item.period === 'tomorrow')
        .reduce((sum, item) => sum + item.remaining_seconds, 0),
      week: progress
        .filter((item) => item.period === 'weekly')
        .reduce((sum, item) => sum + item.remaining_seconds, 0),
    };
  }, [dashboard]);

  const markAsRead = async (id: number) => {
    try {
      await apiClient.post(`/notifications/${id}/read`);
      await loadNotifications();
    } catch (error) {
      console.error('标记已读失败', error);
    }
  };

  return (
    <div className="notification-bell" ref={rootRef}>
      <button
        type="button"
        onClick={() => setShowDropdown(!showDropdown)}
        className="bell-button"
        aria-label="通知"
        aria-expanded={showDropdown}
      >
        <Bell size={20} />
        {unreadCount > 0 && <span className="badge">{unreadCount}</span>}
      </button>

      {showDropdown && (
        <div className="dropdown">
          <div className="notification-summary">
            <h4>目标提醒</h4>
            <div>
              <span>今日还差</span>
              <strong>{formatTime(remaining.today)}</strong>
            </div>
            <div>
              <span>本周还差</span>
              <strong>{formatTime(remaining.week)}</strong>
            </div>
          </div>

          {notifications.length === 0 ? (
            <p className="notification-empty">暂无通知</p>
          ) : (
            <ul>
              {notifications.slice(0, 12).map((notification) => (
                <li
                  key={notification.id}
                  className={notification.read_at ? 'read' : 'unread'}
                  onClick={() => !notification.read_at && markAsRead(notification.id)}
                >
                  <p>{notification.title}</p>
                  {notification.content && <small>{notification.content}</small>}
                  <time>{new Date(notification.created_at).toLocaleString()}</time>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
};
