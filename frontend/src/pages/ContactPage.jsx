import { useState } from 'react';
import { contact } from '../api/endpoints';
import { sanitizeInput } from '../utils/helpers';
import toast from 'react-hot-toast';
import { FiMail, FiPhone, FiMapPin, FiSend } from 'react-icons/fi';
import './ContactPage.css';

export default function ContactPage() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    subject: '',
    message: '',
  });
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [errors, setErrors] = useState({});

  const validate = () => {
    const newErrors = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required.';
    }

    if (!formData.email.trim()) {
      newErrors.email = 'Email is required.';
    } else {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(formData.email.trim())) {
        newErrors.email = 'Please enter a valid email address.';
      }
    }

    if (!formData.subject.trim()) {
      newErrors.subject = 'Subject is required.';
    }

    if (!formData.message.trim()) {
      newErrors.message = 'Message is required.';
    } else if (formData.message.trim().length < 10) {
      newErrors.message = 'Message must be at least 10 characters.';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: '' }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validate()) return;

    setSubmitting(true);
    try {
      const sanitizedData = {
        name: sanitizeInput(formData.name.trim()),
        email: sanitizeInput(formData.email.trim()),
        subject: sanitizeInput(formData.subject.trim()),
        message: sanitizeInput(formData.message.trim()),
      };

      await contact.submit(sanitizedData);
      setSubmitted(true);
      setFormData({ name: '', email: '', subject: '', message: '' });
      toast.success('Message sent successfully!');
    } catch (err) {
      const msg =
        err.response?.data?.detail ||
        err.response?.data?.error ||
        'Failed to send message. Please try again.';
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="contact-page">
      {/* Page Header */}
      <section className="contact-page-header">
        <div className="contact-page-header-overlay" />
        <div className="contact-page-header-content">
          <h1 className="contact-page-title">Get in Touch</h1>
          <p className="contact-page-subtitle">
            Have a question or need help planning your trip? We would love to hear from you.
          </p>
        </div>
      </section>

      {/* Contact Content */}
      <section className="contact-page-content">
        <div className="contact-page-container">
          {/* Contact Form */}
          <div className="contact-form-section">
            {submitted ? (
              <div className="contact-success">
                <div className="contact-success-icon">
                  <FiSend />
                </div>
                <h2 className="contact-success-title">Message Sent!</h2>
                <p className="contact-success-text">
                  Thank you for reaching out. We will get back to you as soon as
                  possible.
                </p>
                <button
                  className="contact-success-btn"
                  onClick={() => setSubmitted(false)}
                >
                  Send Another Message
                </button>
              </div>
            ) : (
              <>
                <h2 className="contact-form-title">Send Us a Message</h2>
                <p className="contact-form-subtitle">
                  Fill out the form below and our team will respond within 24 hours.
                </p>
                <form
                  className="contact-form"
                  onSubmit={handleSubmit}
                  noValidate
                >
                  <div className="contact-form-row">
                    <div className="contact-input-group">
                      <label htmlFor="contact-name" className="contact-label">
                        Full Name
                      </label>
                      <input
                        id="contact-name"
                        name="name"
                        type="text"
                        placeholder="Your full name"
                        value={formData.name}
                        onChange={handleChange}
                        className={`contact-input ${errors.name ? 'contact-input-error' : ''}`}
                        maxLength={100}
                      />
                      {errors.name && (
                        <span className="contact-error-msg">{errors.name}</span>
                      )}
                    </div>
                    <div className="contact-input-group">
                      <label htmlFor="contact-email" className="contact-label">
                        Email Address
                      </label>
                      <input
                        id="contact-email"
                        name="email"
                        type="email"
                        placeholder="your@email.com"
                        value={formData.email}
                        onChange={handleChange}
                        className={`contact-input ${errors.email ? 'contact-input-error' : ''}`}
                        maxLength={150}
                      />
                      {errors.email && (
                        <span className="contact-error-msg">{errors.email}</span>
                      )}
                    </div>
                  </div>

                  <div className="contact-input-group">
                    <label htmlFor="contact-subject" className="contact-label">
                      Subject
                    </label>
                    <input
                      id="contact-subject"
                      name="subject"
                      type="text"
                      placeholder="What is this about?"
                      value={formData.subject}
                      onChange={handleChange}
                      className={`contact-input ${errors.subject ? 'contact-input-error' : ''}`}
                      maxLength={200}
                    />
                    {errors.subject && (
                      <span className="contact-error-msg">{errors.subject}</span>
                    )}
                  </div>

                  <div className="contact-input-group">
                    <label htmlFor="contact-message" className="contact-label">
                      Message
                    </label>
                    <textarea
                      id="contact-message"
                      name="message"
                      placeholder="Tell us how we can help you..."
                      value={formData.message}
                      onChange={handleChange}
                      className={`contact-textarea ${errors.message ? 'contact-input-error' : ''}`}
                      rows={6}
                      maxLength={3000}
                    />
                    {errors.message && (
                      <span className="contact-error-msg">{errors.message}</span>
                    )}
                    <span className="contact-char-count">
                      {formData.message.length}/3000
                    </span>
                  </div>

                  <button
                    type="submit"
                    className="contact-submit-btn"
                    disabled={submitting}
                  >
                    {submitting ? (
                      <span className="contact-btn-loading">
                        <span className="contact-spinner" />
                        Sending...
                      </span>
                    ) : (
                      <>
                        <FiSend />
                        Send Message
                      </>
                    )}
                  </button>
                </form>
              </>
            )}
          </div>

          {/* Contact Info Sidebar */}
          <div className="contact-info-section">
            <h3 className="contact-info-title">Contact Information</h3>
            <p className="contact-info-subtitle">
              Reach out to us through any of the following channels.
            </p>

            <div className="contact-info-cards">
              <div className="contact-info-card">
                <div className="contact-info-card-icon">
                  <FiMail />
                </div>
                <div className="contact-info-card-body">
                  <h4 className="contact-info-card-label">Email</h4>
                  <a
                    href="mailto:support@leisuretimez.com"
                    className="contact-info-card-value"
                  >
                    support@leisuretimez.com
                  </a>
                </div>
              </div>

              <div className="contact-info-card">
                <div className="contact-info-card-icon">
                  <FiPhone />
                </div>
                <div className="contact-info-card-body">
                  <h4 className="contact-info-card-label">Phone</h4>
                  <a
                    href="tel:+18001234567"
                    className="contact-info-card-value"
                  >
                    +1 (800) 123-4567
                  </a>
                </div>
              </div>

              <div className="contact-info-card">
                <div className="contact-info-card-icon">
                  <FiMapPin />
                </div>
                <div className="contact-info-card-body">
                  <h4 className="contact-info-card-label">Address</h4>
                  <p className="contact-info-card-value">
                    123 Travel Street, Suite 100
                    <br />
                    Adventure City, AC 10001
                  </p>
                </div>
              </div>
            </div>

            <div className="contact-info-hours">
              <h4 className="contact-info-hours-title">Business Hours</h4>
              <ul className="contact-info-hours-list">
                <li>
                  <span>Monday - Friday</span>
                  <span>9:00 AM - 6:00 PM</span>
                </li>
                <li>
                  <span>Saturday</span>
                  <span>10:00 AM - 4:00 PM</span>
                </li>
                <li>
                  <span>Sunday</span>
                  <span>Closed</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
