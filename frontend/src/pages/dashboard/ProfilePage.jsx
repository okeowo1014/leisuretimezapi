import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../../context/AuthContext';
import { profile } from '../../api/endpoints';
import { sanitizeInput, getImageUrl } from '../../utils/helpers';
import LoadingSpinner from '../../components/ui/LoadingSpinner';
import toast from 'react-hot-toast';
import {
  FiUser, FiMail, FiPhone, FiMapPin, FiCalendar,
  FiCamera, FiSave, FiEdit2, FiX, FiBriefcase
} from 'react-icons/fi';
import './ProfilePage.css';

export default function ProfilePage() {
  const { user, refreshProfile } = useAuth();
  const fileInputRef = useRef(null);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [editing, setEditing] = useState(false);
  const [imagePreview, setImagePreview] = useState(null);

  const [formData, setFormData] = useState({
    firstname: '',
    lastname: '',
    phone: '',
    address: '',
    city: '',
    state: '',
    country: '',
    date_of_birth: '',
    gender: '',
    marital_status: '',
    profession: '',
  });

  const [profileData, setProfileData] = useState(null);

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    setLoading(true);
    try {
      const { data } = await profile.get();
      setProfileData(data);
      setFormData({
        firstname: data.firstname || data.user?.firstname || '',
        lastname: data.lastname || data.user?.lastname || '',
        phone: data.phone || '',
        address: data.address || '',
        city: data.city || '',
        state: data.state || '',
        country: data.country || '',
        date_of_birth: data.date_of_birth || '',
        gender: data.gender || '',
        marital_status: data.marital_status || '',
        profession: data.profession || '',
      });
    } catch (err) {
      toast.error('Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: sanitizeInput(value) }));
  };

  const validate = () => {
    if (!formData.firstname.trim()) {
      toast.error('First name is required');
      return false;
    }
    if (!formData.lastname.trim()) {
      toast.error('Last name is required');
      return false;
    }
    if (formData.phone && !/^[+\d\s()-]{7,20}$/.test(formData.phone)) {
      toast.error('Please enter a valid phone number');
      return false;
    }
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    setSaving(true);
    try {
      const sanitized = {};
      Object.entries(formData).forEach(([key, val]) => {
        sanitized[key] = typeof val === 'string' ? sanitizeInput(val.trim()) : val;
      });

      await profile.update(sanitized);
      await refreshProfile();
      toast.success('Profile updated successfully');
      setEditing(false);
      fetchProfile();
    } catch (err) {
      const msg = err.response?.data?.detail ||
        err.response?.data?.error ||
        (typeof err.response?.data === 'object'
          ? Object.values(err.response.data).flat().join(', ')
          : 'Failed to update profile');
      toast.error(msg);
    } finally {
      setSaving(false);
    }
  };

  const handleImageSelect = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      toast.error('Please select an image file');
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      toast.error('Image must be less than 5MB');
      return;
    }

    const reader = new FileReader();
    reader.onload = (ev) => setImagePreview(ev.target.result);
    reader.readAsDataURL(file);

    uploadImage(file);
  };

  const uploadImage = async (file) => {
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('image', file);
      await profile.uploadImage(formData);
      await refreshProfile();
      toast.success('Profile image updated');
    } catch (err) {
      toast.error('Failed to upload image');
      setImagePreview(null);
    } finally {
      setUploading(false);
    }
  };

  const cancelEdit = () => {
    setEditing(false);
    if (profileData) {
      setFormData({
        firstname: profileData.firstname || profileData.user?.firstname || '',
        lastname: profileData.lastname || profileData.user?.lastname || '',
        phone: profileData.phone || '',
        address: profileData.address || '',
        city: profileData.city || '',
        state: profileData.state || '',
        country: profileData.country || '',
        date_of_birth: profileData.date_of_birth || '',
        gender: profileData.gender || '',
        marital_status: profileData.marital_status || '',
        profession: profileData.profession || '',
      });
    }
  };

  const avatarSrc = imagePreview
    || getImageUrl(profileData?.image || user?.image);

  if (loading) return <LoadingSpinner message="Loading profile..." />;

  return (
    <div className="profile-page">
      {/* Profile Header */}
      <div className="profile-header-card">
        <div className="profile-avatar-section">
          <div className="profile-avatar-wrapper">
            <img
              src={avatarSrc}
              alt="Profile"
              className="profile-avatar"
              onError={(e) => { e.target.src = '/placeholder.svg'; }}
            />
            <button
              className="profile-avatar-upload-btn"
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              title="Change profile picture"
            >
              {uploading ? <span className="avatar-upload-spinner" /> : <FiCamera />}
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleImageSelect}
              hidden
            />
          </div>
        </div>

        <div className="profile-header-info">
          <h1 className="profile-header-name">
            {formData.firstname || 'User'} {formData.lastname}
          </h1>
          <p className="profile-header-email">
            <FiMail /> {user?.email || profileData?.email || profileData?.user?.email}
          </p>
          {formData.profession && (
            <p className="profile-header-profession">
              <FiBriefcase /> {formData.profession}
            </p>
          )}
        </div>

        <div className="profile-header-actions">
          {!editing ? (
            <button className="profile-edit-btn" onClick={() => setEditing(true)}>
              <FiEdit2 /> Edit Profile
            </button>
          ) : (
            <button className="profile-cancel-btn" onClick={cancelEdit}>
              <FiX /> Cancel
            </button>
          )}
        </div>
      </div>

      {/* Profile Form */}
      <form className="profile-form-card" onSubmit={handleSubmit}>
        <h2 className="profile-form-title">Personal Information</h2>

        <div className="profile-form-grid">
          <div className="profile-field">
            <label className="profile-label">
              <FiUser className="profile-label-icon" /> First Name
            </label>
            <input
              type="text"
              name="firstname"
              value={formData.firstname}
              onChange={handleChange}
              className="profile-input"
              disabled={!editing}
              placeholder="Enter first name"
            />
          </div>

          <div className="profile-field">
            <label className="profile-label">
              <FiUser className="profile-label-icon" /> Last Name
            </label>
            <input
              type="text"
              name="lastname"
              value={formData.lastname}
              onChange={handleChange}
              className="profile-input"
              disabled={!editing}
              placeholder="Enter last name"
            />
          </div>

          <div className="profile-field">
            <label className="profile-label">
              <FiPhone className="profile-label-icon" /> Phone
            </label>
            <input
              type="tel"
              name="phone"
              value={formData.phone}
              onChange={handleChange}
              className="profile-input"
              disabled={!editing}
              placeholder="Enter phone number"
            />
          </div>

          <div className="profile-field">
            <label className="profile-label">
              <FiCalendar className="profile-label-icon" /> Date of Birth
            </label>
            <input
              type="date"
              name="date_of_birth"
              value={formData.date_of_birth}
              onChange={handleChange}
              className="profile-input"
              disabled={!editing}
            />
          </div>

          <div className="profile-field">
            <label className="profile-label">Gender</label>
            <select
              name="gender"
              value={formData.gender}
              onChange={handleChange}
              className="profile-input"
              disabled={!editing}
            >
              <option value="">Select gender</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
              <option value="other">Other</option>
              <option value="prefer_not_to_say">Prefer not to say</option>
            </select>
          </div>

          <div className="profile-field">
            <label className="profile-label">Marital Status</label>
            <select
              name="marital_status"
              value={formData.marital_status}
              onChange={handleChange}
              className="profile-input"
              disabled={!editing}
            >
              <option value="">Select status</option>
              <option value="single">Single</option>
              <option value="married">Married</option>
              <option value="divorced">Divorced</option>
              <option value="widowed">Widowed</option>
            </select>
          </div>

          <div className="profile-field">
            <label className="profile-label">
              <FiBriefcase className="profile-label-icon" /> Profession
            </label>
            <input
              type="text"
              name="profession"
              value={formData.profession}
              onChange={handleChange}
              className="profile-input"
              disabled={!editing}
              placeholder="Enter profession"
            />
          </div>
        </div>

        <h2 className="profile-form-title profile-form-title-mt">Address</h2>

        <div className="profile-form-grid">
          <div className="profile-field profile-field-full">
            <label className="profile-label">
              <FiMapPin className="profile-label-icon" /> Address
            </label>
            <input
              type="text"
              name="address"
              value={formData.address}
              onChange={handleChange}
              className="profile-input"
              disabled={!editing}
              placeholder="Enter address"
            />
          </div>

          <div className="profile-field">
            <label className="profile-label">City</label>
            <input
              type="text"
              name="city"
              value={formData.city}
              onChange={handleChange}
              className="profile-input"
              disabled={!editing}
              placeholder="Enter city"
            />
          </div>

          <div className="profile-field">
            <label className="profile-label">State</label>
            <input
              type="text"
              name="state"
              value={formData.state}
              onChange={handleChange}
              className="profile-input"
              disabled={!editing}
              placeholder="Enter state"
            />
          </div>

          <div className="profile-field">
            <label className="profile-label">Country</label>
            <input
              type="text"
              name="country"
              value={formData.country}
              onChange={handleChange}
              className="profile-input"
              disabled={!editing}
              placeholder="Enter country"
            />
          </div>
        </div>

        {editing && (
          <div className="profile-form-actions">
            <button type="button" className="profile-cancel-form-btn" onClick={cancelEdit}>
              Cancel
            </button>
            <button type="submit" className="profile-save-btn" disabled={saving}>
              {saving ? (
                <span className="profile-btn-loading">
                  <span className="profile-btn-spinner" /> Saving...
                </span>
              ) : (
                <>
                  <FiSave /> Save Changes
                </>
              )}
            </button>
          </div>
        )}
      </form>
    </div>
  );
}
