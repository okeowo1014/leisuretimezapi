import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { packages as packagesApi, bookings } from '../api/endpoints';
import { formatCurrency, getImageUrl, sanitizeInput } from '../utils/helpers';
import toast from 'react-hot-toast';
import { FiCalendar, FiUsers, FiMapPin, FiCreditCard, FiArrowLeft, FiCheck } from 'react-icons/fi';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import './BookingPage.css';

export default function BookingPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();
  const [pkg, setPkg] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [step, setStep] = useState(1);
  const [offer, setOffer] = useState(null);

  const [form, setForm] = useState({
    firstname: '',
    lastname: '',
    email: '',
    phone: '',
    adult: 1,
    children: 0,
    datefrom: '',
    dateto: '',
    travelcountry: '',
    travelstate: '',
    destinations: '',
    purpose: 'tourism',
    service: '',
    payment_method: 'stripe',
  });

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login', { state: { from: `/book/${id}` } });
      return;
    }
    fetchPackage();
  }, [id, isAuthenticated]);

  useEffect(() => {
    if (user) {
      setForm((f) => ({
        ...f,
        firstname: user.firstname || '',
        lastname: user.lastname || '',
        email: user.email || '',
      }));
    }
  }, [user]);

  const fetchPackage = async () => {
    try {
      const { data } = await packagesApi.get(id);
      setPkg(data);
    } catch {
      toast.error('Package not found');
      navigate('/packages');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((f) => ({ ...f, [name]: value }));
  };

  const checkOffer = async () => {
    try {
      const { data } = await packagesApi.checkOffer(id, {
        adult: form.adult,
        children: form.children,
      });
      setOffer(data);
    } catch {
      // no special offer
    }
  };

  const handleNext = () => {
    if (step === 1) {
      if (!form.firstname || !form.lastname || !form.email || !form.phone) {
        toast.error('Please fill in all personal details');
        return;
      }
    }
    if (step === 2) {
      if (!form.datefrom || !form.dateto) {
        toast.error('Please select travel dates');
        return;
      }
      if (new Date(form.datefrom) >= new Date(form.dateto)) {
        toast.error('End date must be after start date');
        return;
      }
      if (new Date(form.datefrom) < new Date()) {
        toast.error('Start date cannot be in the past');
        return;
      }
      checkOffer();
    }
    setStep((s) => Math.min(s + 1, 3));
  };

  const handleBack = () => setStep((s) => Math.max(s - 1, 1));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const payload = {
        ...form,
        firstname: sanitizeInput(form.firstname),
        lastname: sanitizeInput(form.lastname),
        email: sanitizeInput(form.email),
        phone: sanitizeInput(form.phone),
        destinations: sanitizeInput(form.destinations),
        travelcountry: sanitizeInput(form.travelcountry),
        travelstate: sanitizeInput(form.travelstate),
      };
      const { data } = await bookings.create(id, payload);
      toast.success('Booking created successfully!');
      navigate(`/dashboard/bookings`);
    } catch (err) {
      const msg = err.response?.data?.error || err.response?.data?.detail || 'Booking failed';
      toast.error(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <LoadingSpinner />;
  if (!pkg) return null;

  return (
    <div className="booking-page">
      <div className="booking-container">
        <Link to={`/packages/${id}`} className="back-link">
          <FiArrowLeft /> Back to package
        </Link>

        <div className="booking-grid">
          <div className="booking-form-section">
            <h1 className="booking-title">Book Your Trip</h1>
            <p className="booking-subtitle">Complete the form below to reserve your spot</p>

            <div className="step-indicator">
              {[1, 2, 3].map((s) => (
                <div key={s} className={`step ${step >= s ? 'active' : ''} ${step > s ? 'completed' : ''}`}>
                  <div className="step-circle">
                    {step > s ? <FiCheck /> : s}
                  </div>
                  <span className="step-label">
                    {s === 1 ? 'Details' : s === 2 ? 'Travel Info' : 'Payment'}
                  </span>
                </div>
              ))}
            </div>

            <form onSubmit={handleSubmit}>
              {step === 1 && (
                <div className="form-step">
                  <h3>Personal Information</h3>
                  <div className="form-row">
                    <div className="form-group">
                      <label>First Name</label>
                      <input type="text" name="firstname" value={form.firstname} onChange={handleChange} required />
                    </div>
                    <div className="form-group">
                      <label>Last Name</label>
                      <input type="text" name="lastname" value={form.lastname} onChange={handleChange} required />
                    </div>
                  </div>
                  <div className="form-row">
                    <div className="form-group">
                      <label>Email</label>
                      <input type="email" name="email" value={form.email} onChange={handleChange} required />
                    </div>
                    <div className="form-group">
                      <label>Phone</label>
                      <input type="tel" name="phone" value={form.phone} onChange={handleChange} required />
                    </div>
                  </div>
                  <div className="form-row">
                    <div className="form-group">
                      <label><FiUsers style={{ marginRight: 4 }} /> Adults</label>
                      <input type="number" name="adult" min="1" max="20" value={form.adult} onChange={handleChange} />
                    </div>
                    <div className="form-group">
                      <label><FiUsers style={{ marginRight: 4 }} /> Children</label>
                      <input type="number" name="children" min="0" max="20" value={form.children} onChange={handleChange} />
                    </div>
                  </div>
                </div>
              )}

              {step === 2 && (
                <div className="form-step">
                  <h3>Travel Information</h3>
                  <div className="form-row">
                    <div className="form-group">
                      <label><FiCalendar style={{ marginRight: 4 }} /> Start Date</label>
                      <input type="date" name="datefrom" value={form.datefrom} onChange={handleChange} required />
                    </div>
                    <div className="form-group">
                      <label><FiCalendar style={{ marginRight: 4 }} /> End Date</label>
                      <input type="date" name="dateto" value={form.dateto} onChange={handleChange} required />
                    </div>
                  </div>
                  <div className="form-row">
                    <div className="form-group">
                      <label><FiMapPin style={{ marginRight: 4 }} /> Country</label>
                      <input type="text" name="travelcountry" value={form.travelcountry} onChange={handleChange} placeholder="e.g. France" />
                    </div>
                    <div className="form-group">
                      <label><FiMapPin style={{ marginRight: 4 }} /> State/City</label>
                      <input type="text" name="travelstate" value={form.travelstate} onChange={handleChange} placeholder="e.g. Paris" />
                    </div>
                  </div>
                  <div className="form-group">
                    <label>Destinations</label>
                    <input type="text" name="destinations" value={form.destinations} onChange={handleChange} placeholder="e.g. Eiffel Tower, Louvre" />
                  </div>
                  <div className="form-row">
                    <div className="form-group">
                      <label>Purpose</label>
                      <select name="purpose" value={form.purpose} onChange={handleChange}>
                        <option value="tourism">Tourism</option>
                        <option value="business">Business</option>
                        <option value="honeymoon">Honeymoon</option>
                        <option value="adventure">Adventure</option>
                        <option value="relaxation">Relaxation</option>
                        <option value="other">Other</option>
                      </select>
                    </div>
                    <div className="form-group">
                      <label>Services Needed</label>
                      <input type="text" name="service" value={form.service} onChange={handleChange} placeholder="e.g. accommodation, meals" />
                    </div>
                  </div>
                </div>
              )}

              {step === 3 && (
                <div className="form-step">
                  <h3>Payment Method</h3>
                  <div className="payment-options">
                    {['stripe', 'wallet', 'split'].map((method) => (
                      <label
                        key={method}
                        className={`payment-option ${form.payment_method === method ? 'selected' : ''}`}
                      >
                        <input
                          type="radio"
                          name="payment_method"
                          value={method}
                          checked={form.payment_method === method}
                          onChange={handleChange}
                        />
                        <FiCreditCard />
                        <div>
                          <strong>
                            {method === 'stripe' ? 'Card Payment' : method === 'wallet' ? 'Wallet' : 'Split Payment'}
                          </strong>
                          <p>
                            {method === 'stripe'
                              ? 'Pay securely with your card via Stripe'
                              : method === 'wallet'
                              ? 'Pay from your wallet balance'
                              : 'Partially from wallet, rest by card'}
                          </p>
                        </div>
                      </label>
                    ))}
                  </div>

                  {offer && (
                    <div className="offer-banner">
                      <strong>Special Offer Applied!</strong>
                      <p>Price: {formatCurrency(offer.total_price || offer.price)}</p>
                    </div>
                  )}
                </div>
              )}

              <div className="form-actions">
                {step > 1 && (
                  <button type="button" className="btn-secondary" onClick={handleBack}>
                    Back
                  </button>
                )}
                {step < 3 ? (
                  <button type="button" className="btn-primary" onClick={handleNext}>
                    Continue
                  </button>
                ) : (
                  <button type="submit" className="btn-primary" disabled={submitting}>
                    {submitting ? 'Processing...' : 'Confirm Booking'}
                  </button>
                )}
              </div>
            </form>
          </div>

          <div className="booking-summary">
            <div className="summary-card">
              <div className="summary-image">
                <img src={getImageUrl(pkg.main_image)} alt={pkg.name} />
              </div>
              <div className="summary-info">
                <span className="summary-category">{pkg.category}</span>
                <h3>{pkg.name}</h3>
                <div className="summary-details">
                  <span><FiMapPin /> {pkg.destination || 'Various'}</span>
                  <span><FiCalendar /> {pkg.duration}</span>
                  <span><FiUsers /> {Number(form.adult) + Number(form.children)} guests</span>
                </div>
                <div className="summary-price">
                  <span className="price-label">Total Price</span>
                  <span className="price-value">
                    {formatCurrency(offer?.total_price || pkg.discount_price || pkg.price)}
                  </span>
                  {pkg.discount_price && pkg.price !== pkg.discount_price && (
                    <span className="price-original">{formatCurrency(pkg.price)}</span>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
