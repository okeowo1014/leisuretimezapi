import { useState, useRef, useEffect } from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { getImageUrl } from '../../utils/helpers';
import {
  FiMenu, FiX, FiUser, FiLogOut, FiSettings, FiBell,
  FiHeart, FiCalendar, FiCreditCard, FiHelpCircle, FiChevronDown
} from 'react-icons/fi';
import './Navbar.css';

export default function Navbar() {
  const { user, isAuthenticated, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const navigate = useNavigate();
  const dropdownRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(e) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = async () => {
    await logout();
    setDropdownOpen(false);
    navigate('/');
  };

  const navLinks = [
    { to: '/', label: 'Home' },
    { to: '/packages', label: 'Packages' },
    { to: '/blog', label: 'Blog' },
    { to: '/contact', label: 'Contact' },
  ];

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <Link to="/" className="navbar-brand">
          <span className="brand-icon">L</span>
          <span className="brand-text">LeisureTimez</span>
        </Link>

        <div className={`navbar-links ${menuOpen ? 'active' : ''}`}>
          {navLinks.map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
              onClick={() => setMenuOpen(false)}
              end={to === '/'}
            >
              {label}
            </NavLink>
          ))}
        </div>

        <div className="navbar-actions">
          {isAuthenticated ? (
            <div className="user-menu" ref={dropdownRef}>
              <button
                className="user-menu-trigger"
                onClick={() => setDropdownOpen(!dropdownOpen)}
              >
                <div className="user-avatar">
                  {user?.image ? (
                    <img src={getImageUrl(user.image)} alt="" />
                  ) : (
                    <FiUser />
                  )}
                </div>
                <span className="user-name">{user?.firstname || 'Account'}</span>
                <FiChevronDown className={`chevron ${dropdownOpen ? 'rotated' : ''}`} />
              </button>

              {dropdownOpen && (
                <div className="dropdown-menu">
                  <div className="dropdown-header">
                    <p className="dropdown-user-name">
                      {user?.firstname} {user?.lastname}
                    </p>
                    <p className="dropdown-user-email">{user?.email}</p>
                  </div>
                  <div className="dropdown-divider" />
                  <Link to="/dashboard" className="dropdown-item" onClick={() => setDropdownOpen(false)}>
                    <FiUser /> My Profile
                  </Link>
                  <Link to="/dashboard/bookings" className="dropdown-item" onClick={() => setDropdownOpen(false)}>
                    <FiCalendar /> My Bookings
                  </Link>
                  <Link to="/dashboard/wallet" className="dropdown-item" onClick={() => setDropdownOpen(false)}>
                    <FiCreditCard /> Wallet
                  </Link>
                  <Link to="/dashboard/saved" className="dropdown-item" onClick={() => setDropdownOpen(false)}>
                    <FiHeart /> Saved Packages
                  </Link>
                  <Link to="/dashboard/notifications" className="dropdown-item" onClick={() => setDropdownOpen(false)}>
                    <FiBell /> Notifications
                  </Link>
                  <Link to="/dashboard/support" className="dropdown-item" onClick={() => setDropdownOpen(false)}>
                    <FiHelpCircle /> Support
                  </Link>
                  <Link to="/dashboard/settings" className="dropdown-item" onClick={() => setDropdownOpen(false)}>
                    <FiSettings /> Settings
                  </Link>
                  <div className="dropdown-divider" />
                  <button className="dropdown-item logout" onClick={handleLogout}>
                    <FiLogOut /> Sign Out
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="auth-buttons">
              <Link to="/login" className="btn-login">Sign In</Link>
              <Link to="/register" className="btn-register">Get Started</Link>
            </div>
          )}

          <button
            className="menu-toggle"
            onClick={() => setMenuOpen(!menuOpen)}
            aria-label="Toggle menu"
          >
            {menuOpen ? <FiX /> : <FiMenu />}
          </button>
        </div>
      </div>
    </nav>
  );
}
