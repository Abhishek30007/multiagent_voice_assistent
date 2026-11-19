import React, { useState } from 'react';
import { X, Send, PhoneOff } from 'lucide-react';
import { api } from '../services/api';

interface VoiceTesterModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const VoiceTesterModal: React.FC<VoiceTesterModalProps> = ({ isOpen, onClose }) => {
  const [messages, setMessages] = useState<Array<{ sender: 'user' | 'assistant'; text: string }>>([
    {
      sender: 'assistant',
      text: "Hello, I'm Abhishek's AI assistant. He is currently unavailable. How may I help you?",
    },
  ]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [callId] = useState(`call_${Math.random().toString(36).substring(2, 9)}`);

  if (!isOpen) return null;

  const handleSend = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputText.trim() || loading) return;

    const userMsg = inputText.trim();
    setInputText('');
    setMessages((prev) => [...prev, { sender: 'user', text: userMsg }]);
    setLoading(true);

    try {
      const data = await api.simulateVoiceTurn(userMsg, callId);
      setMessages((prev) => [
        ...prev,
        { sender: 'assistant', text: data.response_text },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { sender: 'assistant', text: "Connection error. Could you repeat that?" },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleEnd = async () => {
    try {
      await fetch(`/api/v1/voice/end_call?call_id=${callId}`, { method: 'POST' });
    } catch (e) {
      // ignore
    }
    onClose();
  };

  return (
    <div className="modal-backdrop">
      <div className="modal-content">
        <div style={{ padding: '16px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#10b981' }}></span>
            <span style={{ fontWeight: 600 }}>Active Voice Representative Call</span>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer' }}>
            <X size={20} color="var(--text-muted)" />
          </button>
        </div>

        <div className="chat-box">
          {messages.map((m, idx) => (
            <div key={idx} className={`bubble ${m.sender}`}>
              {m.text}
            </div>
          ))}
          {loading && (
            <div className="bubble assistant" style={{ fontStyle: 'italic', color: 'var(--text-muted)' }}>
              Checking schedule & records...
            </div>
          )}
        </div>

        <form onSubmit={handleSend} style={{ padding: '16px', display: 'flex', gap: '8px', borderTop: '1px solid var(--border)' }}>
          <input
            type="text"
            placeholder="Type caller question (e.g., 'Is Abhishek free tomorrow at 4 PM?')"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            style={{ flex: 1, padding: '10px 14px', borderRadius: '8px', border: '1px solid var(--border)', outline: 'none' }}
          />
          <button type="submit" className="btn btn-primary" disabled={loading}>
            <Send size={16} />
          </button>
          <button type="button" className="btn btn-danger" onClick={handleEnd} title="Hang up">
            <PhoneOff size={16} />
          </button>
        </form>
      </div>
    </div>
  );
};
