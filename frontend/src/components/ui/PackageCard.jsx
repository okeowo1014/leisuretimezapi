import { useState } from 'react';
import { Link } from 'react-router-dom';
import { FiHeart, FiClock, FiMapPin } from 'react-icons/fi';
import { formatCurrency, truncate, getImageUrl } from '../../utils/helpers';
import './PackageCard.css';

export default function PackageCard({ pkg, onSave }) {
  const [saved, setSaved] = useState(false);
  const [imageLoaded, setImageLoaded] = useState(false);

  const {
    id,
    name,
    main_image,
    price,
    duration,
    category,
    description,
    discount_price,
  } = pkg;

  const hasDiscount = discount_price && discount_price < price;
  const displayPrice = hasDiscount ? discount_price : price;
  const discountPercent = hasDiscount
    ? Math.round(((price - discount_price) / price) * 100)
    : 0;

  const handleSave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setSaved(!saved);
    if (onSave) onSave(id, !saved);
  };

  return (
    <div className="package-card">
      <div className="package-card-image-wrapper">
        <Link to={`/packages/${id}`}>
          {!imageLoaded && <div className="package-card-image-skeleton" />}
          <img
            src={getImageUrl(main_image)}
            alt={name}
            className={`package-card-image ${imageLoaded ? 'loaded' : ''}`}
            onLoad={() => setImageLoaded(true)}
            onError={(e) => {
              e.target.src = '/placeholder.svg';
              setImageLoaded(true);
            }}
          />
        </Link>

        {category && (
          <span className="package-card-category">{category}</span>
        )}

        {hasDiscount && (
          <span className="package-card-discount">-{discountPercent}%</span>
        )}

        <button
          className={`package-card-save ${saved ? 'saved' : ''}`}
          onClick={handleSave}
          aria-label={saved ? 'Remove from saved' : 'Save package'}
        >
          <FiHeart />
        </button>
      </div>

      <div className="package-card-body">
        <Link to={`/packages/${id}`} className="package-card-title-link">
          <h3 className="package-card-title">{name}</h3>
        </Link>

        {description && (
          <p className="package-card-description">
            {truncate(description, 90)}
          </p>
        )}

        <div className="package-card-meta">
          {duration && (
            <span className="package-card-meta-item">
              <FiClock />
              {duration}
            </span>
          )}
          {category && (
            <span className="package-card-meta-item">
              <FiMapPin />
              {category}
            </span>
          )}
        </div>

        <div className="package-card-footer">
          <div className="package-card-pricing">
            <span className="package-card-price">
              {formatCurrency(displayPrice)}
            </span>
            {hasDiscount && (
              <span className="package-card-original-price">
                {formatCurrency(price)}
              </span>
            )}
            <span className="package-card-per-person">/ person</span>
          </div>

          <Link to={`/packages/${id}`} className="package-card-view-btn">
            View Details
          </Link>
        </div>
      </div>
    </div>
  );
}
