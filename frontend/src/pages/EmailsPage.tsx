import React, { useEffect, useState } from 'react';
import { Search, Filter, Mail, Tag } from 'lucide-react';
import { api } from '../services/api';
import { EmailMessage } from '../types';

export const EmailsPage: React.FC = () => {
  const [emails, setEmails] = useState<EmailMessage[]>([]);
  const [category, setCategory] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [total, setTotal] = useState<number>(0);

  const loadEmails = async () => {
    setLoading(true);
    try {
      const data = await api.getEmails(1, category);
      setEmails(data.items);
      setTotal(data.total);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEmails();
  }, [category]);

  const categories = ['', 'Assessment', 'Interview', 'Career', 'Finance', 'Meeting', 'General'];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 700 }}>Imported Emails</h2>
          <p style={{ color: 'var(--text-muted)' }}>{total} personal messages available for grounded answering</p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          {categories.map((c) => (
            <button
              key={c || 'all'}
              className={`btn ${category === c ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setCategory(c)}
            >
              {c || 'All'}
            </button>
          ))}
        </div>
      </div>

      <div className="card" style={{ padding: '0', overflow: 'hidden' }}>
        <table>
          <thead>
            <tr>
              <th>Sender</th>
              <th>Subject & Snippet</th>
              <th>Category</th>
              <th>Date</th>
            </tr>
          </thead>
          <tbody>
            {emails.length === 0 ? (
              <tr>
                <td colSpan={4} style={{ textAlign: 'center', padding: '32px', color: 'var(--text-muted)' }}>
                  {loading ? 'Loading emails...' : 'No emails found matching selected filter.'}
                </td>
              </tr>
            ) : (
              emails.map((m) => (
                <tr key={m.id}>
                  <td style={{ fontWeight: 500, minWidth: '180px' }}>
                    <div>{m.sender_name || m.sender_email}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{m.sender_email}</div>
                  </td>
                  <td>
                    <div style={{ fontWeight: 600 }}>{m.subject}</div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                      {m.snippet}
                    </div>
                  </td>
                  <td>
                    <span style={{ 
                      padding: '4px 8px', 
                      borderRadius: '6px', 
                      background: '#eff6ff', 
                      color: 'var(--primary)', 
                      fontSize: '0.75rem', 
                      fontWeight: 600 
                    }}>
                      {m.category || 'General'}
                    </span>
                  </td>
                  <td style={{ fontSize: '0.85rem', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                    {new Date(m.received_at).toLocaleDateString()}
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
