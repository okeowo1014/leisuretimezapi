import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { packages } from '../api/endpoints';
import PackageCard from '../components/ui/PackageCard';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import EmptyState from '../components/ui/EmptyState';
import { FiSearch, FiFilter, FiChevronLeft, FiChevronRight } from 'react-icons/fi';
import toast from 'react-hot-toast';
import './PackagesPage.css';

const CATEGORIES = [
  { value: '', label: 'All Categories' },
  { value: 'tourism', label: 'Tourism' },
  { value: 'cruise', label: 'Cruise' },
  { value: 'hotel', label: 'Hotel' },
  { value: 'adventure', label: 'Adventure' },
];

const SORT_OPTIONS = [
  { value: '', label: 'Default' },
  { value: 'price_asc', label: 'Price: Low to High' },
  { value: 'price_desc', label: 'Price: High to Low' },
  { value: 'newest', label: 'Newest First' },
  { value: 'popular', label: 'Most Popular' },
];

const PAGE_SIZE = 9;

export default function PackagesPage() {
  const [searchParams, setSearchParams] = useSearchParams();

  const [packageList, setPackageList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [totalCount, setTotalCount] = useState(0);
  const [nextPage, setNextPage] = useState(null);
  const [prevPage, setPrevPage] = useState(null);

  // Derive filter state from URL params
  const category = searchParams.get('category') || '';
  const sort = searchParams.get('sort') || '';
  const search = searchParams.get('search') || '';
  const page = parseInt(searchParams.get('page') || '1', 10);

  // Local search input state (debounced)
  const [searchInput, setSearchInput] = useState(search);

  // Sync searchInput when URL param changes externally
  useEffect(() => {
    setSearchInput(search);
  }, [search]);

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchInput !== search) {
        updateParams({ search: searchInput, page: '1' });
      }
    }, 400);
    return () => clearTimeout(timer);
  }, [searchInput]);

  const updateParams = useCallback(
    (updates) => {
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev);
        Object.entries(updates).forEach(([key, value]) => {
          if (value) {
            next.set(key, value);
          } else {
            next.delete(key);
          }
        });
        return next;
      });
    },
    [setSearchParams]
  );

  // Fetch packages whenever filters change
  useEffect(() => {
    let cancelled = false;

    const fetchPackages = async () => {
      setLoading(true);
      try {
        const params = { page, page_size: PAGE_SIZE };

        if (category) params.category = category;
        if (search) params.search = search;

        if (sort === 'price_asc') params.ordering = 'price';
        else if (sort === 'price_desc') params.ordering = '-price';
        else if (sort === 'newest') params.ordering = '-created_at';
        else if (sort === 'popular') params.ordering = '-popularity';

        const { data } = await packages.list(params);

        if (!cancelled) {
          setPackageList(data.results || data);
          setTotalCount(data.count || (data.results ? data.results.length : data.length));
          setNextPage(data.next || null);
          setPrevPage(data.previous || null);
        }
      } catch (err) {
        if (!cancelled) {
          toast.error('Failed to load packages');
          setPackageList([]);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    fetchPackages();
    return () => {
      cancelled = true;
    };
  }, [category, sort, search, page]);

  const handleCategoryChange = (e) => {
    updateParams({ category: e.target.value, page: '1' });
  };

  const handleSortChange = (e) => {
    updateParams({ sort: e.target.value, page: '1' });
  };

  const handleSearchChange = (e) => {
    setSearchInput(e.target.value);
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    updateParams({ search: searchInput, page: '1' });
  };

  const goToPage = (newPage) => {
    updateParams({ page: String(newPage) });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleSavePackage = async (id, shouldSave) => {
    try {
      if (shouldSave) {
        await packages.save(id);
        toast.success('Package saved');
      } else {
        await packages.unsave(id);
        toast.success('Package removed from saved');
      }
    } catch {
      toast.error('Please log in to save packages');
    }
  };

  const clearFilters = () => {
    setSearchParams({});
    setSearchInput('');
  };

  const totalPages = Math.ceil(totalCount / PAGE_SIZE);
  const hasActiveFilters = category || sort || search;

  return (
    <div className="packages-page">
      {/* Page Header */}
      <div className="packages-header">
        <div className="packages-header-content">
          <h1 className="packages-header-title">Explore Travel Packages</h1>
          <p className="packages-header-subtitle">
            Discover curated travel experiences tailored to every type of adventurer.
            Find your perfect getaway from our handpicked collection.
          </p>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="packages-filter-bar">
        <div className="packages-filter-inner">
          <form className="packages-search-form" onSubmit={handleSearchSubmit}>
            <FiSearch className="packages-search-icon" />
            <input
              type="text"
              className="packages-search-input"
              placeholder="Search packages..."
              value={searchInput}
              onChange={handleSearchChange}
            />
          </form>

          <div className="packages-filter-selects">
            <div className="packages-select-wrapper">
              <FiFilter className="packages-select-icon" />
              <select
                className="packages-select"
                value={category}
                onChange={handleCategoryChange}
              >
                {CATEGORIES.map((cat) => (
                  <option key={cat.value} value={cat.value}>
                    {cat.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="packages-select-wrapper">
              <select
                className="packages-select"
                value={sort}
                onChange={handleSortChange}
              >
                {SORT_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {hasActiveFilters && (
            <button className="packages-clear-filters" onClick={clearFilters}>
              Clear Filters
            </button>
          )}
        </div>
      </div>

      {/* Results Count */}
      {!loading && packageList.length > 0 && (
        <div className="packages-results-info">
          <span>
            Showing {(page - 1) * PAGE_SIZE + 1}
            {' - '}
            {Math.min(page * PAGE_SIZE, totalCount)} of {totalCount} packages
          </span>
        </div>
      )}

      {/* Content */}
      <div className="packages-content">
        {loading ? (
          <LoadingSpinner size="large" message="Loading packages..." />
        ) : packageList.length === 0 ? (
          <EmptyState
            title="No packages found"
            description="We couldn't find any packages matching your criteria. Try adjusting your filters or search terms."
            actionLabel={hasActiveFilters ? 'Clear Filters' : undefined}
            onAction={hasActiveFilters ? clearFilters : undefined}
          />
        ) : (
          <>
            <div className="packages-grid">
              {packageList.map((pkg) => (
                <PackageCard key={pkg.id} pkg={pkg} onSave={handleSavePackage} />
              ))}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="packages-pagination">
                <button
                  className="packages-page-btn packages-page-btn-nav"
                  onClick={() => goToPage(page - 1)}
                  disabled={!prevPage && page <= 1}
                  aria-label="Previous page"
                >
                  <FiChevronLeft />
                  <span>Previous</span>
                </button>

                <div className="packages-page-numbers">
                  {generatePageNumbers(page, totalPages).map((p, idx) =>
                    p === '...' ? (
                      <span key={`dots-${idx}`} className="packages-page-dots">
                        ...
                      </span>
                    ) : (
                      <button
                        key={p}
                        className={`packages-page-btn packages-page-btn-num ${
                          p === page ? 'active' : ''
                        }`}
                        onClick={() => goToPage(p)}
                      >
                        {p}
                      </button>
                    )
                  )}
                </div>

                <button
                  className="packages-page-btn packages-page-btn-nav"
                  onClick={() => goToPage(page + 1)}
                  disabled={!nextPage && page >= totalPages}
                  aria-label="Next page"
                >
                  <span>Next</span>
                  <FiChevronRight />
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

/**
 * Generate an array of page numbers with ellipsis for pagination display.
 */
function generatePageNumbers(current, total) {
  if (total <= 7) {
    return Array.from({ length: total }, (_, i) => i + 1);
  }

  const pages = [];

  // Always show first page
  pages.push(1);

  if (current > 3) {
    pages.push('...');
  }

  // Pages around current
  const start = Math.max(2, current - 1);
  const end = Math.min(total - 1, current + 1);

  for (let i = start; i <= end; i++) {
    pages.push(i);
  }

  if (current < total - 2) {
    pages.push('...');
  }

  // Always show last page
  if (total > 1) {
    pages.push(total);
  }

  return pages;
}
