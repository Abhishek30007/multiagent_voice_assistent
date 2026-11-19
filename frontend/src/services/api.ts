import { AuthStatus, EmailMessage, CalendarEvent, CallLog, MetricsSummary, SyncStatus } from '../types';

const BASE_URL = '/api/v1';

export const api = {
  async getAuthStatus(): Promise<AuthStatus> {
    const res = await fetch(`${BASE_URL}/auth/google/status`);
    const json = await res.json();
    return json.data;
  },

  async getEmails(page = 1, category = ''): Promise<{ items: EmailMessage[]; total: number }> {
    const catQuery = category ? `&category=${encodeURIComponent(category)}` : '';
    const res = await fetch(`${BASE_URL}/emails?page=${page}&limit=20${catQuery}`);
    return res.json();
  },

  async getCalendarEvents(): Promise<{ items: CalendarEvent[]; total: number }> {
    const res = await fetch(`${BASE_URL}/calendar/events?limit=50`);
    return res.json();
  },

  async getCallHistory(page = 1): Promise<{ items: CallLog[]; total: number }> {
    const res = await fetch(`${BASE_URL}/calls/history?page=${page}&limit=20`);
    return res.json();
  },

  async getMetrics(): Promise<MetricsSummary> {
    const res = await fetch(`${BASE_URL}/metrics/dashboard`);
    const json = await res.json();
    return json.data;
  },

  async getSyncStatus(): Promise<SyncStatus> {
    const res = await fetch(`${BASE_URL}/sync/status`);
    const json = await res.json();
    return json.data;
  },

  async triggerSync(service = 'all'): Promise<void> {
    await fetch(`${BASE_URL}/sync/${service}`, { method: 'POST' });
  },

  async disconnectGoogle(): Promise<void> {
    await fetch(`${BASE_URL}/auth/google/disconnect`, { method: 'POST' });
  },

  async simulateVoiceTurn(callerText: string, callId?: string): Promise<any> {
    const res = await fetch(`${BASE_URL}/voice/simulate_turn`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        caller_text: callerText,
        call_id: callId,
      }),
    });
    const json = await res.json();
    return json.data;
  },
};
