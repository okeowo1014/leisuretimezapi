import { useState, useEffect } from 'react';
import { notifications } from '../../api/endpoints';
import { timeAgo } from '../../utils/helpers';
import LoadingSpinner from '../../components/ui/LoadingSpinner';
import EmptyState from '../../components/ui/EmptyState';
import toast from 'react-hot-toast';
import {
  FiBell, FiTrash2, FiCheck, FiInfo, FiAlertCircle,
  FiCheckCircle, FiGift, FiCreditCard, FiCalendar, FiX
} from 'react-icons/fi';
import './NotificationsPage.css';

export default function NotificationsPage() {
  const [notifList, setNotifList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState(null);

  useEffect(() => {
    fetchNotifications();
  }, []);

  const fetchNotifications = async () => {
    setLoading(true);
    try {
      const { data } = await notifications.list();
      const list = Array.isArray(data) ? data : data.results || data.notifications || [];
      setNotifList(list);
    } catch (err) {
      toast.error('Failed to load notifications');
    } finally {
      setLoading(false);
    }
  };

  const handleMarkRead = async (id) => {
    try {
      await notifications.markRead(id);
      setNotifList((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true, read: true } : n))
      );
    } catch (err) {
      toast.error('Failed to mark as read');
    }
  };

  const handleDelete = async (id) => {
    setDeletingId(id);
    try {
      await notifications.delete(id);
      setNotifList((prev) => prev.filter((n) => n.id !== id));
      toast.success('Notification deleted');
    } catch (err) {
      toast.error('Failed to delete notification');
    } finally {
      setDeletingId(null);
    }
  };

  const getNotifIcon = (type) => {
    const t = type?.toLowerCase();
    if (t === 'booking' || t === 'reservation') return <FiCalendar className="notif-type-icon notif-icon-booking" />;
    if (t === 'payment' || t === 'wallet' || t === 'transaction') return <FiCreditCard className="notif-type-icon notif-icon-payment" />;
    if (t === 'offer' || t === 'promotion' || t === 'promo') return <FiGift className="notif-type-icon notif-icon-promo" />;
    if (t === 'success' || t === 'confirmed') return <FiCheckCircle className="notif-type-icon notif-icon-success" />;
    if (t === 'warning' || t === 'alert') return <FiAlertCircle className="notif-type-icon notif-icon-warning" />;
    return <FiInfo className="notif-type-icon notif-icon-info" />;
  };

  const isUnread = (notif) => {
    return !notif.is_read && !notif.read;
  };

  const unreadCount = notifList.filter(isUnread).length;

  const handleMarkAllRead = async () => {
    const unreadNotifs = notifList.filter(isUnread);
    try {
      await Promise.all(unreadNotifs.map((n) => notifications.markRead(n.id)));
      setNotifList((prev) =>
        prev.map((n) => ({ ...n, is_read: true, read: true }))
      );
      toast.success('All notifications marked as read');
    } catch (err) {
      toast.error('Failed to mark all as read');
    }
  };

  if (loading) return <LoadingSpinner message="Loading notifications..." />;

  if (!notifList.length) {
    return (
      <div className="notifications-page">
        <h1 className="notifications-page-title">Notifications</h1>
        <EmptyState
          icon={FiBell}
          title="No notifications"
          description="You're all caught up! Notifications about your bookings and account will appear here."
        />
      </div>
    );
  }

  return (
    <div className="notifications-page">
      <div className="notifications-page-header">
        <div className="notifications-title-row">
          <h1 className="notifications-page-title">Notifications</h1>
          {unreadCount > 0 && (
            <span className="notifications-unread-badge">{unreadCount} unread</span>
          )}
        </div>
        {unreadCount > 0 && (
          <button className="notifications-mark-all-btn" onClick={handleMarkAllRead}>
            <FiCheck /> Mark all as read
          </button>
        )}
      </div>

      <div className="notifications-list">
        {notifList.map((notif) => {
          const unread = isUnread(notif);

          return (
            <div
              key={notif.id}
              className={`notification-card ${unread ? 'unread' : ''}`}
              onClick={() => unread && handleMarkRead(notif.id)}
            >
              {unread && <span className="notification-unread-dot" />}

              <div className="notification-icon-wrapper">
                {getNotifIcon(notif.notification_type || notif.type)}
              </div>

              <div className="notification-content">
                <h4 className="notification-title">
                  {notif.title || notif.subject || 'Notification'}
                </h4>
                <p className="notification-message">
                  {notif.message || notif.body || notif.content || ''}
                </p>
                <span className="notification-time">
                  {timeAgo(notif.created_at || notif.date || notif.timestamp)}
                </span>
              </div>

              <div className="notification-actions">
                {unread && (
                  <button
                    className="notification-read-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleMarkRead(notif.id);
                    }}
                    title="Mark as read"
                  >
                    <FiCheck />
                  </button>
                )}
                <button
                  className="notification-delete-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDelete(notif.id);
                  }}
                  disabled={deletingId === notif.id}
                  title="Delete"
                >
                  {deletingId === notif.id ? (
                    <span className="notif-delete-spinner" />
                  ) : (
                    <FiX />
                  )}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
