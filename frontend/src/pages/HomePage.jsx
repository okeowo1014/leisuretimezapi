import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { packages } from '../api/endpoints';
import PackageCard from '../components/ui/PackageCard';
import { getImageUrl, formatCurrency } from '../utils/helpers';
import {
  FiArrowRight,
  FiShield,
  FiAward,
  FiDollarSign,
  FiHeadphones,
  FiMapPin,
  FiCalendar,
} from 'react-icons/fi';
import './HomePage.css';

export default function HomePage() {
  const [indexData, setIndexData] = useState({
    packages: [],
    destinations: [],
    events: [],
    carousel: [],
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchIndex = async () => {
      try {
        setLoading(true);
        const res = await packages.getIndex();
        setIndexData({
          packages: res.data.packages || [],
          destinations: res.data.destinations || [],
          events: res.data.events || [],
          carousel: res.data.carousel || [],
        });
      } catch (err) {
        console.error('Failed to fetch index data:', err);
        setError('Failed to load content. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchIndex();
  }, []);

  const featuredPackages = indexData.packages.slice(0, 6);
  const featuredEvents = indexData.events.slice(0, 6);

  const features = [
    {
      icon: <FiShield />,
      title: 'Secure Booking',
      description:
        'Your personal information and payments are protected with industry-leading security standards.',
    },
    {
      icon: <FiAward />,
      title: 'Top Quality',
      description:
        'Every package is handpicked and vetted by travel experts to guarantee an exceptional experience.',
    },
    {
      icon: <FiDollarSign />,
      title: 'Best Prices',
      description:
        'We negotiate directly with partners to bring you the most competitive prices available.',
    },
    {
      icon: <FiHeadphones />,
      title: '24/7 Support',
      description:
        'Our dedicated support team is always available to assist you before, during, and after your trip.',
    },
  ];

  if (loading) {
    return (
      <div className="home-loading">
        <div className="home-loading-spinner" />
        <p>Loading amazing destinations...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="home-error">
        <p>{error}</p>
        <button onClick={() => window.location.reload()} className="home-retry-btn">
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="home-page">
      {/* ==================== HERO SECTION ==================== */}
      <section className="hero-section">
        <div className="hero-overlay" />
        {indexData.carousel.length > 0 && (
          <img
            src={getImageUrl(indexData.carousel[0]?.image)}
            alt=""
            className="hero-bg-image"
          />
        )}
        <div className="hero-content">
          <span className="hero-badge">Your Next Adventure Awaits</span>
          <h1 className="hero-title">
            Discover the World's Most <span>Breathtaking</span> Destinations
          </h1>
          <p className="hero-subtitle">
            From tropical paradises to cultural landmarks, we craft unforgettable
            travel experiences tailored just for you. Explore curated packages
            at unbeatable prices.
          </p>
          <div className="hero-actions">
            <Link to="/packages" className="hero-btn hero-btn-primary">
              Explore Packages
              <FiArrowRight />
            </Link>
            <Link to="/contact" className="hero-btn hero-btn-secondary">
              Plan My Trip
            </Link>
          </div>
          <div className="hero-stats">
            <div className="hero-stat">
              <span className="hero-stat-value">500+</span>
              <span className="hero-stat-label">Destinations</span>
            </div>
            <div className="hero-stat-divider" />
            <div className="hero-stat">
              <span className="hero-stat-value">10K+</span>
              <span className="hero-stat-label">Happy Travellers</span>
            </div>
            <div className="hero-stat-divider" />
            <div className="hero-stat">
              <span className="hero-stat-value">4.9</span>
              <span className="hero-stat-label">User Rating</span>
            </div>
          </div>
        </div>
      </section>

      {/* ==================== FEATURED PACKAGES ==================== */}
      {featuredPackages.length > 0 && (
        <section className="home-section packages-section">
          <div className="section-container">
            <div className="section-header">
              <div>
                <span className="section-tag">Top Picks</span>
                <h2 className="section-title">Featured Packages</h2>
                <p className="section-subtitle">
                  Handpicked travel experiences loved by thousands of explorers
                </p>
              </div>
              <Link to="/packages" className="section-view-all">
                View All Packages
                <FiArrowRight />
              </Link>
            </div>
            <div className="packages-grid">
              {featuredPackages.map((pkg) => (
                <PackageCard key={pkg.id} pkg={pkg} />
              ))}
            </div>
          </div>
        </section>
      )}

      {/* ==================== DESTINATIONS ==================== */}
      {indexData.destinations.length > 0 && (
        <section className="home-section destinations-section">
          <div className="section-container">
            <div className="section-header">
              <div>
                <span className="section-tag">Explore</span>
                <h2 className="section-title">Popular Destinations</h2>
                <p className="section-subtitle">
                  Trending locations handpicked by our travel experts
                </p>
              </div>
            </div>
            <div className="destinations-scroll">
              {indexData.destinations.map((dest, idx) => (
                <Link
                  to={`/packages?destination=${dest.id || dest.name}`}
                  key={dest.id || idx}
                  className="destination-card"
                >
                  <img
                    src={getImageUrl(dest.image)}
                    alt={dest.name}
                    className="destination-card-image"
                    onError={(e) => {
                      e.target.src = '/placeholder.svg';
                    }}
                  />
                  <div className="destination-card-overlay" />
                  <div className="destination-card-content">
                    <FiMapPin className="destination-card-icon" />
                    <h3 className="destination-card-name">{dest.name}</h3>
                    {dest.package_count !== undefined && (
                      <span className="destination-card-count">
                        {dest.package_count} {dest.package_count === 1 ? 'package' : 'packages'}
                      </span>
                    )}
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* ==================== WHY CHOOSE US ==================== */}
      <section className="home-section features-section">
        <div className="section-container">
          <div className="section-header section-header-centered">
            <span className="section-tag">Why LeisureTimez</span>
            <h2 className="section-title">Why Choose Us</h2>
            <p className="section-subtitle">
              We go above and beyond to make every journey seamless and memorable
            </p>
          </div>
          <div className="features-grid">
            {features.map((feature, idx) => (
              <div key={idx} className="feature-card">
                <div className="feature-icon">{feature.icon}</div>
                <h3 className="feature-title">{feature.title}</h3>
                <p className="feature-description">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ==================== EVENTS ==================== */}
      {featuredEvents.length > 0 && (
        <section className="home-section events-section">
          <div className="section-container">
            <div className="section-header">
              <div>
                <span className="section-tag">What's On</span>
                <h2 className="section-title">Upcoming Events</h2>
                <p className="section-subtitle">
                  Don't miss out on exciting travel events and experiences
                </p>
              </div>
              <Link to="/events" className="section-view-all">
                View All Events
                <FiArrowRight />
              </Link>
            </div>
            <div className="events-grid">
              {featuredEvents.map((event, idx) => (
                <Link
                  to={`/events/${event.id}`}
                  key={event.id || idx}
                  className="event-card"
                >
                  <div className="event-card-image-wrapper">
                    <img
                      src={getImageUrl(event.image || event.main_image)}
                      alt={event.name || event.title}
                      className="event-card-image"
                      onError={(e) => {
                        e.target.src = '/placeholder.svg';
                      }}
                    />
                    <div className="event-card-image-overlay" />
                    {(event.start_date || event.date) && (
                      <div className="event-card-date-badge">
                        <FiCalendar />
                        <span>
                          {new Date(event.start_date || event.date).toLocaleDateString(
                            'en-US',
                            { month: 'short', day: 'numeric' }
                          )}
                        </span>
                      </div>
                    )}
                  </div>
                  <div className="event-card-body">
                    <h3 className="event-card-title">
                      {event.name || event.title}
                    </h3>
                    {event.location && (
                      <span className="event-card-location">
                        <FiMapPin />
                        {event.location}
                      </span>
                    )}
                    {event.description && (
                      <p className="event-card-description">
                        {event.description.length > 100
                          ? event.description.slice(0, 100) + '...'
                          : event.description}
                      </p>
                    )}
                    {event.price !== undefined && event.price !== null && (
                      <span className="event-card-price">
                        {Number(event.price) === 0
                          ? 'Free'
                          : formatCurrency(event.price)}
                      </span>
                    )}
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* ==================== CTA SECTION ==================== */}
      <section className="cta-section">
        <div className="cta-container">
          <div className="cta-content">
            <span className="cta-badge">Personalised Travel</span>
            <h2 className="cta-title">
              Want a Trip Tailored Just for You?
            </h2>
            <p className="cta-subtitle">
              Tell us your dream destination, budget, and preferences. Our travel
              experts will craft a personalised itinerary that matches your vision
              perfectly.
            </p>
            <div className="cta-actions">
              <Link to="/personalised-booking" className="cta-btn cta-btn-primary">
                Create Custom Booking
                <FiArrowRight />
              </Link>
              <Link to="/contact" className="cta-btn cta-btn-secondary">
                Talk to an Expert
              </Link>
            </div>
          </div>
          <div className="cta-decoration">
            <div className="cta-circle cta-circle-1" />
            <div className="cta-circle cta-circle-2" />
            <div className="cta-circle cta-circle-3" />
          </div>
        </div>
      </section>
    </div>
  );
}
