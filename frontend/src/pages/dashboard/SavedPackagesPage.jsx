import { useState, useEffect } from 'react';
import { packages } from '../../api/endpoints';
import LoadingSpinner from '../../components/ui/LoadingSpinner';
import EmptyState from '../../components/ui/EmptyState';
import PackageCard from '../../components/ui/PackageCard';
import toast from 'react-hot-toast';
import { FiHeart, FiTrash2 } from 'react-icons/fi';
import './SavedPackagesPage.css';

export default function SavedPackagesPage() {
  const [savedList, setSavedList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [removingId, setRemovingId] = useState(null);

  useEffect(() => {
    fetchSaved();
  }, []);

  const fetchSaved = async () => {
    setLoading(true);
    try {
      const { data } = await packages.getSaved();
      const list = Array.isArray(data) ? data : data.results || data.packages || [];
      setSavedList(list);
    } catch (err) {
      toast.error('Failed to load saved packages');
    } finally {
      setLoading(false);
    }
  };

  const handleUnsave = async (pkgId) => {
    setRemovingId(pkgId);
    try {
      await packages.unsave(pkgId);
      setSavedList((prev) => prev.filter((p) => (p.id || p.package?.id) !== pkgId));
      toast.success('Package removed from saved');
    } catch (err) {
      toast.error('Failed to remove package');
    } finally {
      setRemovingId(null);
    }
  };

  if (loading) return <LoadingSpinner message="Loading saved packages..." />;

  if (!savedList.length) {
    return (
      <div className="saved-packages-page">
        <h1 className="saved-packages-title">Saved Packages</h1>
        <EmptyState
          icon={FiHeart}
          title="No saved packages"
          description="Save your favorite travel packages to find them easily later."
          actionLabel="Browse Packages"
          actionLink="/packages"
        />
      </div>
    );
  }

  return (
    <div className="saved-packages-page">
      <div className="saved-packages-header">
        <h1 className="saved-packages-title">Saved Packages</h1>
        <span className="saved-packages-count">
          {savedList.length} saved
        </span>
      </div>

      <div className="saved-packages-grid">
        {savedList.map((item) => {
          const pkg = item.package || item;
          const pkgId = pkg.id || item.id;

          return (
            <div key={pkgId} className="saved-package-item">
              <PackageCard
                pkg={pkg}
                onSave={() => handleUnsave(pkgId)}
              />
              <button
                className="saved-package-remove-btn"
                onClick={() => handleUnsave(pkgId)}
                disabled={removingId === pkgId}
                title="Remove from saved"
              >
                {removingId === pkgId ? (
                  <span className="saved-remove-spinner" />
                ) : (
                  <>
                    <FiTrash2 /> Remove
                  </>
                )}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
