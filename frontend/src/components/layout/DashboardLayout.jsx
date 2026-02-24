import { NavLink, Outlet, Navigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
  FiUser, FiCalendar, FiCreditCard, FiHeart,
  FiBell, FiHelpCircle, FiSettings
} from 'react-icons/fi';
import './DashboardLayout.css';

export default function DashboardLayout() {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) return <Navigate to="/login" replace />;

  const sideLinks = [
    { to: '/dashboard', label: 'Profile', icon: FiUser, end: true },
    { to: '/dashboard/bookings', label: 'Bookings', icon: FiCalendar },
    { to: '/dashboard/wallet', label: 'Wallet', icon: FiCreditCard },
    { to: '/dashboard/saved', label: 'Saved', icon: FiHeart },
    { to: '/dashboard/notifications', label: 'Notifications', icon: FiBell },
    { to: '/dashboard/support', label: 'Support', icon: FiHelpCircle },
    { to: '/dashboard/settings', label: 'Settings', icon: FiSettings },
  ];

  return (
    <div className="dashboard-layout">
      <aside className="dashboard-sidebar">
        <h3 className="sidebar-title">Dashboard</h3>
        <nav className="sidebar-nav">
          {sideLinks.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
            >
              <Icon /> {label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <div className="dashboard-content">
        <Outlet />
      </div>
    </div>
  );
}
