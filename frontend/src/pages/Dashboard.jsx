import { useState } from 'react';
import ScreenshotPanel from '../components/ScreenshotPanel';
import AlertPanel from '../components/AlertPanel';
import RulesPanel from '../components/RulesPanel';
import Header from '../components/Header';
import ToastNotification from '../components/ToastNotification';
import '../styles/dashboard.css';

export default function Dashboard() {
  const [view, setView] = useState('setup'); // 'setup' or 'monitor'

  return (
    <div className="dashboard">
      <Header view={view} onViewChange={setView} />
      <ToastNotification />
      <div className="dashboard-content">
        {view === 'setup' ? (
          <div className="dashboard-main-area setup-view">
            <RulesPanel onProceed={() => setView('monitor')} />
          </div>
        ) : (
          <>
            <div className="dashboard-main-area monitor-view">
              <ScreenshotPanel />
            </div>
            <AlertPanel />
          </>
        )}
      </div>
    </div>
  );
}