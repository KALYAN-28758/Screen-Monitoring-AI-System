import { useState, useEffect, useRef } from 'react';
import { FaClock, FaDesktop, FaExclamationCircle, FaPlay, FaStop, FaVideo } from 'react-icons/fa';
import api from '../api/api';

export default function ScreenshotPanel() {
  const [screenshot, setScreenshot] = useState(null);
  const [initialLoading, setInitialLoading] = useState(true);
  const [error, setError] = useState(null);
  const [metadata, setMetadata] = useState(null);
  const [monitorStatus, setMonitorStatus] = useState({ is_running: false });
  const [isCapturing, setIsCapturing] = useState(false);
  const [captureIntervalMs, setCaptureIntervalMs] = useState(15000);

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const intervalRef = useRef(null);

  const fetchMonitorStatus = async () => {
    try {
      const statusResponse = await api.get('/api/monitor/status');
      setMonitorStatus(statusResponse.data);
    } catch (error) {
      console.error('Error fetching monitor status:', error);
    }
  };

  const fetchSettings = async () => {
    try {
      const response = await api.get('/api/monitor/settings');
      if (response.data && response.data.screenshot_interval_seconds) {
        setCaptureIntervalMs(response.data.screenshot_interval_seconds * 1000);
      }
    } catch (error) {
      console.error('Error fetching settings:', error);
    }
  };

  const fetchScreenshot = async () => {
    try {
      setError(null);
      const response = await api.get('/api/screenshots/latest');
      
      if (response.data && response.data.image_url) {
        let imageUrl = response.data.image_url;
        if (!imageUrl.startsWith('http')) {
          const base = import.meta.env.VITE_API_URL || ``;
          imageUrl = `${base}${imageUrl}`;
        }
        // Add cache-busting param so browser always fetches latest image
        imageUrl = `${imageUrl}?t=${Date.now()}`;
        setScreenshot(imageUrl);
        setMetadata({
          app: response.data.active_app,
          windowTitle: response.data.active_window,
          allWindows: response.data.all_windows || [],
          detectedApps: response.data.detected_apps || [],
          summary: response.data.summary,
          description: response.data.description,
          changeScore: response.data.change_score,
          timestamp: response.data.captured_at,
          id: response.data.screenshot_id
        });
      }
    } catch (error) {
      console.error('Error fetching screenshot:', error);
    } finally {
      setInitialLoading(false);
    }
  };

  useEffect(() => {
    fetchSettings();
    fetchMonitorStatus();
    fetchScreenshot();

    const interval = setInterval(() => {
      fetchMonitorStatus();
      fetchScreenshot();
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const sendFrame = () => {
    if (!videoRef.current || !canvasRef.current) return;
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (video.videoWidth === 0 || video.videoHeight === 0) return;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    canvas.toBlob(blob => {
      if (!blob) return;
      const formData = new FormData();
      formData.append('file', blob, 'screenshot.jpg');
      formData.append('width', canvas.width);
      formData.append('height', canvas.height);
      
      // We can try to extract window title if it's a window, but getDisplayMedia doesn't give us window title easily.
      // We'll just pass generic labels for now.
      const track = streamRef.current?.getVideoTracks()[0];
      const label = track ? track.label : "Browser Capture";
      
      formData.append('active_window', label);
      formData.append('active_app', "Browser Captured Source");

      api.post('/api/screenshots/upload', formData).then(res => {
        console.log('Frame uploaded successfully', res.data);
      }).catch(err => {
        console.error('Frame upload failed', err);
      });
    }, 'image/jpeg', 0.8);
  };

  const startCapture = async () => {
    try {
      const stream = await navigator.mediaDevices.getDisplayMedia({ 
        video: { displaySurface: "window" } 
      });
      streamRef.current = stream;
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.onloadedmetadata = () => {
          videoRef.current.play().catch(console.error);
        };
      }

      setIsCapturing(true);
      api.post('/api/monitor/control', { action: 'start' }); // Just update backend state

      // Take first frame immediately
      setTimeout(sendFrame, 1000); 

      intervalRef.current = setInterval(sendFrame, captureIntervalMs);

      // Handle user stopping via browser UI
      stream.getVideoTracks()[0].addEventListener('ended', () => {
        stopCapture();
      });

    } catch (err) {
      console.error("Error starting capture: ", err);
      setError("Failed to start capturing: " + err.message);
    }
  };

  const stopCapture = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setIsCapturing(false);
    api.post('/api/monitor/control', { action: 'stop' });
  };

  const formatTime = (timestamp) => {
    if (!timestamp) return 'N/A';
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

  return (
    <div className="left-panel">
      <div className="screenshot-container">
        <div className="screenshot-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 style={{ margin: 0, display: 'flex', alignItems: 'center' }}>
            <FaVideo className="panel-icon" />
            Active Monitoring
          </h2>
          <div className="monitoring-controls">
            {!isCapturing ? (
              <button className="primary-action-btn start-btn" onClick={startCapture} style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 16px', background: '#22c55e', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 600 }}>
                <FaPlay /> Start Capturing
              </button>
            ) : (
              <button className="primary-action-btn stop-btn" onClick={stopCapture} style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 16px', background: '#ef4444', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 600 }}>
                <FaStop /> Stop Capturing
              </button>
            )}
          </div>
        </div>

        {/* Hidden elements for capture. Avoid display:none to ensure browser renders frames */}
        <video ref={videoRef} autoPlay playsInline muted style={{ position: 'absolute', width: '1px', height: '1px', opacity: 0, pointerEvents: 'none' }} />
        <canvas ref={canvasRef} style={{ display: 'none' }} />

        {initialLoading && !screenshot && (
          <div className="loading-state">
            <div className="spinner"></div>
            <p>Loading activity state...</p>
          </div>
        )}

        {error && (
          <div className="error-state" style={{ marginTop: '16px' }}>
            <FaExclamationCircle className="error-icon" />
            <p>{error}</p>
          </div>
        )}

        {screenshot && (
          <div className="screenshot-split-layout" style={{ marginTop: '16px' }}>
            <div className="activity-details-panel">
              <div className="activity-detail-section status-row">
                <div>
                  <h3>Monitoring Status</h3>
                  <p className="status-note">
                    {isCapturing
                      ? 'Active monitoring is running and capturing screenshots.'
                      : 'Monitoring is currently stopped.'}
                  </p>
                </div>
                <div className={`status-pill ${isCapturing ? 'active' : 'inactive'}`}>
                  {isCapturing ? 'Active' : 'Stopped'}
                </div>
              </div>

              <div className="activity-detail-section">
                <h3>Active Focus</h3>
                <div className="active-focus-card">
                  <div className="active-focus-app">{metadata?.app || 'Unknown App'}</div>
                  <div className="active-focus-title">{metadata?.windowTitle || 'Unknown Window Title'}</div>
                </div>
              </div>

              <div className="activity-detail-section">
                <h3>AI Activity Summary</h3>
                <div className="ai-summary-text" style={{ opacity: metadata?.summary ? 1 : 0.6, fontStyle: metadata?.summary ? 'normal' : 'italic' }}>
                  {metadata?.summary || 'Pending AI analysis...'}
                </div>
              </div>

              {metadata?.changeScore != null && (
                <div className="activity-detail-section">
                  <h3>Visual Change</h3>
                  <div className="change-summary-row">
                    <span className="change-score-label">Change score</span>
                    <span className="change-score-value">{(metadata.changeScore * 100).toFixed(1)}%</span>
                    <span className="change-importance">{metadata.changeScore >= 0.7 ? 'High' : metadata.changeScore >= 0.35 ? 'Medium' : 'Low'}</span>
                  </div>
                  <p className="change-description" style={{ opacity: metadata?.description ? 1 : 0.6, fontStyle: metadata?.description ? 'normal' : 'italic' }}>
                    {metadata?.description || 'Waiting for AI change description...'}
                  </p>
                </div>
              )}

              {metadata?.detectedApps && metadata.detectedApps.length > 0 && (
                <div className="activity-detail-section">
                  <h3>Detected Apps (AI)</h3>
                  <div className="detected-apps-badges">
                    {metadata.detectedApps.map((app, index) => (
                      <span key={index} className="detected-app-badge">{app}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="screenshot-wrapper">
              <img
                src={screenshot}
                alt="Latest Screenshot"
                className="screenshot-image"
                onError={(e) => {
                  console.error('Image failed to load:', e);
                  setError('Failed to load image');
                }}
              />
              {metadata && (
                <div className="screenshot-footer">
                  <div className="meta-item">
                    <FaClock className="meta-icon" />
                    <span>{formatTime(metadata.timestamp)}</span>
                  </div>
                  <div className="meta-item" style={{ fontSize: '11px', color: '#94a3b8' }}>
                    ID: #{metadata.id}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}