import { useState, useEffect } from 'react';
import { bookings } from '../../api/endpoints';
import { formatCurrency, formatDate, getStatusColor } from '../../utils/helpers';
import LoadingSpinner from '../../components/ui/LoadingSpinner';
import EmptyState from '../../components/ui/EmptyState';
import toast from 'react-hot-toast';
import {
  FiCalendar, FiChevronDown, FiChevronUp, FiXCircle,
  FiPackage, FiHash, FiDollarSign, FiMapPin, FiUsers,
  FiClock, FiAlertTriangle
} from 'react-icons/fi';
import './BookingsPage.css';

export default function BookingsPage() {
  const [bookingList, setBookingList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState(null);
  const [cancellingId, setCancellingId] = useState(null);
  const [cancelReason, setCancelReason] = useState('');
  const [showCancelModal, setShowCancelModal] = useState(false);
  const [selectedBookingId, setSelectedBookingId] = useState(null);

  useEffect(() => {
    fetchBookings();
  }, []);

  const fetchBookings = async () => {
    setLoading(true);
    try {
      const { data } = await bookings.list();
      const list = Array.isArray(data) ? data : data.results || data.bookings || [];
      setBookingList(list);
    } catch (err) {
      toast.error('Failed to load bookings');
    } finally {
      setLoading(false);
    }
  };

  const toggleExpand = (id) => {
    setExpandedId((prev) => (prev === id ? null : id));
  };

  const openCancelModal = (id) => {
    setSelectedBookingId(id);
    setCancelReason('');
    setShowCancelModal(true);
  };

  const closeCancelModal = () => {
    setShowCancelModal(false);
    setSelectedBookingId(null);
    setCancelReason('');
  };

  const handleCancel = async () => {
    if (!cancelReason.trim()) {
      toast.error('Please provide a reason for cancellation');
      return;
    }

    setCancellingId(selectedBookingId);
    try {
      await bookings.cancel(selectedBookingId, { reason: cancelReason.trim() });
      toast.success('Booking cancelled successfully');
      closeCancelModal();
      fetchBookings();
    } catch (err) {
      const msg = err.response?.data?.detail ||
        err.response?.data?.error || 'Failed to cancel booking';
      toast.error(msg);
    } finally {
      setCancellingId(null);
    }
  };

  const getStatusLabel = (status) => {
    return status ? status.charAt(0).toUpperCase() + status.slice(1).toLowerCase() : 'Unknown';
  };

  if (loading) return <LoadingSpinner message="Loading bookings..." />;

  if (!bookingList.length) {
    return (
      <div className="bookings-page">
        <h1 className="bookings-page-title">My Bookings</h1>
        <EmptyState
          icon={FiCalendar}
          title="No bookings yet"
          description="Your travel bookings will appear here once you book a package."
          actionLabel="Browse Packages"
          actionLink="/packages"
        />
      </div>
    );
  }

  return (
    <div className="bookings-page">
      <div className="bookings-page-header">
        <h1 className="bookings-page-title">My Bookings</h1>
        <span className="bookings-count">{bookingList.length} booking{bookingList.length !== 1 ? 's' : ''}</span>
      </div>

      <div className="bookings-list">
        {bookingList.map((booking) => {
          const isExpanded = expandedId === booking.id;
          const status = booking.status?.toLowerCase();
          const canCancel = status === 'pending' || status === 'confirmed';

          return (
            <div key={booking.id} className={`booking-card ${isExpanded ? 'expanded' : ''}`}>
              <div className="booking-card-header" onClick={() => toggleExpand(booking.id)}>
                <div className="booking-card-main">
                  <div className="booking-card-id">
                    <FiHash className="booking-icon" />
                    <span>{booking.booking_id || `BK-${booking.id}`}</span>
                  </div>
                  <h3 className="booking-card-name">
                    <FiPackage className="booking-icon" />
                    {booking.package_name || booking.package?.name || 'Travel Package'}
                  </h3>
                </div>

                <div className="booking-card-meta-row">
                  <div className="booking-card-dates">
                    <FiCalendar className="booking-icon" />
                    <span>{formatDate(booking.start_date || booking.travel_date)}</span>
                    {booking.end_date && (
                      <span> - {formatDate(booking.end_date)}</span>
                    )}
                  </div>

                  <div className="booking-card-price">
                    <FiDollarSign className="booking-icon" />
                    {formatCurrency(booking.total_price || booking.total_amount || booking.amount)}
                  </div>

                  <span
                    className="booking-status-badge"
                    style={{
                      backgroundColor: `${getStatusColor(status)}18`,
                      color: getStatusColor(status),
                      borderColor: `${getStatusColor(status)}30`,
                    }}
                  >
                    {getStatusLabel(booking.status)}
                  </span>

                  <button className="booking-expand-btn" aria-label="Toggle details">
                    {isExpanded ? <FiChevronUp /> : <FiChevronDown />}
                  </button>
                </div>
              </div>

              {isExpanded && (
                <div className="booking-card-details">
                  <div className="booking-details-grid">
                    {booking.destination && (
                      <div className="booking-detail-item">
                        <FiMapPin className="booking-detail-icon" />
                        <div>
                          <span className="booking-detail-label">Destination</span>
                          <span className="booking-detail-value">{booking.destination}</span>
                        </div>
                      </div>
                    )}
                    {booking.guests && (
                      <div className="booking-detail-item">
                        <FiUsers className="booking-detail-icon" />
                        <div>
                          <span className="booking-detail-label">Guests</span>
                          <span className="booking-detail-value">
                            {booking.guests} {booking.guests === 1 ? 'guest' : 'guests'}
                          </span>
                        </div>
                      </div>
                    )}
                    {(booking.num_adults || booking.adults) && (
                      <div className="booking-detail-item">
                        <FiUsers className="booking-detail-icon" />
                        <div>
                          <span className="booking-detail-label">Adults</span>
                          <span className="booking-detail-value">{booking.num_adults || booking.adults}</span>
                        </div>
                      </div>
                    )}
                    {(booking.num_children || booking.children) && (
                      <div className="booking-detail-item">
                        <FiUsers className="booking-detail-icon" />
                        <div>
                          <span className="booking-detail-label">Children</span>
                          <span className="booking-detail-value">{booking.num_children || booking.children}</span>
                        </div>
                      </div>
                    )}
                    {booking.created_at && (
                      <div className="booking-detail-item">
                        <FiClock className="booking-detail-icon" />
                        <div>
                          <span className="booking-detail-label">Booked On</span>
                          <span className="booking-detail-value">{formatDate(booking.created_at)}</span>
                        </div>
                      </div>
                    )}
                    {booking.special_requests && (
                      <div className="booking-detail-item booking-detail-full">
                        <FiPackage className="booking-detail-icon" />
                        <div>
                          <span className="booking-detail-label">Special Requests</span>
                          <span className="booking-detail-value">{booking.special_requests}</span>
                        </div>
                      </div>
                    )}
                  </div>

                  {canCancel && (
                    <div className="booking-detail-actions">
                      <button
                        className="booking-cancel-btn"
                        onClick={(e) => {
                          e.stopPropagation();
                          openCancelModal(booking.id);
                        }}
                        disabled={cancellingId === booking.id}
                      >
                        <FiXCircle />
                        {cancellingId === booking.id ? 'Cancelling...' : 'Cancel Booking'}
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Cancel Confirmation Modal */}
      {showCancelModal && (
        <div className="booking-modal-overlay" onClick={closeCancelModal}>
          <div className="booking-modal" onClick={(e) => e.stopPropagation()}>
            <div className="booking-modal-icon">
              <FiAlertTriangle />
            </div>
            <h3 className="booking-modal-title">Cancel Booking</h3>
            <p className="booking-modal-text">
              Are you sure you want to cancel this booking? This action may not be reversible.
            </p>

            <div className="booking-modal-field">
              <label className="booking-modal-label">Reason for cancellation</label>
              <textarea
                className="booking-modal-textarea"
                value={cancelReason}
                onChange={(e) => setCancelReason(e.target.value)}
                placeholder="Please provide a reason for cancellation..."
                rows={3}
              />
            </div>

            <div className="booking-modal-actions">
              <button className="booking-modal-cancel-btn" onClick={closeCancelModal}>
                Keep Booking
              </button>
              <button
                className="booking-modal-confirm-btn"
                onClick={handleCancel}
                disabled={cancellingId}
              >
                {cancellingId ? 'Cancelling...' : 'Yes, Cancel'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
