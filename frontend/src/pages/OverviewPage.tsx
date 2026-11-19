import React, { useEffect, useState } from 'react';
import { Mail, Calendar, PhoneCall, CheckCircle, RefreshCw } from 'lucide-react';
import { api } from '../services/api';
import { AuthStatus, SyncStatus } from '../types';

export const OverviewPage: React.FC = () => {
  const [auth, setAuth] = useState<AuthStatus | null>(null);
  const [sync, setSync] = useState<SyncStatus | null>(null);
  const [emailCount, setEmailCount] = useState<number>(0);
  const [eventCount, setEventCount] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);

  const loadData = async () => {
    setLoading(true);
    try {
      const [authData, syncData, emails, events] = await Promise.all([
        api.getAuthStatus(),
        api.getSyncStatus(),
        api.getEmails(1),
        api.getCalendarEvents(),
      ]);
      setAuth(authData);
      setSync(syncData);
      setEmailCount(emails.total);
      setEventCount(events.total);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 700 }}>Personal AI Twin Status</h2>
          <p style={{ color: 'var(--text-muted)' }}>Real-time voice representative for Abhishek</p>
        </div>
        <button className="btn btn-secondary" onClick={loadData}>
          <RefreshCw size={16} /> Refresh
        </button>
      </div>

      <div className="grid-3">
        <div className="card">
          <div className="card-title">Gmail Connection</div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="card-value">{emailCount}</span>
            <span className={`status-badge ${auth?.gmail_connected ? 'online' : 'offline'}`}>
              {auth?.gmail_connected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
          <p style={{ marginTop: '12px', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Imported personal emails
          </p>
        </div>

        <div className="card">
          <div className="card-title">Google Calendar</div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="card-value">{eventCount}</span>
            <span className={`status-badge ${auth?.calendar_connected ? 'online' : 'offline'}`}>
              {auth?.calendar_connected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
          <p style={{ marginTop: '12px', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Scheduled events & assessments
          </p>
        </div>

        <div className="card">
          <div className="card-title">Voice Representative</div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="card-value" style={{ color: '#10b981' }}>Live</span>
            <span className="status-badge online">LiveKit SIP Ready</span>
          </div>
          <p style={{ marginTop: '12px', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Deepgram STT & Gemini API Reasoning
          </p>
        </div>
      </div>

      <div className="card">
        <h3 style={{ fontSize: '1.1rem', marginBottom: '16px' }}>Personal Knowledge Grounding</h3>
        <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginBottom: '16px' }}>
          The AI telephone assistant only references verified records from Abhishek's primary Google Calendar and connected Gmail. It never hallucinates personal commitments.
        </p>

        <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
          <div style={{ padding: '16px', background: '#f8fafc', borderRadius: '8px', flex: 1, minWidth: '220px' }}>
            <strong>Account Owner:</strong>
            <p>{auth?.owner_name || 'Abhishek'}</p>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>{auth?.owner_email}</p>
          </div>
          <div style={{ padding: '16px', background: '#f8fafc', borderRadius: '8px', flex: 1, minWidth: '220px' }}>
            <strong>Auto-Sync Interval:</strong>
            <p>Every 15 minutes</p>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Celery Beat Scheduler Active</p>
          </div>
          <div style={{ padding: '16px', background: '#f8fafc', borderRadius: '8px', flex: 1, minWidth: '220px' }}>
            <strong>Disclosure Policy:</strong>
            <p>Read-Only Personal Grounding</p>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Write actions & sensitive data blocked</p>
          </div>
        </div>
      </div>
    </div>
  );
};
