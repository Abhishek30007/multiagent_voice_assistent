import React, { useEffect, useState } from 'react';
import { Calendar as CalIcon, Clock, MapPin } from 'lucide-react';
import { api } from '../services/api';
import { CalendarEvent } from '../types';

export const CalendarPage: React.FC = () => {
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getCalendarEvents().then((res) => {
      setEvents(res.items);
      setLoading(false);
    });
  }, []);

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 700 }}>Google Calendar Schedule</h2>
        <p style={{ color: 'var(--text-muted)' }}>Synchronized schedule used by AI to check Abhishek's availability</p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {events.length === 0 ? (
          <div className="card" style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
            {loading ? 'Loading calendar...' : 'No upcoming events found.'}
          </div>
        ) : (
          events.map((evt) => {
            const start = new Date(evt.start_time);
            const end = new Date(evt.end_time);
            return (
              <div key={evt.id} className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '6px' }}>
                    {evt.summary || '(Untitled Event)'}
                  </h3>
                  <div style={{ display: 'flex', gap: '16px', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Clock size={14} />
                      {start.toLocaleDateString()} {start.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} - {end.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                    {evt.location && (
                      <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <MapPin size={14} /> {evt.location}
                      </span>
                    )}
                  </div>
                  {evt.description && (
                    <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '8px' }}>
                      {evt.description}
                    </p>
                  )}
                </div>

                <div>
                  <span style={{ 
                    padding: '6px 12px', 
                    borderRadius: '20px', 
                    background: evt.status === 'confirmed' ? '#dcfce7' : '#fef9c3', 
                    color: evt.status === 'confirmed' ? '#15803d' : '#854d0e',
                    fontSize: '0.8rem',
                    fontWeight: 600,
                  }}>
                    {evt.status.toUpperCase()}
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
