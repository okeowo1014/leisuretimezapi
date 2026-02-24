import { useState } from 'react';
import { FiStar } from 'react-icons/fi';
import './StarRating.css';

export default function StarRating({
  rating = 0,
  onRate,
  readonly = false,
  size = 'medium',
  maxStars = 5,
}) {
  const [hoverRating, setHoverRating] = useState(0);

  const handleClick = (starValue) => {
    if (readonly || !onRate) return;
    onRate(starValue);
  };

  const handleMouseEnter = (starValue) => {
    if (readonly) return;
    setHoverRating(starValue);
  };

  const handleMouseLeave = () => {
    if (readonly) return;
    setHoverRating(0);
  };

  const activeRating = hoverRating || rating;

  return (
    <div
      className={`star-rating ${size} ${readonly ? 'readonly' : 'interactive'}`}
      onMouseLeave={handleMouseLeave}
      role={readonly ? 'img' : 'radiogroup'}
      aria-label={`Rating: ${rating} out of ${maxStars} stars`}
    >
      {Array.from({ length: maxStars }, (_, i) => {
        const starValue = i + 1;
        const isFull = starValue <= Math.floor(activeRating);
        const isHalf =
          !isFull &&
          starValue === Math.ceil(activeRating) &&
          activeRating % 1 >= 0.25;

        return (
          <button
            key={starValue}
            type="button"
            className={`star-btn ${isFull ? 'filled' : ''} ${isHalf ? 'half' : ''}`}
            onClick={() => handleClick(starValue)}
            onMouseEnter={() => handleMouseEnter(starValue)}
            disabled={readonly}
            aria-label={`${starValue} star${starValue !== 1 ? 's' : ''}`}
            tabIndex={readonly ? -1 : 0}
          >
            <FiStar className="star-icon" />
            {(isFull || isHalf) && (
              <FiStar
                className={`star-icon-fill ${isHalf ? 'half-fill' : ''}`}
              />
            )}
          </button>
        );
      })}

      {rating > 0 && readonly && (
        <span className="star-rating-value">{rating.toFixed(1)}</span>
      )}
    </div>
  );
}
