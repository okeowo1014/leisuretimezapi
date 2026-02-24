import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import DOMPurify from 'dompurify';
import { blog } from '../api/endpoints';
import { useAuth } from '../context/AuthContext';
import { formatDate, getImageUrl, timeAgo } from '../utils/helpers';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import toast from 'react-hot-toast';
import {
  FiHeart,
  FiMessageSquare,
  FiCalendar,
  FiUser,
  FiArrowLeft,
  FiThumbsUp,
} from 'react-icons/fi';
import './BlogDetailPage.css';

const REACTION_TYPES = [
  { type: 'like', label: 'Like', icon: <FiThumbsUp /> },
  { type: 'love', label: 'Love', icon: <FiHeart /> },
  { type: 'insightful', label: 'Insightful', icon: <FiMessageSquare /> },
  { type: 'celebrate', label: 'Celebrate', icon: <span className="blog-detail-reaction-emoji">&#127881;</span> },
];

export default function BlogDetailPage() {
  const { slug } = useParams();
  const { isAuthenticated, user } = useAuth();

  const [post, setPost] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reactingType, setReactingType] = useState(null);
  const [commentText, setCommentText] = useState('');
  const [submittingComment, setSubmittingComment] = useState(false);

  useEffect(() => {
    const fetchPost = async () => {
      try {
        setLoading(true);
        setError(null);
        const { data } = await blog.get(slug);
        setPost(data);
      } catch (err) {
        console.error('Failed to fetch blog post:', err);
        setError('Failed to load the blog post. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    if (slug) {
      fetchPost();
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }, [slug]);

  const handleReaction = async (reactionType) => {
    if (reactingType) return;
    setReactingType(reactionType);
    try {
      const { data } = await blog.react(slug, { reaction_type: reactionType });
      setPost((prev) => ({
        ...prev,
        reactions: data.reactions || prev.reactions,
      }));
      toast.success(`Reacted with ${reactionType}!`);
    } catch (err) {
      const msg =
        err.response?.data?.detail ||
        err.response?.data?.error ||
        'Failed to react. Please try again.';
      toast.error(msg);
    } finally {
      setReactingType(null);
    }
  };

  const handleSubmitComment = async (e) => {
    e.preventDefault();
    const content = commentText.trim();
    if (!content) {
      toast.error('Please write a comment before submitting.');
      return;
    }

    setSubmittingComment(true);
    try {
      const { data } = await blog.addComment(slug, { content });
      setPost((prev) => ({
        ...prev,
        comments: [...(prev.comments || []), data],
      }));
      setCommentText('');
      toast.success('Comment added successfully!');
    } catch (err) {
      const msg =
        err.response?.data?.detail ||
        err.response?.data?.error ||
        'Failed to add comment. Please try again.';
      toast.error(msg);
    } finally {
      setSubmittingComment(false);
    }
  };

  const getReactionCount = (type) => {
    if (!post?.reactions) return 0;
    if (Array.isArray(post.reactions)) {
      const found = post.reactions.find((r) => r.reaction_type === type);
      return found?.count || 0;
    }
    return post.reactions[type] || 0;
  };

  if (loading) {
    return (
      <div className="blog-detail-page">
        <LoadingSpinner size="large" message="Loading article..." />
      </div>
    );
  }

  if (error || !post) {
    return (
      <div className="blog-detail-page">
        <div className="blog-detail-error">
          <p>{error || 'Post not found.'}</p>
          <Link to="/blog" className="blog-detail-back-link">
            <FiArrowLeft />
            Back to Blog
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="blog-detail-page">
      {/* Hero Cover Image */}
      {post.cover_image && (
        <div className="blog-detail-hero">
          <img
            src={getImageUrl(post.cover_image)}
            alt={post.title}
            className="blog-detail-hero-image"
            onError={(e) => {
              e.target.src = '/placeholder.svg';
            }}
          />
          <div className="blog-detail-hero-overlay" />
        </div>
      )}

      {/* Article Content */}
      <article className="blog-detail-article">
        <div className="blog-detail-container">
          {/* Back Link */}
          <Link to="/blog" className="blog-detail-back-link">
            <FiArrowLeft />
            Back to Blog
          </Link>

          {/* Post Header */}
          <header className="blog-detail-header">
            {post.tags && post.tags.length > 0 && (
              <div className="blog-detail-tags">
                {post.tags.map((tag, idx) => (
                  <span key={idx} className="blog-detail-tag">
                    {typeof tag === 'string' ? tag : tag.name}
                  </span>
                ))}
              </div>
            )}
            <h1 className="blog-detail-title">{post.title}</h1>
            <div className="blog-detail-meta">
              <span className="blog-detail-meta-item">
                <FiUser />
                {post.author_name || post.author?.name || 'Staff'}
              </span>
              <span className="blog-detail-meta-divider">&bull;</span>
              <span className="blog-detail-meta-item">
                <FiCalendar />
                {formatDate(post.published_at)}
              </span>
            </div>
          </header>

          {/* Post Content */}
          <div
            className="blog-detail-content"
            dangerouslySetInnerHTML={{
              __html: DOMPurify.sanitize(post.content),
            }}
          />

          {/* Reactions Section */}
          <div className="blog-detail-reactions">
            <h3 className="blog-detail-reactions-title">
              What did you think?
            </h3>
            <div className="blog-detail-reactions-bar">
              {REACTION_TYPES.map(({ type, label, icon }) => (
                <button
                  key={type}
                  className={`blog-detail-reaction-btn ${
                    reactingType === type ? 'reacting' : ''
                  }`}
                  onClick={() => handleReaction(type)}
                  disabled={!!reactingType}
                  title={label}
                >
                  <span className="blog-detail-reaction-icon">{icon}</span>
                  <span className="blog-detail-reaction-label">{label}</span>
                  <span className="blog-detail-reaction-count">
                    {getReactionCount(type)}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* Comments Section */}
          <div className="blog-detail-comments">
            <h3 className="blog-detail-comments-title">
              <FiMessageSquare />
              Comments
              {post.comments && post.comments.length > 0 && (
                <span className="blog-detail-comments-count">
                  ({post.comments.length})
                </span>
              )}
            </h3>

            {/* Comments List */}
            {post.comments && post.comments.length > 0 ? (
              <div className="blog-detail-comments-list">
                {post.comments.map((comment, idx) => (
                  <div key={comment.id || idx} className="blog-detail-comment">
                    <div className="blog-detail-comment-avatar">
                      <FiUser />
                    </div>
                    <div className="blog-detail-comment-body">
                      <div className="blog-detail-comment-header">
                        <span className="blog-detail-comment-author">
                          {comment.user_name ||
                            comment.user?.name ||
                            comment.author_name ||
                            'Anonymous'}
                        </span>
                        <span className="blog-detail-comment-time">
                          {timeAgo(comment.created_at)}
                        </span>
                      </div>
                      <p className="blog-detail-comment-content">
                        {comment.content}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="blog-detail-no-comments">
                No comments yet. Be the first to share your thoughts!
              </p>
            )}

            {/* Comment Form */}
            {isAuthenticated ? (
              <form
                className="blog-detail-comment-form"
                onSubmit={handleSubmitComment}
              >
                <div className="blog-detail-comment-form-header">
                  <FiUser className="blog-detail-comment-form-avatar-icon" />
                  <span className="blog-detail-comment-form-user">
                    Commenting as{' '}
                    <strong>
                      {user?.firstname
                        ? `${user.firstname} ${user.lastname || ''}`
                        : user?.email || 'User'}
                    </strong>
                  </span>
                </div>
                <textarea
                  className="blog-detail-comment-textarea"
                  placeholder="Write your comment..."
                  value={commentText}
                  onChange={(e) => setCommentText(e.target.value)}
                  rows={4}
                  maxLength={2000}
                />
                <div className="blog-detail-comment-form-actions">
                  <span className="blog-detail-comment-char-count">
                    {commentText.length}/2000
                  </span>
                  <button
                    type="submit"
                    className="blog-detail-comment-submit-btn"
                    disabled={submittingComment || !commentText.trim()}
                  >
                    {submittingComment ? 'Posting...' : 'Post Comment'}
                  </button>
                </div>
              </form>
            ) : (
              <div className="blog-detail-comment-login-prompt">
                <p>
                  <Link to="/login">Sign in</Link> to leave a comment.
                </p>
              </div>
            )}
          </div>
        </div>
      </article>
    </div>
  );
}
