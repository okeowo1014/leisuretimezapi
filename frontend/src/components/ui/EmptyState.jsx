import { FiInbox } from 'react-icons/fi';
import './EmptyState.css';

export default function EmptyState({
  icon: Icon = FiInbox,
  title = 'Nothing here yet',
  description = '',
  actionLabel,
  onAction,
  actionLink,
}) {
  return (
    <div className="empty-state">
      <div className="empty-state-icon-wrapper">
        <Icon className="empty-state-icon" />
      </div>

      <h3 className="empty-state-title">{title}</h3>

      {description && (
        <p className="empty-state-description">{description}</p>
      )}

      {actionLabel && (onAction || actionLink) && (
        actionLink ? (
          <a href={actionLink} className="empty-state-action">
            {actionLabel}
          </a>
        ) : (
          <button className="empty-state-action" onClick={onAction}>
            {actionLabel}
          </button>
        )
      )}
    </div>
  );
}
