import React, { useEffect, useState } from 'react';
import { RefreshCw, Power } from 'lucide-react';
import { api } from '../services/api';
import { AuthStatus } from '../types';

export const SettingsPage: React.FC = () => {
  const [auth, setAuth] = useState<AuthStatus | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    api.getAuthStatus().then(setAuth).catch(console.error);
  }, []);

  const handleSyncNow = async () => {
    setSyncing(true);
    setMessage('Initiating full data ingestion sync...');
    try {
      await api.triggerSync('all');
      setMessage('Background synchronization initiated successfully.');
    } catch (e) {
      setMessage('Sync failed to start.');
    } finally {
      setSyncing(false);
    }
  };

  const handleDisconnect = async () => {
    if (!confirm('Are you sure you want to disconnect your Google account and revoke OAuth tokens?')) return;
    try {
      await api.disconnectGoogle();
      const updated = await api.getAuthStatus();
      setAuth(updated);
      setMessage('Google account disconnected and tokens removed.');
    } catch (e) {
      setMessage('Disconnect failed.');
    }
  };

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 700 }}>Settings & Privacy Controls</h2>
        <p style={{ color: 'var(--text-muted)' }}>Configure Google OAuth, AI telephone number, and disclosure policies</p>
      </div>

      {message && (
        <div style={{ padding: '12px 16px', background: '#eff6ff', borderRadius: '8px', color: 'var(--primary)', marginBottom: '20px' }}>
          {message}
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {/* Google Connection Card */}
        <div className="card">
          <h3 style={{ fontSize: '1.1rem', marginBottom: '8px' }}>Google Account Connection</h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '16px' }}>
            Personal data sources: Read-only access to Gmail and Primary Google Calendar.
          </p>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontWeight: 600 }}>{auth?.owner_email || 'Not connected'}</div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Status: {auth?.is_connected ? 'Connected (Tokens Fernet Encrypted in DB)' : 'Disconnected'}
              </div>
            </div>

            <div style={{ display: 'flex', gap: '12px' }}>
              <button className="btn btn-secondary" onClick={handleSyncNow} disabled={syncing}>
                <RefreshCw size={16} /> Sync Now
              </button>
              {auth?.is_connected && (
                <button className="btn btn-danger" onClick={handleDisconnect}>
                  <Power size={16} /> Disconnect
                </button>
              )}
            </div>
          </div>
        </div>

        {/* AI Telephone & Telephony Config */}
        <div className="card">
          <h3 style={{ fontSize: '1.1rem', marginBottom: '8px' }}>AI Telephone Trunk Configuration</h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '16px' }}>
            SIP trunk provider and telephony endpoint parameters.
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div>
              <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>AI Phone Number</label>
              <input type="text" readOnly value="+1 (555) 019-2834" style={{ width: '100%', padding: '8px 12px', marginTop: '4px', borderRadius: '6px', border: '1px solid var(--border)', background: '#f8fafc' }} />
            </div>
            <div>
              <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>SIP Protocol Engine</label>
              <input type="text" readOnly value="LiveKit Agents SIP Trunking" style={{ width: '100%', padding: '8px 12px', marginTop: '4px', borderRadius: '6px', border: '1px solid var(--border)', background: '#f8fafc' }} />
            </div>
            <div>
              <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>Speech-to-Text Model</label>
              <input type="text" readOnly value="Deepgram Nova-2" style={{ width: '100%', padding: '8px 12px', marginTop: '4px', borderRadius: '6px', border: '1px solid var(--border)', background: '#f8fafc' }} />
            </div>
            <div>
              <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>Text-to-Speech Engine</label>
              <input type="text" readOnly value="Cartesia Sonic / ElevenLabs" style={{ width: '100%', padding: '8px 12px', marginTop: '4px', borderRadius: '6px', border: '1px solid var(--border)', background: '#f8fafc' }} />
            </div>
          </div>
        </div>

        {/* Privacy & Permissions Policy */}
        <div className="card">
          <h3 style={{ fontSize: '1.1rem', marginBottom: '8px' }}>Privacy & Disclosure Guardrails</h3>
          <ul style={{ paddingLeft: '20px', fontSize: '0.9rem', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <li>The AI introduces itself as an assistant and never impersonates Abhishek.</li>
            <li>Caller ID is never treated as strong authentication for confidential data.</li>
            <li>Passcodes, financial statements, and OTPs are blocked from verbal disclosure.</li>
            <li>The AI representative never sends emails or modifies calendar events.</li>
            <li>Call audio is not retained by default; call transcripts are not indexed into personal memory.</li>
          </ul>
        </div>
      </div>
    </div>
  );
};
