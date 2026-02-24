import { useState } from 'react';
import { Link } from 'react-router-dom';
import { auth } from '../api/endpoints';
import { sanitizeInput } from '../utils/helpers';
import { FiMail, FiArrowLeft } from 'react-icons/fi';
import toast from 'react-hot-toast';
import './ForgotPasswordPage.css';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();

    const sanitizedEmail = sanitizeInput(email.trim());

    if (!sanitizedEmail) {
      toast.error('Please enter your email address');
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(sanitizedEmail)) {
      toast.error('Please enter a valid email address');
      return;
    }

    setLoading(true);
    try {
      await auth.resetPassword({ email: sanitizedEmail });
      setSubmitted(true);
      toast.success('Reset link sent! Check your inbox.');
    } catch (err) {
      const msg =
        err.response?.data?.error ||
        err.response?.data?.detail ||
        'Failed to send reset link. Please try again.';
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="forgot-page">
      <div className="forgot-card">
        <Link to="/login" className="forgot-back-link">
          <FiArrowLeft />
          <span>Back to Sign In</span>
        </Link>

        {!submitted ? (
          <>
            <div className="forgot-header">
              <div className="forgot-icon-circle">
                <FiMail className="forgot-icon" />
              </div>
              <h2 className="forgot-title">Forgot Password?</h2>
              <p className="forgot-subtitle">
                No worries! Enter the email address associated with your account
                and we&apos;ll send you a link to reset your password.
              </p>
            </div>

            <form onSubmit={handleSubmit} className="forgot-form" noValidate>
              <div className="forgot-input-group">
                <label htmlFor="forgot-email" className="forgot-label">
                  Email Address
                </label>
                <div className="forgot-input-wrapper">
                  <FiMail className="forgot-input-icon" />
                  <input
                    id="forgot-email"
                    type="email"
                    placeholder="Enter your email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="forgot-input"
                    autoComplete="email"
                    required
                  />
                </div>
              </div>

              <button
                type="submit"
                className="forgot-submit-btn"
                disabled={loading}
              >
                {loading ? (
                  <span className="forgot-btn-loading">
                    <span className="forgot-spinner" />
                    Sending...
                  </span>
                ) : (
                  'Send Reset Link'
                )}
              </button>
            </form>
          </>
        ) : (
          <div className="forgot-success">
            <div className="forgot-success-icon-circle">
              <svg
                className="forgot-success-check"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <polyline points="20 6 9 17 4 12" />
              </svg>
            </div>
            <h2 className="forgot-title">Check Your Email</h2>
            <p className="forgot-subtitle">
              We&apos;ve sent a password reset link to{' '}
              <strong>{email}</strong>. Please check your inbox and follow the
              instructions to reset your password.
            </p>
            <p className="forgot-hint">
              Didn&apos;t receive the email? Check your spam folder or{' '}
              <button
                type="button"
                className="forgot-resend-btn"
                onClick={() => setSubmitted(false)}
              >
                try again
              </button>
              .
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
