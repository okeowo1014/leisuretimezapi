import { useState, useEffect } from 'react';
import { support } from '../../api/endpoints';
import { timeAgo, getStatusColor } from '../../utils/helpers';
import LoadingSpinner from '../../components/ui/LoadingSpinner';
import EmptyState from '../../components/ui/EmptyState';
import toast from 'react-hot-toast';
import {
  FiHelpCircle, FiPlus, FiMessageSquare, FiSend, FiX,
  FiChevronRight, FiClock, FiAlertCircle
} from 'react-icons/fi';
import './SupportPage.css';

export default function SupportPage() {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [ticketDetail, setTicketDetail] = useState(null);
  const [showNew, setShowNew] = useState(false);
  const [replyText, setReplyText] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const [newTicket, setNewTicket] = useState({
    subject: '',
    message: '',
    priority: 'medium',
  });

  useEffect(() => {
    fetchTickets();
  }, []);

  const fetchTickets = async () => {
    try {
      const { data } = await support.list();
      setTickets(Array.isArray(data) ? data : data.results || []);
    } catch {
      toast.error('Failed to load tickets');
    } finally {
      setLoading(false);
    }
  };

  const fetchTicketDetail = async (id) => {
    try {
      const { data } = await support.get(id);
      setTicketDetail(data);
      setSelectedTicket(id);
    } catch {
      toast.error('Failed to load ticket');
    }
  };

  const handleCreateTicket = async (e) => {
    e.preventDefault();
    if (!newTicket.subject.trim() || !newTicket.message.trim()) {
      toast.error('Please fill in all fields');
      return;
    }
    setSubmitting(true);
    try {
      await support.create(newTicket);
      toast.success('Ticket created');
      setShowNew(false);
      setNewTicket({ subject: '', message: '', priority: 'medium' });
      fetchTickets();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to create ticket');
    } finally {
      setSubmitting(false);
    }
  };

  const handleReply = async (e) => {
    e.preventDefault();
    if (!replyText.trim()) return;
    setSubmitting(true);
    try {
      await support.reply(selectedTicket, { message: replyText });
      toast.success('Reply sent');
      setReplyText('');
      fetchTicketDetail(selectedTicket);
    } catch {
      toast.error('Failed to send reply');
    } finally {
      setSubmitting(false);
    }
  };

  const handleCloseTicket = async () => {
    try {
      await support.close(selectedTicket);
      toast.success('Ticket closed');
      fetchTickets();
      setSelectedTicket(null);
      setTicketDetail(null);
    } catch {
      toast.error('Failed to close ticket');
    }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className="support-page">
      <div className="support-header">
        <div>
          <h1>Support</h1>
          <p>Need help? Open a ticket and we'll assist you.</p>
        </div>
        <button className="btn-new-ticket" onClick={() => setShowNew(true)}>
          <FiPlus /> New Ticket
        </button>
      </div>

      {showNew && (
        <div className="modal-overlay" onClick={() => setShowNew(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>New Support Ticket</h2>
              <button className="modal-close" onClick={() => setShowNew(false)}>
                <FiX />
              </button>
            </div>
            <form onSubmit={handleCreateTicket}>
              <div className="form-group">
                <label>Subject</label>
                <input
                  type="text"
                  value={newTicket.subject}
                  onChange={(e) => setNewTicket({ ...newTicket, subject: e.target.value })}
                  placeholder="Brief description of your issue"
                  required
                />
              </div>
              <div className="form-group">
                <label>Priority</label>
                <select
                  value={newTicket.priority}
                  onChange={(e) => setNewTicket({ ...newTicket, priority: e.target.value })}
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </div>
              <div className="form-group">
                <label>Message</label>
                <textarea
                  rows="5"
                  value={newTicket.message}
                  onChange={(e) => setNewTicket({ ...newTicket, message: e.target.value })}
                  placeholder="Describe your issue in detail..."
                  required
                />
              </div>
              <div className="modal-actions">
                <button type="button" className="btn-cancel" onClick={() => setShowNew(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-submit" disabled={submitting}>
                  {submitting ? 'Submitting...' : 'Create Ticket'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {selectedTicket && ticketDetail ? (
        <div className="ticket-detail">
          <button className="back-btn" onClick={() => { setSelectedTicket(null); setTicketDetail(null); }}>
            &larr; Back to tickets
          </button>
          <div className="ticket-detail-header">
            <div>
              <h2>{ticketDetail.subject}</h2>
              <div className="ticket-meta">
                <span className="status-badge" style={{ background: getStatusColor(ticketDetail.status) }}>
                  {ticketDetail.status}
                </span>
                <span className="priority-badge">{ticketDetail.priority} priority</span>
                <span><FiClock /> {timeAgo(ticketDetail.created_at)}</span>
              </div>
            </div>
            {ticketDetail.status !== 'closed' && (
              <button className="btn-close-ticket" onClick={handleCloseTicket}>
                Close Ticket
              </button>
            )}
          </div>

          <div className="messages-list">
            {(ticketDetail.messages || []).map((msg, i) => (
              <div key={i} className={`message ${msg.is_staff ? 'staff' : 'user'}`}>
                <div className="message-header">
                  <strong>{msg.sender_name || (msg.is_staff ? 'Support' : 'You')}</strong>
                  <span>{timeAgo(msg.created_at)}</span>
                </div>
                <p>{msg.message}</p>
              </div>
            ))}
          </div>

          {ticketDetail.status !== 'closed' && (
            <form className="reply-form" onSubmit={handleReply}>
              <textarea
                value={replyText}
                onChange={(e) => setReplyText(e.target.value)}
                placeholder="Type your reply..."
                rows="3"
              />
              <button type="submit" disabled={submitting || !replyText.trim()}>
                <FiSend /> Send
              </button>
            </form>
          )}
        </div>
      ) : tickets.length === 0 ? (
        <EmptyState
          icon={FiHelpCircle}
          title="No support tickets"
          description="You haven't created any support tickets yet."
          actionLabel="Create Ticket"
          onAction={() => setShowNew(true)}
        />
      ) : (
        <div className="tickets-list">
          {tickets.map((ticket) => (
            <div
              key={ticket.id}
              className="ticket-card"
              onClick={() => fetchTicketDetail(ticket.id)}
            >
              <div className="ticket-card-info">
                <FiMessageSquare className="ticket-icon" />
                <div>
                  <h3>{ticket.subject}</h3>
                  <div className="ticket-card-meta">
                    <span className="status-badge" style={{ background: getStatusColor(ticket.status) }}>
                      {ticket.status}
                    </span>
                    <span>{timeAgo(ticket.created_at)}</span>
                  </div>
                </div>
              </div>
              <FiChevronRight className="ticket-arrow" />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
