import { format, parseISO, formatDistanceToNow } from 'date-fns';

export function formatCurrency(amount, currency = 'USD') {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
  }).format(amount || 0);
}

export function formatDate(dateStr) {
  if (!dateStr) return '';
  try {
    return format(parseISO(dateStr), 'MMM dd, yyyy');
  } catch {
    return dateStr;
  }
}

export function formatDateTime(dateStr) {
  if (!dateStr) return '';
  try {
    return format(parseISO(dateStr), 'MMM dd, yyyy h:mm a');
  } catch {
    return dateStr;
  }
}

export function timeAgo(dateStr) {
  if (!dateStr) return '';
  try {
    return formatDistanceToNow(parseISO(dateStr), { addSuffix: true });
  } catch {
    return dateStr;
  }
}

export function truncate(str, len = 100) {
  if (!str) return '';
  return str.length > len ? str.slice(0, len) + '...' : str;
}

export function getImageUrl(path) {
  if (!path) return '/placeholder.svg';
  if (path.startsWith('http')) return path;
  const base = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  return `${base}${path}`;
}

export function getStatusColor(status) {
  const map = {
    pending: '#f59e0b',
    confirmed: '#10b981',
    invoiced: '#3b82f6',
    paid: '#10b981',
    cancelled: '#ef4444',
    completed: '#10b981',
    open: '#3b82f6',
    in_progress: '#f59e0b',
    resolved: '#10b981',
    closed: '#6b7280',
    draft: '#6b7280',
    published: '#10b981',
    archived: '#f59e0b',
  };
  return map[status?.toLowerCase()] || '#6b7280';
}

export function sanitizeInput(input) {
  if (typeof input !== 'string') return input;
  return input.replace(/[<>]/g, '');
}
