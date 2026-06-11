import { useState, useEffect, useRef } from 'react';
import { FaExclamationTriangle, FaCheckCircle, FaInfoCircle, FaSlidersH } from 'react-icons/fa';
import { triggerToast } from './ToastNotification';
import api from '../api/api';

export default function AlertPanel() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const seenAlertIdsRef = useRef(new Set());
  const isFirstFetchRef = useRef(true);

  const formatTime = (timestamp) => {
    if (!timestamp) return 'N/A';
    // Backend stores UTC times; ensure JS parses as UTC by appending 'Z' if no timezone info
    let ts = String(timestamp);
    if (!ts.endsWith('Z') && !ts.includes('+') && !ts.includes('T')) {
      ts = ts.replace(' ', 'T') + 'Z';
    } else if (!ts.endsWith('Z') && !ts.includes('+')) {
      ts = ts + 'Z';
    }
    const date = new Date(ts);
    return date.toLocaleTimeString('en-IN', { 
      timeZone: 'Asia/Kolkata',
      hour: '2-digit', 
      minute: '2-digit',
      second: '2-digit',
      hour12: true
    }) + ' IST';
  };

  const getSeverityIcon = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical':
      case 'warning':
        return <FaExclamationTriangle className="severity-icon" />;
      case 'system':
      case 'activity':
        return <FaSlidersH className="severity-icon" />;
      default:
        return <FaInfoCircle className="severity-icon" />;
    }
  };

  const fetchAlerts = async (isInitial = false) => {
    try {
      if (isInitial) setLoading(true);
      const response = await api.get('/api/alerts');
      const fetchedAlerts = Array.isArray(response.data) ? response.data : response.data.alerts || [];
      
      // Detect NEW alerts and trigger toast notifications for them
      if (!isFirstFetchRef.current) {
        fetchedAlerts.forEach(alert => {
          const alertId = alert.id || alert.triggered_at;
          if (!seenAlertIdsRef.current.has(alertId)) {
            // This is a brand new alert — show toast!
            triggerToast({
              title: alert.title,
              message: alert.message,
              severity: alert.severity,
            });
          }
        });
      }

      // Update the set of seen alert IDs
      seenAlertIdsRef.current = new Set(fetchedAlerts.map(a => a.id || a.triggered_at));
      isFirstFetchRef.current = false;

      setAlerts(fetchedAlerts);
    } catch (error) {
      console.error('Error fetching alerts:', error);
    } finally {
      if (isInitial) setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts(true);
    const interval = setInterval(() => fetchAlerts(false), 5000);
    return () => clearInterval(interval);
  }, []);

  const filteredAlerts = alerts.filter(alert => {
    if (filter === 'all') return true;
    if (filter === 'system') {
      return alert.severity?.toLowerCase() === 'system' || alert.severity?.toLowerCase() === 'activity';
    }
    return alert.severity?.toLowerCase() === filter;
  });

  const severityCounts = {
    critical: alerts.filter(a => a.severity?.toLowerCase() === 'critical').length,
    warning: alerts.filter(a => a.severity?.toLowerCase() === 'warning').length,
    system: alerts.filter(a => a.severity?.toLowerCase() === 'system' || a.severity?.toLowerCase() === 'activity').length,
    info: alerts.filter(a => a.severity?.toLowerCase() === 'info').length,
  };

  return (
    <div className="right-panel">
      <div className="alert-container">
        <div className="alert-header">
          <h2>
            <FaExclamationTriangle className="panel-icon" />
            Alerts
            <span className="alert-count">{alerts.length}</span>
          </h2>
        </div>

        <div className="alert-stats">
          <div className="stat-box critical" onClick={() => setFilter('critical')}>
            <span className="stat-number">{severityCounts.critical}</span>
            <span className="stat-label">Critical</span>
          </div>
          <div className="stat-box warning" onClick={() => setFilter('warning')}>
            <span className="stat-number">{severityCounts.warning}</span>
            <span className="stat-label">Warning</span>
          </div>
          <div className="stat-box system" onClick={() => setFilter('system')}>
            <span className="stat-number">{severityCounts.system}</span>
            <span className="stat-label">System</span>
          </div>
          <div className="stat-box info" onClick={() => setFilter('info')}>
            <span className="stat-number">{severityCounts.info}</span>
            <span className="stat-label">Info</span>
          </div>
          {filter !== 'all' && (
            <button className="filter-btn" onClick={() => setFilter('all')}>Clear Filter</button>
          )}
        </div>

        {loading && (
          <div className="loading-state-alerts">
            <div className="spinner-small"></div>
            <p>Loading alerts...</p>
          </div>
        )}

        <div className="alert-list">
          {filteredAlerts && filteredAlerts.length > 0 ? (
            filteredAlerts.map((alert) => {
              const severity = alert.severity?.toLowerCase() || 'default';
              return (
                <div key={alert.id || alert.triggered_at} className={`alert-card ${severity}`}>
                  <div className="alert-content">
                    <div className="alert-icon-section">
                      {getSeverityIcon(alert.severity)}
                    </div>
                    <div className="alert-body">
                      <h4 className="alert-title">{alert.title}</h4>
                      <p className="alert-description">{alert.message}</p>
                      <div className="alert-footer">
                        <span className="alert-time">{formatTime(alert.triggered_at)}</span>
                      </div>
                    </div>
                    <span className={`alert-badge ${severity}`}>{alert.severity || 'info'}</span>
                  </div>
                </div>
              );
            })
          ) : (
            <div className="no-alerts">
              <FaCheckCircle className="no-alerts-icon" />
              <p>No alerts {filter !== 'all' ? `with severity "${filter}"` : 'available'}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}