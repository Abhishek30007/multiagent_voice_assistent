export interface AuthStatus {
  is_connected: boolean;
  owner_name: string;
  owner_email: string;
  provider: string;
  scopes: string[];
  expires_at?: string;
  is_expired: boolean;
  gmail_connected: boolean;
  calendar_connected: boolean;
}

export interface EmailMessage {
  id: number;
  message_id: string;
  thread_id?: string;
  sender_name?: string;
  sender_email: string;
  subject?: string;
  snippet?: string;
  received_at: string;
  category?: string;
  is_read: boolean;
  has_attachments: boolean;
}

export interface CalendarEvent {
  id: number;
  event_id: string;
  summary?: string;
  description?: string;
  location?: string;
  start_time: string;
  end_time: string;
  is_all_day: boolean;
  status: string;
  organizer_email?: string;
}

export interface CallLog {
  id: number;
  call_id: string;
  caller_number: string;
  call_start_time: string;
  duration_seconds: number;
  call_status: string;
  turn_count: number;
  agent_execution_summary?: string;
  evidence_sources: Array<{ type: string; id: string; title: string }>;
}

export interface MetricsSummary {
  total_calls: number;
  failed_calls: number;
  failed_call_rate_pct: number;
  unsupported_response_rate_pct: number;
  tokens_consumed: number;
  estimated_cost_usd: number;
  latencies: Record<string, { avg_ms: number; p95_ms: number; samples: number }>;
}

export interface SyncStatus {
  is_syncing: boolean;
  services: Record<string, {
    service_name: string;
    sync_status: string;
    items_synced: number;
    last_sync_completed_at?: string;
  }>;
}
