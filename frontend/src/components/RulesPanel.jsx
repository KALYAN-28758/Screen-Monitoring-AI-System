import { useState, useEffect } from 'react';
import { FaPlus, FaTrash, FaListUl, FaToggleOn, FaToggleOff, FaSpinner, FaRocket, FaArrowRight } from 'react-icons/fa';
import api from '../api/api';

export default function RulesPanel({ onProceed }) {
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState('');
  const [prompt, setPrompt] = useState('');
  const [message, setMessage] = useState(null);
  const [intervalVal, setIntervalVal] = useState(60);
  const [savingInterval, setSavingInterval] = useState(false);

  const fetchRules = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/rules/');
      setRules(response.data || []);
    } catch (error) {
      console.error('Error fetching rules:', error);
      showTemporaryMessage('Failed to fetch rules. Please check backend connection.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const showTemporaryMessage = (text, type = 'info') => {
    setMessage({ text, type });
    setTimeout(() => setMessage(null), 5000);
  };

  useEffect(() => {
    fetchRules();
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await api.get('/api/monitor/settings');
      if (response.data && response.data.screenshot_interval_seconds) {
        setIntervalVal(response.data.screenshot_interval_seconds);
      }
    } catch (error) {
      console.error('Error fetching settings:', error);
    }
  };

  const handleUpdateInterval = async (e) => {
    e.preventDefault();
    try {
      setSavingInterval(true);
      await api.post('/api/monitor/settings', {
        screenshot_interval_seconds: parseInt(intervalVal, 10)
      });
      showTemporaryMessage('Screenshot interval updated successfully!', 'success');
    } catch (error) {
      console.error('Error updating interval:', error);
      showTemporaryMessage('Failed to update interval.', 'error');
    } finally {
      setSavingInterval(false);
    }
  };

  const handleCreateRule = async (e) => {
    e.preventDefault();
    if (!name.trim() || !prompt.trim()) return;

    try {
      setCreating(true);
      const response = await api.post('/api/rules/', {
        name: name.trim(),
        prompt: prompt.trim(),
        is_active: true
      });
      setRules([response.data, ...rules]);
      setName('');
      setPrompt('');
      showTemporaryMessage('Instruction rule added successfully!', 'success');
    } catch (error) {
      console.error('Error creating rule:', error);
      showTemporaryMessage('Failed to create rule.', 'error');
    } finally {
      setCreating(false);
    }
  };

  const handleToggleRule = async (rule) => {
    try {
      const updatedRule = { ...rule, is_active: !rule.is_active };
      const response = await api.put(`/api/rules/${rule.id}`, {
        is_active: updatedRule.is_active
      });
      
      setRules(rules.map(r => r.id === rule.id ? response.data : r));
      showTemporaryMessage(
        `Rule "${rule.name}" is now ${response.data.is_active ? 'active' : 'inactive'}.`,
        'success'
      );
    } catch (error) {
      console.error('Error toggling rule:', error);
      showTemporaryMessage('Failed to update rule status.', 'error');
    }
  };

  const handleDeleteRule = async (ruleId) => {
    try {
      await api.delete(`/api/rules/${ruleId}`);
      setRules(rules.filter(r => r.id !== ruleId));
      showTemporaryMessage('Rule deleted successfully.', 'success');
    } catch (error) {
      console.error('Error deleting rule:', error);
      showTemporaryMessage('Failed to delete rule.', 'error');
    }
  };

  return (
    <div className="rules-panel-container">
      <div className="rules-header">
        <h2>
          <FaListUl className="panel-icon" />
          Monitoring Instructions & Rules
        </h2>
      </div>

      {message && (
        <div className={`status-banner ${message.type}`}>
          {message.text}
        </div>
      )}

      <div className="rules-content-layout">
        {/* Form column */}
        <div className="forms-column">
          <form onSubmit={handleCreateRule} className="rule-form">
          <h3>Add Monitoring Instruction</h3>
          <p className="form-help-text">
            Tell the AI what to look for and when to alert you. Be specific! <br/>
            <strong>Examples:</strong> "Alert me if the YouTube video is paused or completed", "Notify me when the user switches browser tabs", "Tell me if a new message arrives in WhatsApp"
          </p>
          <div className="form-group">
            <label htmlFor="rule-name">Instruction/Rule Name</label>
            <input
              id="rule-name"
              type="text"
              placeholder="e.g., Video Watchdog"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="rule-prompt">AI Prompt / Instruction</label>
            <textarea
              id="rule-prompt"
              rows="3"
              placeholder="e.g., Alert me if the YouTube video stops, pauses, or completes. The alert message should say exactly what happened."
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              required
            />
          </div>
          <button type="submit" className="add-rule-btn" disabled={creating}>
            {creating ? <FaSpinner className="spin-icon" /> : <FaPlus />}
            {creating ? 'Adding...' : 'Add Instruction'}
          </button>
        </form>

        <hr className="settings-divider" />

        <form onSubmit={handleUpdateInterval} className="rule-form">
          <h3>Monitoring Settings</h3>
          <p className="form-help-text">
            Set how often the AI takes a screenshot to analyze your activity.
          </p>
          <div className="form-group">
            <label htmlFor="screenshot-interval">Screenshot Interval (Seconds)</label>
            <input
              id="screenshot-interval"
              type="number"
              min="10"
              max="3600"
              value={intervalVal}
              onChange={(e) => setIntervalVal(e.target.value)}
              required
            />
          </div>
          <button type="submit" className="add-rule-btn" disabled={savingInterval}>
            {savingInterval ? <FaSpinner className="spin-icon" /> : null}
            {savingInterval ? ' Saving...' : 'Save Settings'}
          </button>
        </form>
        </div>

        {/* List column */}
        <div className="rules-list-section">
          <h3>Active Guidelines</h3>
          {loading ? (
            <div className="loading-state-rules">
              <FaSpinner className="spin-icon large" />
              <p>Loading rules...</p>
            </div>
          ) : rules.length > 0 ? (
            <div className="rules-list">
              {rules.map((rule) => (
                <div key={rule.id} className={`rule-item-card ${rule.is_active ? 'active' : 'inactive'}`}>
                  <div className="rule-info">
                    <h4>{rule.name}</h4>
                    <p className="rule-prompt-text">{rule.prompt}</p>
                  </div>
                  <div className="rule-actions">
                    <button
                      type="button"
                      className="toggle-action-btn"
                      onClick={() => handleToggleRule(rule)}
                      title={rule.is_active ? 'Deactivate instruction' : 'Activate instruction'}
                    >
                      {rule.is_active ? (
                        <FaToggleOn className="toggle-icon active" />
                      ) : (
                        <FaToggleOff className="toggle-icon inactive" />
                      )}
                    </button>
                    <button
                      type="button"
                      className="delete-action-btn"
                      onClick={() => handleDeleteRule(rule.id)}
                      title="Delete instruction"
                    >
                      <FaTrash className="delete-icon" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-rules">
              <p>No custom instructions active.</p>
              <p className="secondary-text">Add one on the left to start customized AI monitoring (e.g. tracking video playing state or browser tab changes).</p>
            </div>
          )}
        </div>
      </div>

      {/* Prominent Proceed to Monitoring CTA */}
      {onProceed && (
        <div className="proceed-cta-section">
          <div className="proceed-cta-inner">
            <div className="proceed-cta-text">
              <FaRocket className="proceed-cta-icon" />
              <div>
                <h3>Ready to Start Monitoring?</h3>
                <p>Your rules are set. Start capturing and get real-time alerts on your screen.</p>
              </div>
            </div>
            <button className="proceed-cta-btn" onClick={onProceed} id="proceed-to-monitoring-btn">
              <span>Proceed to Monitoring</span>
              <FaArrowRight className="proceed-cta-arrow" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
