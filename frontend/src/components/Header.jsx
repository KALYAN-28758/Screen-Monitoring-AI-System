import { useEffect, useState } from 'react';
import { FaHeartbeat } from 'react-icons/fa';
import api from '../api/api';

function Header({ view, onViewChange }) {
  const [monitorStatus, setMonitorStatus] = useState({
    is_running: false,
    screenshots_taken: 0,
    alerts_triggered: 0,
  });

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await api.get('/api/monitor/status');
        setMonitorStatus(response.data);
      } catch (error) {
        console.error('Unable to fetch monitor status:', error);
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="app-header">
      <div className="header-content">
        <div className="header-left">
          <div className="logo">
            <FaHeartbeat className="logo-icon" />
          </div>
          <div className="header-text">
            <h1>Activity Monitor</h1>
            <p>Real-time system activity tracking &amp; alerts</p>
          </div>
        </div>
        <div className="header-right">
          <div className="header-status">
            <span className={`status-badge ${monitorStatus.is_running ? 'online' : 'offline'}`}>
              <span className="status-dot" />
              {monitorStatus.is_running ? 'Monitoring Active' : 'Monitoring Stopped'}
            </span>
            <div className="status-summary">
              <span>{monitorStatus.screenshots_taken} screenshots</span>
              <span>{monitorStatus.alerts_triggered} alerts</span>
            </div>
          </div>
          {view === 'setup' ? (
            <button className="header-proceed-btn" onClick={() => onViewChange('monitor')}>
              Proceed to Monitoring
              <span className="btn-arrow">→</span>
            </button>
          ) : (
            <button className="header-back-btn" onClick={() => onViewChange('setup')}>
              <span className="btn-arrow">←</span>
              Back to Setup
            </button>
          )}
        </div>
      </div>
    </header>
  );
}

export default Header;
