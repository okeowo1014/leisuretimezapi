import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { packages, reviews } from '../api/endpoints';
import { useAuth } from '../context/AuthContext';
import StarRating from '../components/ui/StarRating';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import {
  formatCurrency,
  formatDate,
  getImageUrl,
  truncate,
} from '../utils/helpers';
import toast from 'react-hot-toast';
import {
  FiHeart,
  FiClock,
  FiMapPin,
  FiUsers,
  FiCalendar,
  FiStar,
  FiShare2,
  FiChevronLeft,
  FiChevronRight,
} from 'react-icons/fi';
import './PackageDetailPage.css';

export default function PackageDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { isAuthenticated, user } = useAuth();

  // Package data
  const [pkg, setPkg] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Image gallery
  const [selectedImageIndex, setSelectedImageIndex] = useState(0);

  // Save state
  const [isSaved, setIsSaved] = useState(false);
  const [savingToggle, setSavingToggle] = useState(false);

  // Check offer
  const [adultCount, setAdultCount] = useState(1);
  const [childrenCount, setChildrenCount] = useState(0);
  const [offerResult, setOfferResult] = useState(null);
  const [checkingOffer, setCheckingOffer] = useState(false);

  // Reviews
  const [reviewList, setReviewList] = useState([]);
  const [reviewsLoading, setReviewsLoading] = useState(true);

  // Review form
  const [reviewRating, setReviewRating] = useState(0);
  const [reviewComment, setReviewComment] = useState('');
  const [submittingReview, setSubmittingReview] = useState(false);

  // Fetch package details
  useEffect(() => {
    let cancelled = false;

    const fetchPackage = async () => {
      setLoading(true);
      setError(null);
      try {
        const { data } = await packages.get(id);
        if (!cancelled) {
          setPkg(data);
          setIsSaved(data.is_saved || false);
        }
      } catch (err) {
        if (!cancelled) {
          setError('Failed to load package details.');
          toast.error('Could not load package details');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    fetchPackage();
    return () => {
      cancelled = true;
    };
  }, [id]);

  // Fetch reviews
  useEffect(() => {
    let cancelled = false;

    const fetchReviews = async () => {
      setReviewsLoading(true);
      try {
        const { data } = await reviews.list(id);
        if (!cancelled) {
          setReviewList(data.results || data);
        }
      } catch {
        if (!cancelled) setReviewList([]);
      } finally {
        if (!cancelled) setReviewsLoading(false);
      }
    };

    fetchReviews();
    return () => {
      cancelled = true;
    };
  }, [id]);

  // Build images array
  const images = pkg
    ? [
        ...(pkg.main_image ? [pkg.main_image] : []),
        ...(pkg.images || []).map((img) => (typeof img === 'string' ? img : img.image || img.url)),
      ]
    : [];

  // If no images, provide placeholder
  const displayImages = images.length > 0 ? images : [null];

  // Gallery navigation
  const goToPrevImage = () => {
    setSelectedImageIndex((prev) =>
      prev === 0 ? displayImages.length - 1 : prev - 1
    );
  };

  const goToNextImage = () => {
    setSelectedImageIndex((prev) =>
      prev === displayImages.length - 1 ? 0 : prev + 1
    );
  };

  // Save / Unsave
  const handleToggleSave = async () => {
    if (!isAuthenticated) {
      toast.error('Please log in to save packages');
      navigate('/login');
      return;
    }

    setSavingToggle(true);
    try {
      if (isSaved) {
        await packages.unsave(id);
        setIsSaved(false);
        toast.success('Removed from saved');
      } else {
        await packages.save(id);
        setIsSaved(true);
        toast.success('Package saved!');
      }
    } catch {
      toast.error('Failed to update saved status');
    } finally {
      setSavingToggle(false);
    }
  };

  // Share
  const handleShare = async () => {
    const shareUrl = window.location.href;
    if (navigator.share) {
      try {
        await navigator.share({
          title: pkg?.name,
          text: pkg?.description ? truncate(pkg.description, 120) : 'Check out this travel package!',
          url: shareUrl,
        });
      } catch {
        // User cancelled share
      }
    } else {
      try {
        await navigator.clipboard.writeText(shareUrl);
        toast.success('Link copied to clipboard!');
      } catch {
        toast.error('Failed to copy link');
      }
    }
  };

  // Check Offer
  const handleCheckOffer = async () => {
    if (adultCount < 1) {
      toast.error('At least 1 adult is required');
      return;
    }

    setCheckingOffer(true);
    setOfferResult(null);
    try {
      const { data } = await packages.checkOffer(id, {
        adults: adultCount,
        children: childrenCount,
      });
      setOfferResult(data);
    } catch (err) {
      const msg = err.response?.data?.error || err.response?.data?.detail || 'Failed to check offer';
      toast.error(msg);
    } finally {
      setCheckingOffer(false);
    }
  };

  // Submit Review
  const handleSubmitReview = async (e) => {
    e.preventDefault();

    if (!reviewRating) {
      toast.error('Please select a rating');
      return;
    }
    if (!reviewComment.trim()) {
      toast.error('Please write a comment');
      return;
    }

    setSubmittingReview(true);
    try {
      const { data } = await reviews.create(id, {
        rating: reviewRating,
        comment: reviewComment.trim(),
      });
      setReviewList((prev) => [data, ...prev]);
      setReviewRating(0);
      setReviewComment('');
      toast.success('Review submitted!');
    } catch (err) {
      const msg = err.response?.data?.error || err.response?.data?.detail || 'Failed to submit review';
      toast.error(msg);
    } finally {
      setSubmittingReview(false);
    }
  };

  // Book Now
  const handleBookNow = () => {
    if (!isAuthenticated) {
      toast.error('Please log in to book this package');
      navigate('/login');
      return;
    }
    navigate(`/book/${id}`);
  };

  // Compute average rating
  const averageRating =
    reviewList.length > 0
      ? reviewList.reduce((sum, r) => sum + (r.rating || 0), 0) / reviewList.length
      : 0;

  // Price info
  const hasDiscount = pkg?.discount_price && pkg.discount_price < pkg.price;
  const displayPrice = hasDiscount ? pkg.discount_price : pkg?.price;

  if (loading) {
    return (
      <div className="pkg-detail-loading">
        <LoadingSpinner size="large" message="Loading package details..." />
      </div>
    );
  }

  if (error || !pkg) {
    return (
      <div className="pkg-detail-error">
        <h2>Oops!</h2>
        <p>{error || 'Package not found.'}</p>
        <Link to="/packages" className="pkg-detail-back-link">
          Back to Packages
        </Link>
      </div>
    );
  }

  return (
    <div className="pkg-detail-page">
      {/* Breadcrumb */}
      <div className="pkg-detail-breadcrumb">
        <Link to="/packages" className="pkg-detail-breadcrumb-link">
          Packages
        </Link>
        <span className="pkg-detail-breadcrumb-sep">/</span>
        <span className="pkg-detail-breadcrumb-current">{truncate(pkg.name, 40)}</span>
      </div>

      {/* Image Gallery */}
      <div className="pkg-detail-gallery">
        <div className="pkg-detail-gallery-main">
          <img
            src={getImageUrl(displayImages[selectedImageIndex])}
            alt={`${pkg.name} - image ${selectedImageIndex + 1}`}
            className="pkg-detail-gallery-main-img"
            onError={(e) => {
              e.target.src = '/placeholder.svg';
            }}
          />

          {displayImages.length > 1 && (
            <>
              <button
                className="pkg-detail-gallery-nav pkg-detail-gallery-nav-prev"
                onClick={goToPrevImage}
                aria-label="Previous image"
              >
                <FiChevronLeft />
              </button>
              <button
                className="pkg-detail-gallery-nav pkg-detail-gallery-nav-next"
                onClick={goToNextImage}
                aria-label="Next image"
              >
                <FiChevronRight />
              </button>
            </>
          )}

          <div className="pkg-detail-gallery-counter">
            {selectedImageIndex + 1} / {displayImages.length}
          </div>
        </div>

        {displayImages.length > 1 && (
          <div className="pkg-detail-gallery-thumbs">
            {displayImages.map((img, idx) => (
              <button
                key={idx}
                className={`pkg-detail-thumb ${idx === selectedImageIndex ? 'active' : ''}`}
                onClick={() => setSelectedImageIndex(idx)}
                aria-label={`View image ${idx + 1}`}
              >
                <img
                  src={getImageUrl(img)}
                  alt={`Thumbnail ${idx + 1}`}
                  onError={(e) => {
                    e.target.src = '/placeholder.svg';
                  }}
                />
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Content Layout: Main + Sidebar */}
      <div className="pkg-detail-layout">
        {/* Main Content */}
        <div className="pkg-detail-main">
          {/* Title & Actions */}
          <div className="pkg-detail-title-section">
            <div className="pkg-detail-title-top">
              {pkg.category && (
                <span className="pkg-detail-category-badge">{pkg.category}</span>
              )}
              <div className="pkg-detail-actions">
                <button
                  className={`pkg-detail-action-btn ${isSaved ? 'saved' : ''}`}
                  onClick={handleToggleSave}
                  disabled={savingToggle}
                  aria-label={isSaved ? 'Unsave package' : 'Save package'}
                >
                  <FiHeart />
                </button>
                <button
                  className="pkg-detail-action-btn"
                  onClick={handleShare}
                  aria-label="Share package"
                >
                  <FiShare2 />
                </button>
              </div>
            </div>

            <h1 className="pkg-detail-title">{pkg.name}</h1>

            {/* Rating Summary */}
            <div className="pkg-detail-rating-summary">
              <StarRating rating={averageRating} readonly size="small" />
              <span className="pkg-detail-review-count">
                ({reviewList.length} review{reviewList.length !== 1 ? 's' : ''})
              </span>
            </div>
          </div>

          {/* Key Details Cards */}
          <div className="pkg-detail-info-cards">
            {pkg.duration && (
              <div className="pkg-detail-info-card">
                <div className="pkg-detail-info-card-icon">
                  <FiClock />
                </div>
                <div>
                  <span className="pkg-detail-info-card-label">Duration</span>
                  <span className="pkg-detail-info-card-value">{pkg.duration}</span>
                </div>
              </div>
            )}

            {pkg.category && (
              <div className="pkg-detail-info-card">
                <div className="pkg-detail-info-card-icon">
                  <FiMapPin />
                </div>
                <div>
                  <span className="pkg-detail-info-card-label">Category</span>
                  <span className="pkg-detail-info-card-value">{pkg.category}</span>
                </div>
              </div>
            )}

            <div className="pkg-detail-info-card">
              <div className="pkg-detail-info-card-icon">
                <FiUsers />
              </div>
              <div>
                <span className="pkg-detail-info-card-label">Availability</span>
                <span className="pkg-detail-info-card-value">
                  {pkg.available_slots != null
                    ? `${pkg.available_slots} spots left`
                    : pkg.is_available === false
                    ? 'Sold Out'
                    : 'Available'}
                </span>
              </div>
            </div>

            {pkg.start_date && (
              <div className="pkg-detail-info-card">
                <div className="pkg-detail-info-card-icon">
                  <FiCalendar />
                </div>
                <div>
                  <span className="pkg-detail-info-card-label">Start Date</span>
                  <span className="pkg-detail-info-card-value">
                    {formatDate(pkg.start_date)}
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Description */}
          <div className="pkg-detail-description">
            <h2 className="pkg-detail-section-title">About This Package</h2>
            <div className="pkg-detail-description-text">
              {pkg.description
                ? pkg.description.split('\n').map((paragraph, idx) => (
                    <p key={idx}>{paragraph}</p>
                  ))
                : <p>No description available.</p>}
            </div>
          </div>

          {/* Inclusions / Features */}
          {pkg.inclusions && pkg.inclusions.length > 0 && (
            <div className="pkg-detail-inclusions">
              <h2 className="pkg-detail-section-title">What&apos;s Included</h2>
              <ul className="pkg-detail-inclusions-list">
                {pkg.inclusions.map((item, idx) => (
                  <li key={idx} className="pkg-detail-inclusion-item">
                    <span className="pkg-detail-inclusion-check">&#10003;</span>
                    {typeof item === 'string' ? item : item.name || item.title}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Reviews Section */}
          <div className="pkg-detail-reviews-section">
            <h2 className="pkg-detail-section-title">
              <FiStar className="pkg-detail-section-title-icon" />
              Reviews ({reviewList.length})
            </h2>

            {/* Review Form */}
            {isAuthenticated && (
              <form className="pkg-detail-review-form" onSubmit={handleSubmitReview}>
                <h3 className="pkg-detail-review-form-title">Write a Review</h3>

                <div className="pkg-detail-review-form-rating">
                  <span className="pkg-detail-review-form-label">Your Rating:</span>
                  <StarRating rating={reviewRating} onRate={setReviewRating} size="medium" />
                </div>

                <textarea
                  className="pkg-detail-review-textarea"
                  placeholder="Share your experience with this package..."
                  value={reviewComment}
                  onChange={(e) => setReviewComment(e.target.value)}
                  rows={4}
                  maxLength={1000}
                />

                <div className="pkg-detail-review-form-footer">
                  <span className="pkg-detail-review-char-count">
                    {reviewComment.length}/1000
                  </span>
                  <button
                    type="submit"
                    className="pkg-detail-review-submit-btn"
                    disabled={submittingReview}
                  >
                    {submittingReview ? 'Submitting...' : 'Submit Review'}
                  </button>
                </div>
              </form>
            )}

            {!isAuthenticated && (
              <div className="pkg-detail-review-login-prompt">
                <p>
                  <Link to="/login" className="pkg-detail-link">Log in</Link> to leave a review.
                </p>
              </div>
            )}

            {/* Reviews List */}
            {reviewsLoading ? (
              <LoadingSpinner size="small" message="Loading reviews..." />
            ) : reviewList.length === 0 ? (
              <div className="pkg-detail-no-reviews">
                <FiStar className="pkg-detail-no-reviews-icon" />
                <p>No reviews yet. Be the first to share your experience!</p>
              </div>
            ) : (
              <div className="pkg-detail-reviews-list">
                {reviewList.map((review) => (
                  <div key={review.id} className="pkg-detail-review-card">
                    <div className="pkg-detail-review-card-header">
                      <div className="pkg-detail-review-avatar">
                        {(review.user_name || review.user?.firstname || 'U').charAt(0).toUpperCase()}
                      </div>
                      <div className="pkg-detail-review-meta">
                        <span className="pkg-detail-review-author">
                          {review.user_name || review.user?.firstname || 'Anonymous'}
                        </span>
                        <span className="pkg-detail-review-date">
                          {formatDate(review.created_at || review.date)}
                        </span>
                      </div>
                      <div className="pkg-detail-review-rating-badge">
                        <StarRating rating={review.rating} readonly size="small" />
                      </div>
                    </div>
                    <p className="pkg-detail-review-comment">{review.comment}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Sidebar */}
        <div className="pkg-detail-sidebar">
          {/* Pricing Card */}
          <div className="pkg-detail-pricing-card">
            <div className="pkg-detail-pricing-header">
              <div className="pkg-detail-pricing-amount">
                <span className="pkg-detail-price">{formatCurrency(displayPrice)}</span>
                {hasDiscount && (
                  <span className="pkg-detail-original-price">
                    {formatCurrency(pkg.price)}
                  </span>
                )}
              </div>
              <span className="pkg-detail-price-per">per person</span>
              {hasDiscount && (
                <span className="pkg-detail-discount-badge">
                  {Math.round(((pkg.price - pkg.discount_price) / pkg.price) * 100)}% OFF
                </span>
              )}
            </div>

            <button className="pkg-detail-book-btn" onClick={handleBookNow}>
              Book Now
            </button>

            <p className="pkg-detail-pricing-note">
              No hidden fees. Free cancellation available.
            </p>
          </div>

          {/* Check Offer Card */}
          <div className="pkg-detail-offer-card">
            <h3 className="pkg-detail-offer-title">Check Offer</h3>
            <p className="pkg-detail-offer-subtitle">
              Get a personalized price for your group.
            </p>

            <div className="pkg-detail-offer-inputs">
              <div className="pkg-detail-offer-input-group">
                <label className="pkg-detail-offer-label">
                  <FiUsers className="pkg-detail-offer-label-icon" />
                  Adults
                </label>
                <div className="pkg-detail-counter">
                  <button
                    type="button"
                    className="pkg-detail-counter-btn"
                    onClick={() => setAdultCount((c) => Math.max(1, c - 1))}
                    aria-label="Decrease adults"
                  >
                    &minus;
                  </button>
                  <span className="pkg-detail-counter-value">{adultCount}</span>
                  <button
                    type="button"
                    className="pkg-detail-counter-btn"
                    onClick={() => setAdultCount((c) => c + 1)}
                    aria-label="Increase adults"
                  >
                    +
                  </button>
                </div>
              </div>

              <div className="pkg-detail-offer-input-group">
                <label className="pkg-detail-offer-label">
                  <FiUsers className="pkg-detail-offer-label-icon" />
                  Children
                </label>
                <div className="pkg-detail-counter">
                  <button
                    type="button"
                    className="pkg-detail-counter-btn"
                    onClick={() => setChildrenCount((c) => Math.max(0, c - 1))}
                    aria-label="Decrease children"
                  >
                    &minus;
                  </button>
                  <span className="pkg-detail-counter-value">{childrenCount}</span>
                  <button
                    type="button"
                    className="pkg-detail-counter-btn"
                    onClick={() => setChildrenCount((c) => c + 1)}
                    aria-label="Increase children"
                  >
                    +
                  </button>
                </div>
              </div>
            </div>

            <button
              className="pkg-detail-offer-check-btn"
              onClick={handleCheckOffer}
              disabled={checkingOffer}
            >
              {checkingOffer ? 'Checking...' : 'Check Price'}
            </button>

            {offerResult && (
              <div className="pkg-detail-offer-result">
                <div className="pkg-detail-offer-result-row">
                  <span>Total Price</span>
                  <span className="pkg-detail-offer-result-price">
                    {formatCurrency(offerResult.total_price || offerResult.total)}
                  </span>
                </div>
                {offerResult.discount && (
                  <div className="pkg-detail-offer-result-row pkg-detail-offer-result-discount">
                    <span>Discount</span>
                    <span>-{formatCurrency(offerResult.discount)}</span>
                  </div>
                )}
                {(offerResult.final_price || offerResult.grand_total) && (
                  <div className="pkg-detail-offer-result-row pkg-detail-offer-result-final">
                    <span>Final Price</span>
                    <span>{formatCurrency(offerResult.final_price || offerResult.grand_total)}</span>
                  </div>
                )}
                {offerResult.message && (
                  <p className="pkg-detail-offer-result-msg">{offerResult.message}</p>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
