import { useState, useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { sanitizeInput } from '../utils/helpers';
import { FiMail, FiLock, FiUser, FiEye, FiEyeOff } from 'react-icons/fi';
import toast from 'react-hot-toast';
import './RegisterPage.css';

function getPasswordStrength(password) {
  if (!password) return { score: 0, label: '', color: '' };

  let score = 0;
  if (password.length >= 8) score += 1;
  if (password.length >= 12) score += 1;
  if (/[a-z]/.test(password) && /[A-Z]/.test(password)) score += 1;
  if (/\d/.test(password)) score += 1;
  if (/[^a-zA-Z0-9]/.test(password)) score += 1;

  if (score <= 1) return { score: 1, label: 'Weak', color: '#ef4444' };
  if (score === 2) return { score: 2, label: 'Fair', color: '#f59e0b' };
  if (score === 3) return { score: 3, label: 'Good', color: '#3b82f6' };
  if (score >= 4) return { score: 4, label: 'Strong', color: '#10b981' };

  return { score: 0, label: '', color: '' };
}

export default function RegisterPage() {
  const navigate = useNavigate();
  const { register, loading } = useAuth();

  const [formData, setFormData] = useState({
    firstname: '',
    lastname: '',
    email: '',
    password: '',
    confirm_password: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const passwordStrength = useMemo(
    () => getPasswordStrength(formData.password),
    [formData.password]
  );

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const validate = () => {
    const { firstname, lastname, email, password, confirm_password } = formData;

    if (!firstname.trim() || !lastname.trim() || !email.trim() || !password || !confirm_password) {
      toast.error('Please fill in all fields');
      return false;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email.trim())) {
      toast.error('Please enter a valid email address');
      return false;
    }

    if (password.length < 8) {
      toast.error('Password must be at least 8 characters');
      return false;
    }

    if (password !== confirm_password) {
      toast.error('Passwords do not match');
      return false;
    }

    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validate()) return;

    const sanitized = {
      firstname: sanitizeInput(formData.firstname.trim()),
      lastname: sanitizeInput(formData.lastname.trim()),
      email: sanitizeInput(formData.email.trim()),
      password: sanitizeInput(formData.password),
      confirm_password: sanitizeInput(formData.confirm_password),
    };

    try {
      await register(sanitized);
      navigate('/');
    } catch {
      // Error already handled by AuthContext
    }
  };

  return (
    <div className="register-page">
      {/* Left decorative panel */}
      <div className="register-panel-left">
        <div className="register-panel-overlay" />
        <div className="register-panel-content">
          <div className="register-panel-logo">
            <span className="register-logo-icon">&#9992;</span>
            <span className="register-logo-text">LeisureTimez</span>
          </div>
          <h1 className="register-panel-heading">
            Start Your Journey<br />With Us Today
          </h1>
          <p className="register-panel-subtext">
            Join thousands of travelers who trust LeisureTimez for their
            adventures. Create an account to unlock exclusive deals and
            personalized recommendations.
          </p>
          <div className="register-panel-features">
            <div className="register-feature-item">
              <span className="register-feature-dot" />
              <span>Exclusive Member Discounts</span>
            </div>
            <div className="register-feature-item">
              <span className="register-feature-dot" />
              <span>Personalized Recommendations</span>
            </div>
            <div className="register-feature-item">
              <span className="register-feature-dot" />
              <span>Instant Booking Confirmation</span>
            </div>
          </div>
        </div>
      </div>

      {/* Right form panel */}
      <div className="register-panel-right">
        <div className="register-form-container">
          <div className="register-form-header">
            <h2 className="register-form-title">Create Account</h2>
            <p className="register-form-subtitle">
              Fill in your details to get started
            </p>
          </div>

          <form onSubmit={handleSubmit} className="register-form" noValidate>
            <div className="register-name-row">
              <div className="register-input-group">
                <label htmlFor="firstname" className="register-label">
                  First Name
                </label>
                <div className="register-input-wrapper">
                  <FiUser className="register-input-icon" />
                  <input
                    id="firstname"
                    name="firstname"
                    type="text"
                    placeholder="First name"
                    value={formData.firstname}
                    onChange={handleChange}
                    className="register-input"
                    autoComplete="given-name"
                    required
                  />
                </div>
              </div>

              <div className="register-input-group">
                <label htmlFor="lastname" className="register-label">
                  Last Name
                </label>
                <div className="register-input-wrapper">
                  <FiUser className="register-input-icon" />
                  <input
                    id="lastname"
                    name="lastname"
                    type="text"
                    placeholder="Last name"
                    value={formData.lastname}
                    onChange={handleChange}
                    className="register-input"
                    autoComplete="family-name"
                    required
                  />
                </div>
              </div>
            </div>

            <div className="register-input-group">
              <label htmlFor="reg-email" className="register-label">
                Email Address
              </label>
              <div className="register-input-wrapper">
                <FiMail className="register-input-icon" />
                <input
                  id="reg-email"
                  name="email"
                  type="email"
                  placeholder="Enter your email"
                  value={formData.email}
                  onChange={handleChange}
                  className="register-input"
                  autoComplete="email"
                  required
                />
              </div>
            </div>

            <div className="register-input-group">
              <label htmlFor="reg-password" className="register-label">
                Password
              </label>
              <div className="register-input-wrapper">
                <FiLock className="register-input-icon" />
                <input
                  id="reg-password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Create a password"
                  value={formData.password}
                  onChange={handleChange}
                  className="register-input"
                  autoComplete="new-password"
                  required
                />
                <button
                  type="button"
                  className="register-toggle-password"
                  onClick={() => setShowPassword((prev) => !prev)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <FiEyeOff /> : <FiEye />}
                </button>
              </div>

              {/* Password strength indicator */}
              {formData.password && (
                <div className="register-password-strength">
                  <div className="register-strength-bars">
                    {[1, 2, 3, 4].map((level) => (
                      <div
                        key={level}
                        className={`register-strength-bar ${
                          passwordStrength.score >= level ? 'active' : ''
                        }`}
                        style={{
                          backgroundColor:
                            passwordStrength.score >= level
                              ? passwordStrength.color
                              : '#e5e7eb',
                        }}
                      />
                    ))}
                  </div>
                  <span
                    className="register-strength-label"
                    style={{ color: passwordStrength.color }}
                  >
                    {passwordStrength.label}
                  </span>
                </div>
              )}
            </div>

            <div className="register-input-group">
              <label htmlFor="confirm_password" className="register-label">
                Confirm Password
              </label>
              <div className="register-input-wrapper">
                <FiLock className="register-input-icon" />
                <input
                  id="confirm_password"
                  name="confirm_password"
                  type={showConfirmPassword ? 'text' : 'password'}
                  placeholder="Confirm your password"
                  value={formData.confirm_password}
                  onChange={handleChange}
                  className="register-input"
                  autoComplete="new-password"
                  required
                />
                <button
                  type="button"
                  className="register-toggle-password"
                  onClick={() => setShowConfirmPassword((prev) => !prev)}
                  aria-label={
                    showConfirmPassword ? 'Hide password' : 'Show password'
                  }
                >
                  {showConfirmPassword ? <FiEyeOff /> : <FiEye />}
                </button>
              </div>
              {formData.confirm_password &&
                formData.password !== formData.confirm_password && (
                  <span className="register-mismatch-text">
                    Passwords do not match
                  </span>
                )}
            </div>

            <button
              type="submit"
              className="register-submit-btn"
              disabled={loading}
            >
              {loading ? (
                <span className="register-btn-loading">
                  <span className="register-spinner" />
                  Creating Account...
                </span>
              ) : (
                'Create Account'
              )}
            </button>
          </form>

          <p className="register-footer-text">
            Already have an account?{' '}
            <Link to="/login" className="register-login-link">
              Sign In
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
