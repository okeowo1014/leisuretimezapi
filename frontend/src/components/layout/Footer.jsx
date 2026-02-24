import { Link } from 'react-router-dom';
import { FiMapPin, FiMail, FiPhone, FiInstagram, FiFacebook, FiTwitter } from 'react-icons/fi';
import './Footer.css';

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-container">
        <div className="footer-grid">
          <div className="footer-brand">
            <Link to="/" className="footer-logo">
              <span className="footer-logo-icon">L</span>
              <span>LeisureTimez</span>
            </Link>
            <p className="footer-tagline">
              Crafting unforgettable travel experiences. Discover the world with curated packages,
              luxury cruises, and personalized adventures.
            </p>
            <div className="footer-social">
              <a href="#" aria-label="Instagram"><FiInstagram /></a>
              <a href="#" aria-label="Facebook"><FiFacebook /></a>
              <a href="#" aria-label="Twitter"><FiTwitter /></a>
            </div>
          </div>

          <div className="footer-links">
            <h4>Explore</h4>
            <Link to="/packages">All Packages</Link>
            <Link to="/packages?category=tourism">Tourism</Link>
            <Link to="/packages?category=cruise">Cruises</Link>
            <Link to="/packages?category=hotel">Hotels</Link>
            <Link to="/blog">Travel Blog</Link>
          </div>

          <div className="footer-links">
            <h4>Company</h4>
            <Link to="/contact">Contact Us</Link>
            <Link to="/blog">Blog</Link>
            <a href="#">Privacy Policy</a>
            <a href="#">Terms of Service</a>
          </div>

          <div className="footer-contact">
            <h4>Get in Touch</h4>
            <div className="contact-item">
              <FiMail />
              <span>support@leisuretimez.com</span>
            </div>
            <div className="contact-item">
              <FiPhone />
              <span>+1 (555) 123-4567</span>
            </div>
            <div className="contact-item">
              <FiMapPin />
              <span>New York, NY</span>
            </div>
          </div>
        </div>

        <div className="footer-bottom">
          <p>&copy; {new Date().getFullYear()} LeisureTimez. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
}
