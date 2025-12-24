import React, { useEffect, useState } from 'react';
import { Bell } from 'lucide-react';
import { apiClient } from '../api/client';

interface Notification {
  id: number;
  message: string;
  is_read: boolean;
  created_at: string;
}

export const NotificationBell: React.FC = () => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [showDropdown, setShowDropdown] = useState(false);

  useEffect(() => {
    loadNotifications();
    // 每分钟刷新一次通知
    const interval = setInterval(loadNotifications, 60000);
    return () => clearInterval(interval);
  }, []);

  const loadNotifications = async () => {
    try {
      const data = await apiClient.get<Notification[]>('/notifications');
      setNotifications(data);
    } catch (error) {
      console.error('加载通知失败', error);
    }
  };

  const markAsRead = async (id: number) => {
    try {
      await apiClient.patch(`/notifications/${id}`, {});
      await loadNotifications();
    } catch (error) {
      console.error('标记已读失败', error);
    }
  };

  return (
    <div className="notification-bell">
      <button onClick={() => setShowDropdown(!showDropdown)} className="bell-button">
        <Bell size={20} />
      </button>

      {showDropdown && (
        <div className="dropdown">
          <h4>通知</h4>
          {notifications.length === 0 ? (
            <p>暂无通知</p>
          ) : (
            <ul>
              {notifications.map((notif) => (
                <li
                  key={notif.id}
                  className={notif.is_read ? 'read' : 'unread'}
                  onClick={() => !notif.is_read && markAsRead(notif.id)}
                >
                  <p>{notif.message}</p>
                  <small>{new Date(notif.created_at).toLocaleString()}</small>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
};
