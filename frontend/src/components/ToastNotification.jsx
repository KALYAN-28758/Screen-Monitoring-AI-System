import { useState, useEffect, useCallback } from 'react';
import { FaExclamationTriangle, FaBell, FaInfoCircle, FaTimes, FaSlidersH } from 'react-icons/fa';

let addToastExternal = null;

export function triggerToast(toast) {
  if (addToastExternal) {
    addToastExternal(toast);
  }
}

export default function ToastNotification() {
  const [toasts, setToasts] = useState([]);

  const addToast = useCallback((toast) => {
    const id = Date.now() + Math.random();
    setToasts(prev => [...prev, { ...toast, id }]);

    // Auto-dismiss after 8 seconds
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 8000);
  }, []);

  useEffect(() => {
    addToastExternal = addToast;
    return () => { addToastExternal = null; };
  }, [addToast]);

  const removeToast = (id) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  };

  const getIcon = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical':
      case 'warning':
        return <FaExclamationTriangle />;
      case 'system':
      case 'activity':
        return <FaSlidersH />;
      default:
        return <FaInfoCircle />;
    }
  };

  if (toasts.length === 0) return null;

  return (
    <div className="toast-container">
      {toasts.map((toast) => {
        const severity = toast.severity?.toLowerCase() || 'info';
        return (
          <div key={toast.id} className={`toast-item ${severity}`}>
            <div className="toast-icon-wrapper">
              <FaBell className="toast-bell-icon" />
              {getIcon(toast.severity)}
            </div>
            <div className="toast-body">
              <div className="toast-title">{toast.title || 'Alert'}</div>
              <div className="toast-message">{toast.message}</div>
            </div>
            <button className="toast-close" onClick={() => removeToast(toast.id)}>
              <FaTimes />
            </button>
          </div>
        );
      })}
    </div>
  );
}
