import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { MetricsSummary } from '../types';

export const AgentMonitorPage: React.FC = () => {
  const [metrics, setMetrics] = useState<MetricsSummary | null>(null);

  useEffect(() => {
    api.getMetrics().then(setMetrics).catch(console.error);
  }, []);

  const agents = [
    { name: 'Supervisor Agent', desc: 'Intent classification & prompt injection filter', status: 'Healthy', latency: '35ms' },
    { name: 'Gmail Retrieval Agent', desc: 'Keyword & semantic search over personal email store', status: 'Healthy', latency: '48ms' },
    { name: 'Calendar Agent', desc: 'Schedule conflict & free/busy interval resolver', status: 'Healthy', latency: '22ms' },
    { name: 'Evidence Validation Agent', desc: 'Anti-hallucination factual cross-verification', status: 'Healthy', latency: '18ms' },
    { name: 'Safety & Policy Agent', desc: 'Privacy disclosure rules & write-action blocker', status: 'Healthy', latency: '12ms' },
    { name: 'Response Generation Agent', desc: 'Spoken-friendly persona response formulator', status: 'Healthy', latency: '85ms' },
  ];

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 700 }}>Agent Execution Monitor</h2>
        <p style={{ color: 'var(--text-muted)' }}>Real-time OpenTelemetry tracking and multi-agent pipeline performance</p>
      </div>

      <div className="grid-3">
        <div className="card">
          <div className="card-title">Token Consumption</div>
          <div className="card-value">{metrics?.tokens_consumed || 0}</div>
          <p style={{ marginTop: '8px', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Est. Cost: ${metrics?.estimated_cost_usd?.toFixed(4) || '0.0000'}
          </p>
        </div>

        <div className="card">
          <div className="card-title">Failed Call Rate</div>
          <div className="card-value" style={{ color: (metrics?.failed_call_rate_pct || 0) > 0 ? '#ef4444' : '#10b981' }}>
            {metrics?.failed_call_rate_pct || 0}%
          </div>
          <p style={{ marginTop: '8px', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Target &lt; 1.0%
          </p>
        </div>

        <div className="card">
          <div className="card-title">Unsupported Query Rate</div>
          <div className="card-value">{metrics?.unsupported_response_rate_pct || 0}%</div>
          <p style={{ marginTop: '8px', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Grounded abstention rate
          </p>
        </div>
      </div>

      <div className="card" style={{ marginBottom: '24px' }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '16px' }}>LangGraph Agents Status</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
          {agents.map((ag) => (
            <div key={ag.name} style={{ padding: '16px', background: '#f8fafc', borderRadius: '8px', border: '1px solid var(--border)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                <span style={{ fontWeight: 600 }}>{ag.name}</span>
                <span className="status-badge online">Active</span>
              </div>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '8px' }}>{ag.desc}</p>
              <div style={{ fontSize: '0.75rem', color: 'var(--primary)', fontWeight: 600 }}>
                Avg Latency: {ag.latency}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
