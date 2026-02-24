import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { auth } from '../../api/endpoints';
import { sanitizeInput } from '../../utils/helpers';
import toast from 'react-hot-toast';
import {
  FiLock, FiEye, FiEyeOff, FiShield, FiAlertTriangle,
  FiTrash2, FiKey, FiSave
} from 'react-icons/fi';
import './SettingsPage.css';

export default function SettingsPage() {
  const navigate = useNavigate();
  const { logout } = useAuth();

  // --- Change Password ---
  const [passwords, setPasswords] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });
  const [showPasswords, setShowPasswords] = useState({
    current: false,
    new: false,
    confirm: false,
  });
  const [changingPassword, setChangingPassword] = useState(false);

  // --- Delete Account ---
  const [showDeleteSection, setShowDeleteSection] = useState(false);
  const [deletePassword, setDeletePassword] = useState('');
  const [showDeletePassword, setShowDeletePassword] = useState(false);
  const [deletingAccount, setDeletingAccount] = useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState('');

  const handlePasswordChange = (e) => {
    const { name, value } = e.target;
    setPasswords((prev) => ({ ...prev, [name]: value }));
  };

  const togglePasswordVisibility = (field) => {
    setShowPasswords((prev) => ({ ...prev, [field]: !prev[field] }));
  };

  const validatePassword = () => {
    const { current_password, new_password, confirm_password } = passwords;

    if (!current_password) {
      toast.error('Current password is required');
      return false;
    }
    if (!new_password) {
      toast.error('New password is required');
      return false;
    }
    if (new_password.length < 8) {
      toast.error('New password must be at least 8 characters');
      return false;
    }
    if (!/(?=.*[a-z])/.test(new_password)) {
      toast.error('Password must include a lowercase letter');
      return false;
    }
    if (!/(?=.*[A-Z])/.test(new_password)) {
      toast.error('Password must include an uppercase letter');
      return false;
    }
    if (!/(?=.*\d)/.test(new_password)) {
      toast.error('Password must include a number');
      return false;
    }
    if (new_password !== confirm_password) {
      toast.error('Passwords do not match');
      return false;
    }
    if (current_password === new_password) {
      toast.error('New password must differ from current password');
      return false;
    }
    return true;
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    if (!validatePassword()) return;

    setChangingPassword(true);
    try {
      await auth.changePassword({
        current_password: sanitizeInput(passwords.current_password),
        new_password: sanitizeInput(passwords.new_password),
        confirm_password: sanitizeInput(passwords.confirm_password),
      });
      toast.success('Password changed successfully. Please log in again.');
      setPasswords({ current_password: '', new_password: '', confirm_password: '' });
      setTimeout(async () => {
        await logout();
        navigate('/login');
      }, 1500);
    } catch (err) {
      const errData = err.response?.data;
      if (typeof errData === 'object' && errData !== null) {
        const msg = errData.detail || errData.error ||
          Object.values(errData).flat().join(', ');
        toast.error(msg);
      } else {
        toast.error('Failed to change password');
      }
    } finally {
      setChangingPassword(false);
    }
  };

  const handleDeleteAccount = async (e) => {
    e.preventDefault();

    if (deleteConfirmText !== 'DELETE') {
      toast.error('Please type DELETE to confirm');
      return;
    }
    if (!deletePassword) {
      toast.error('Password is required to delete account');
      return;
    }

    setDeletingAccount(true);
    try {
      await auth.deleteAccount({ password: sanitizeInput(deletePassword) });
      toast.success('Account deleted successfully');
      setTimeout(async () => {
        await logout();
        navigate('/');
      }, 1500);
    } catch (err) {
      const msg = err.response?.data?.detail ||
        err.response?.data?.error || 'Failed to delete account';
      toast.error(msg);
    } finally {
      setDeletingAccount(false);
    }
  };

  const getPasswordStrength = (password) => {
    if (!password) return { level: 0, label: '', color: '' };
    let score = 0;
    if (password.length >= 8) score++;
    if (password.length >= 12) score++;
    if (/[a-z]/.test(password) && /[A-Z]/.test(password)) score++;
    if (/\d/.test(password)) score++;
    if (/[^a-zA-Z0-9]/.test(password)) score++;

    if (score <= 1) return { level: 1, label: 'Weak', color: '#ef4444' };
    if (score <= 2) return { level: 2, label: 'Fair', color: '#f59e0b' };
    if (score <= 3) return { level: 3, label: 'Good', color: '#FA7436' };
    if (score <= 4) return { level: 4, label: 'Strong', color: '#10b981' };
    return { level: 5, label: 'Very Strong', color: '#059669' };
  };

  const passwordStrength = getPasswordStrength(passwords.new_password);

  return (
    <div className="settings-page">
      {/* Change Password Section */}
      <div className="settings-card">
        <div className="settings-card-header">
          <div className="settings-card-icon-wrapper">
            <FiKey className="settings-card-icon" />
          </div>
          <div>
            <h2 className="settings-card-title">Change Password</h2>
            <p className="settings-card-description">
              Update your password to keep your account secure.
            </p>
          </div>
        </div>

        <form className="settings-form" onSubmit={handleChangePassword}>
          <div className="settings-field">
            <label className="settings-label">Current Password</label>
            <div className="settings-input-wrapper">
              <FiLock className="settings-input-icon" />
              <input
                type={showPasswords.current ? 'text' : 'password'}
                name="current_password"
                value={passwords.current_password}
                onChange={handlePasswordChange}
                className="settings-input"
                placeholder="Enter current password"
                autoComplete="current-password"
              />
              <button
                type="button"
                className="settings-toggle-password"
                onClick={() => togglePasswordVisibility('current')}
                aria-label="Toggle password visibility"
              >
                {showPasswords.current ? <FiEyeOff /> : <FiEye />}
              </button>
            </div>
          </div>

          <div className="settings-field">
            <label className="settings-label">New Password</label>
            <div className="settings-input-wrapper">
              <FiLock className="settings-input-icon" />
              <input
                type={showPasswords.new ? 'text' : 'password'}
                name="new_password"
                value={passwords.new_password}
                onChange={handlePasswordChange}
                className="settings-input"
                placeholder="Enter new password"
                autoComplete="new-password"
              />
              <button
                type="button"
                className="settings-toggle-password"
                onClick={() => togglePasswordVisibility('new')}
                aria-label="Toggle password visibility"
              >
                {showPasswords.new ? <FiEyeOff /> : <FiEye />}
              </button>
            </div>
            {passwords.new_password && (
              <div className="settings-password-strength">
                <div className="settings-strength-bar">
                  {[1, 2, 3, 4, 5].map((level) => (
                    <div
                      key={level}
                      className="settings-strength-segment"
                      style={{
                        backgroundColor:
                          level <= passwordStrength.level
                            ? passwordStrength.color
                            : '#e2e8f0',
                      }}
                    />
                  ))}
                </div>
                <span
                  className="settings-strength-label"
                  style={{ color: passwordStrength.color }}
                >
                  {passwordStrength.label}
                </span>
              </div>
            )}
          </div>

          <div className="settings-field">
            <label className="settings-label">Confirm New Password</label>
            <div className="settings-input-wrapper">
              <FiLock className="settings-input-icon" />
              <input
                type={showPasswords.confirm ? 'text' : 'password'}
                name="confirm_password"
                value={passwords.confirm_password}
                onChange={handlePasswordChange}
                className="settings-input"
                placeholder="Confirm new password"
                autoComplete="new-password"
              />
              <button
                type="button"
                className="settings-toggle-password"
                onClick={() => togglePasswordVisibility('confirm')}
                aria-label="Toggle password visibility"
              >
                {showPasswords.confirm ? <FiEyeOff /> : <FiEye />}
              </button>
            </div>
            {passwords.confirm_password && passwords.new_password !== passwords.confirm_password && (
              <span className="settings-field-error">Passwords do not match</span>
            )}
          </div>

          <div className="settings-form-actions">
            <button
              type="submit"
              className="settings-submit-btn"
              disabled={changingPassword}
            >
              {changingPassword ? (
                <span className="settings-btn-loading">
                  <span className="settings-btn-spinner" /> Updating...
                </span>
              ) : (
                <>
                  <FiSave /> Update Password
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Delete Account Section */}
      <div className="settings-card settings-card-danger">
        <div className="settings-card-header">
          <div className="settings-card-icon-wrapper settings-icon-danger">
            <FiShield className="settings-card-icon" />
          </div>
          <div>
            <h2 className="settings-card-title settings-title-danger">Danger Zone</h2>
            <p className="settings-card-description">
              Permanently delete your account and all associated data. This action cannot be undone.
            </p>
          </div>
        </div>

        {!showDeleteSection ? (
          <button
            className="settings-delete-toggle-btn"
            onClick={() => setShowDeleteSection(true)}
          >
            <FiTrash2 /> Delete My Account
          </button>
        ) : (
          <form className="settings-delete-form" onSubmit={handleDeleteAccount}>
            <div className="settings-danger-warning">
              <FiAlertTriangle className="settings-danger-warning-icon" />
              <div>
                <strong>Warning:</strong> This will permanently delete your account including
                all bookings, wallet balance, saved packages, and personal data. This action
                is irreversible.
              </div>
            </div>

            <div className="settings-field">
              <label className="settings-label">
                Type <strong>DELETE</strong> to confirm
              </label>
              <input
                type="text"
                value={deleteConfirmText}
                onChange={(e) => setDeleteConfirmText(e.target.value)}
                className="settings-input settings-input-danger"
                placeholder="Type DELETE"
              />
            </div>

            <div className="settings-field">
              <label className="settings-label">Confirm your password</label>
              <div className="settings-input-wrapper">
                <FiLock className="settings-input-icon" />
                <input
                  type={showDeletePassword ? 'text' : 'password'}
                  value={deletePassword}
                  onChange={(e) => setDeletePassword(e.target.value)}
                  className="settings-input settings-input-danger"
                  placeholder="Enter your password"
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  className="settings-toggle-password"
                  onClick={() => setShowDeletePassword((p) => !p)}
                  aria-label="Toggle password visibility"
                >
                  {showDeletePassword ? <FiEyeOff /> : <FiEye />}
                </button>
              </div>
            </div>

            <div className="settings-delete-actions">
              <button
                type="button"
                className="settings-delete-cancel-btn"
                onClick={() => {
                  setShowDeleteSection(false);
                  setDeletePassword('');
                  setDeleteConfirmText('');
                }}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="settings-delete-confirm-btn"
                disabled={deletingAccount || deleteConfirmText !== 'DELETE'}
              >
                {deletingAccount ? (
                  <span className="settings-btn-loading">
                    <span className="settings-btn-spinner settings-spinner-danger" /> Deleting...
                  </span>
                ) : (
                  <>
                    <FiTrash2 /> Permanently Delete Account
                  </>
                )}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
