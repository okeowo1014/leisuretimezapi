import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { blog } from '../api/endpoints';
import { formatDate, getImageUrl, truncate } from '../utils/helpers';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import { FiCalendar, FiUser, FiArrowRight } from 'react-icons/fi';
import './BlogPage.css';

export default function BlogPage() {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [pagination, setPagination] = useState({
    count: 0,
    next: null,
    previous: null,
  });

  useEffect(() => {
    const fetchPosts = async () => {
      try {
        setLoading(true);
        setError(null);
        const { data } = await blog.list({ page });
        setPosts(data.results || []);
        setPagination({
          count: data.count || 0,
          next: data.next,
          previous: data.previous,
        });
      } catch (err) {
        console.error('Failed to fetch blog posts:', err);
        setError('Failed to load blog posts. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchPosts();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [page]);

  const totalPages = Math.ceil(pagination.count / (posts.length || 1));

  const handlePrevious = () => {
    if (pagination.previous) {
      setPage((prev) => prev - 1);
    }
  };

  const handleNext = () => {
    if (pagination.next) {
      setPage((prev) => prev + 1);
    }
  };

  return (
    <div className="blog-page">
      {/* Page Header */}
      <section className="blog-page-header">
        <div className="blog-page-header-overlay" />
        <div className="blog-page-header-content">
          <h1 className="blog-page-title">Travel Blog</h1>
          <p className="blog-page-subtitle">
            Stories, tips, and inspiration for your next adventure
          </p>
        </div>
      </section>

      {/* Blog Grid */}
      <section className="blog-page-content">
        <div className="blog-page-container">
          {loading ? (
            <LoadingSpinner size="large" message="Loading blog posts..." />
          ) : error ? (
            <div className="blog-page-error">
              <p>{error}</p>
              <button
                onClick={() => setPage(1)}
                className="blog-page-retry-btn"
              >
                Try Again
              </button>
            </div>
          ) : posts.length === 0 ? (
            <div className="blog-page-empty">
              <p>No blog posts available yet. Check back soon!</p>
            </div>
          ) : (
            <>
              <div className="blog-grid">
                {posts.map((post) => (
                  <Link
                    to={`/blog/${post.slug}`}
                    key={post.id || post.slug}
                    className="blog-card"
                  >
                    <div className="blog-card-image-wrapper">
                      <img
                        src={getImageUrl(post.cover_image)}
                        alt={post.title}
                        className="blog-card-image"
                        onError={(e) => {
                          e.target.src = '/placeholder.svg';
                        }}
                      />
                    </div>
                    <div className="blog-card-body">
                      {post.tags && post.tags.length > 0 && (
                        <div className="blog-card-tags">
                          {post.tags.slice(0, 3).map((tag, idx) => (
                            <span key={idx} className="blog-card-tag">
                              {typeof tag === 'string' ? tag : tag.name}
                            </span>
                          ))}
                        </div>
                      )}
                      <h2 className="blog-card-title">{post.title}</h2>
                      <p className="blog-card-excerpt">
                        {truncate(post.excerpt, 120)}
                      </p>
                      <div className="blog-card-meta">
                        <div className="blog-card-meta-left">
                          <span className="blog-card-meta-item">
                            <FiUser />
                            {post.author_name || post.author?.name || 'Staff'}
                          </span>
                          <span className="blog-card-meta-item">
                            <FiCalendar />
                            {formatDate(post.published_at)}
                          </span>
                        </div>
                        <span className="blog-card-read-more">
                          Read More
                          <FiArrowRight />
                        </span>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>

              {/* Pagination */}
              {pagination.count > 0 && (pagination.next || pagination.previous) && (
                <div className="blog-pagination">
                  <button
                    className="blog-pagination-btn"
                    onClick={handlePrevious}
                    disabled={!pagination.previous}
                  >
                    &larr; Previous
                  </button>
                  <span className="blog-pagination-info">
                    Page {page} of {totalPages || 1}
                  </span>
                  <button
                    className="blog-pagination-btn"
                    onClick={handleNext}
                    disabled={!pagination.next}
                  >
                    Next &rarr;
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </section>
    </div>
  );
}
