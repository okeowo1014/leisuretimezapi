import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { sanitizeInput } from '../utils/helpers';
import { FiMail, FiLock, FiEye, FiEyeOff } from 'react-icons/fi';
import toast from 'react-hot-toast';
import './LoginPage.css';

export default function LoginPage() {
  const navigate = useNavigate();
  const { login, loading } = useAuth();

  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [showPassword, setShowPassword] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    const email = sanitizeInput(formData.email.trim());
    const password = sanitizeInput(formData.password);

    if (!email || !password) {
      toast.error('Please fill in all fields');
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      toast.error('Please enter a valid email address');
      return;
    }

    try {
      await login(email, password);
      navigate('/');
    } catch {
      // Error already handled by AuthContext
    }
  };

  return (
    <div className="login-page">
      {/* Left decorative panel */}
      <div className="login-panel-left">
        <div className="login-panel-overlay" />
        <div className="login-panel-content">
          <div className="login-panel-logo">
            <span className="login-logo-icon">&#9992;</span>
            <span className="login-logo-text">LeisureTimez</span>
          </div>
          <h1 className="login-panel-heading">
            Explore the World,<br />One Trip at a Time
          </h1>
          <p className="login-panel-subtext">
            Discover handpicked destinations, curated travel packages, and
            unforgettable experiences. Your next adventure is just a click away.
          </p>
          <div className="login-panel-features">
            <div className="login-feature-item">
              <span className="login-feature-dot" />
              <span>500+ Premium Destinations</span>
            </div>
            <div className="login-feature-item">
              <span className="login-feature-dot" />
              <span>24/7 Travel Support</span>
            </div>
            <div className="login-feature-item">
              <span className="login-feature-dot" />
              <span>Best Price Guarantee</span>
            </div>
          </div>
        </div>
      </div>

      {/* Right form panel */}
      <div className="login-panel-right">
        <div className="login-form-container">
          <div className="login-form-header">
            <h2 className="login-form-title">Welcome Back</h2>
            <p className="login-form-subtitle">
              Sign in to continue your journey
            </p>
          </div>

          <form onSubmit={handleSubmit} className="login-form" noValidate>
            <div className="login-input-group">
              <label htmlFor="email" className="login-label">
                Email Address
              </label>
              <div className="login-input-wrapper">
                <FiMail className="login-input-icon" />
                <input
                  id="email"
                  name="email"
                  type="email"
                  placeholder="Enter your email"
                  value={formData.email}
                  onChange={handleChange}
                  className="login-input"
                  autoComplete="email"
                  required
                />
              </div>
            </div>

            <div className="login-input-group">
              <label htmlFor="password" className="login-label">
                Password
              </label>
              <div className="login-input-wrapper">
                <FiLock className="login-input-icon" />
                <input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Enter your password"
                  value={formData.password}
                  onChange={handleChange}
                  className="login-input"
                  autoComplete="current-password"
                  required
                />
                <button
                  type="button"
                  className="login-toggle-password"
                  onClick={() => setShowPassword((prev) => !prev)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <FiEyeOff /> : <FiEye />}
                </button>
              </div>
            </div>

            <div className="login-options">
              <Link to="/forgot-password" className="login-forgot-link">
                Forgot password?
              </Link>
            </div>

            <button
              type="submit"
              className="login-submit-btn"
              disabled={loading}
            >
              {loading ? (
                <span className="login-btn-loading">
                  <span className="login-spinner" />
                  Signing in...
                </span>
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          <p className="login-footer-text">
            Don&apos;t have an account?{' '}
            <Link to="/register" className="login-signup-link">
              Sign Up
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
