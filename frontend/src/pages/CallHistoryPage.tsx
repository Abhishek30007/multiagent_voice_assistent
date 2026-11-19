import React, { useEffect, useState } from 'react';
import { Phone } from 'lucide-react';
import { api } from '../services/api';
import { CallLog } from '../types';

export const CallHistoryPage: React.FC = () => {
  const [calls, setCalls] = useState<CallLog[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getCallHistory().then((res) => {
      setCalls(res.items);
      setLoading(false);
    });
  }, []);

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 700 }}>Telephone Call History</h2>
        <p style={{ color: 'var(--text-muted)' }}>Audit logs of incoming telephone calls handled by the AI twin</p>
      </div>

      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <table>
          <thead>
            <tr>
              <th>Caller Phone</th>
              <th>Status</th>
              <th>Duration</th>
              <th>Turns</th>
              <th>Agent Execution Summary & Sources</th>
              <th>Date / Time</th>
            </tr>
          </thead>
          <tbody>
            {calls.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                  {loading ? 'Loading call history...' : 'No calls recorded yet. Use the "Test Voice Call" button to simulate a call!'}
                </td>
              </tr>
            ) : (
              calls.map((c) => (
                <tr key={c.id}>
                  <td style={{ fontWeight: 600 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Phone size={14} color="var(--primary)" />
                      {c.caller_number}
                    </div>
                  </td>
                  <td>
                    <span className={`status-badge ${c.call_status === 'completed' ? 'online' : 'offline'}`}>
                      {c.call_status}
                    </span>
                  </td>
                  <td>{c.duration_seconds}s</td>
                  <td>{c.turn_count}</td>
                  <td>
                    <div style={{ fontSize: '0.85rem' }}>{c.agent_execution_summary}</div>
                    {c.evidence_sources && c.evidence_sources.length > 0 && (
                      <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap', marginTop: '6px' }}>
                        {c.evidence_sources.map((s, idx) => (
                          <span key={idx} style={{ 
                            padding: '2px 6px', 
                            borderRadius: '4px', 
                            background: '#eff6ff', 
                            fontSize: '0.7rem',
                            color: 'var(--primary)',
                          }}>
                            {s.type}: {s.title}
                          </span>
                        ))}
                      </div>
                    )}
                  </td>
                  <td style={{ fontSize: '0.85rem', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                    {new Date(c.call_start_time).toLocaleString()}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
