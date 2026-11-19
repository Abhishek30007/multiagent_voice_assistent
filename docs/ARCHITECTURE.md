# Personal AI Twin Architecture & Design

This document details the complete end-to-end architecture, multi-agent reasoning flow, telephone call sequence, and data flow for Abhishek's Personal AI Twin.

---

## 1. End-to-End System Architecture

```mermaid
graph TD
    Caller([Incoming Caller / Browser]) -->|SIP Trunk / WebRTC| LiveKit[LiveKit Server & SIP Dispatcher]
    LiveKit -->|Audio Frames| STT[Deepgram Speech-to-Text Adapter]
    STT -->|Transcript| VoiceSession[LiveKit Voice Session Manager]
    VoiceSession -->|Query + Context| LangGraph[LangGraph Multi-Agent Engine]
    
    subgraph MultiAgentEngine [LangGraph Multi-Agent System]
        Supervisor[Supervisor Agent] -->|Route: Calendar| CalAgent[Calendar Agent]
        Supervisor -->|Route: Gmail| MailAgent[Gmail Retrieval Agent]
        Supervisor -->|Route: Both| CalAgent
        CalAgent --> MailAgent
        CalAgent --> EvVal[Evidence Validation Agent]
        MailAgent --> EvVal
        EvVal --> Safety[Safety & Policy Agent]
        Safety --> ResponseAg[Response Generation Agent]
    end
    
    LangGraph -->|Grounded Response Text| TTS[Cartesia / ElevenLabs TTS Adapter]
    TTS -->|Synthesized Audio Stream| LiveKit
    LiveKit -->|Natural Voice Output| Caller

    subgraph DataStorage [Personal Knowledge Base]
        Postgres[(PostgreSQL 16 DB)]
        Redis[(Redis 7 Cache & Locks)]
        Postgres --> MailAgent
        Postgres --> CalAgent
    end

    subgraph DataIngestion [Background Data Ingestion]
        GmailAPI[Gmail API v1] -->|Incremental Sync| Ingest[Email Ingestion Service]
        GCalAPI[Google Calendar v3] -->|SyncToken| IngestCal[Calendar Ingestion Service]
        Ingest --> Postgres
        IngestCal --> Postgres
    end
```

---

## 2. Voice Call Turn Sequence

```mermaid
sequenceDiagram
    autonumber
    actor Caller as Incoming Caller
    participant Trunk as Telephony Trunk (SIP)
    participant LK as LiveKit Engine
    participant Session as Call Session Manager
    participant Graph as LangGraph Multi-Agent
    participant DB as PostgreSQL
    participant TTS as Text-to-Speech

    Caller->>Trunk: Dials Dedicated AI Number
    Trunk->>LK: SIP INVITE
    LK->>Session: Establish Isolated Call Session
    Session-->>Caller: Speaks Introductory Greeting ("Hello, I'm Abhishek's AI assistant...")
    
    Caller->>LK: "Is Abhishek available tomorrow at 4 PM?"
    LK->>Session: Audio Data
    Session->>Session: Deepgram Speech-to-Text Transcribe
    Session->>Graph: Invoke Agent Pipeline (Isolated State)
    
    Graph->>DB: Query CalendarEvent for tomorrow 4 PM
    DB-->>Graph: Found 'Online Assessment Scheduled'
    Graph->>Graph: Validate Evidence (Anti-Hallucination)
    Graph->>Graph: Check Disclosure Policy & Neutralize Injections
    Graph-->>Session: Grounded Response ("I found an online assessment at 4 PM tomorrow...")
    
    Session->>TTS: Synthesize Speech
    TTS-->>LK: Stream Audio Frames
    LK-->>Caller: Caller Hears Grounded Natural Answer
```

---

## 3. Privacy, Permissions & Anti-Hallucination Guarantees

1. **Clear AI Persona Identification**: The agent introduces itself clearly on turn 1: *"Hello, I'm Abhishek's AI assistant. He is currently unavailable. How may I help you?"*
2. **Strict Read-Only Grounding**: The system queries only verified records from Abhishek's connected Gmail and primary Google Calendar.
3. **No Halucination**: If evidence is missing, the agent abstains: *"I don't have verified information about that. I can take a message for him."*
4. **Zero Write Permissions**: The AI representative cannot modify calendar events, cancel appointments, or send emails.
5. **No Credential / Financial Disclosure**: Passwords, OTPs, financial balances, and full credit card details are filtered by the Safety Agent.
6. **No Raw Audio Retention**: Raw call audio is not stored to disk by default, protecting caller privacy.
