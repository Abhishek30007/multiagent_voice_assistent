# Production Google Cloud Platform (GCP) Deployment Guide

This guide describes how to deploy the Personal AI Twin system to Google Cloud Platform with production-grade reliability, security, and scalability.

---

## 1. Architectural Distribution on GCP

Because voice calls require persistent WebRTC connections, we separate the stateless API tier from the long-running voice worker:

| Component | Recommended GCP Service | Why |
|---|---|---|
| **FastAPI Backend & API** | Google Cloud Run | Auto-scales to zero, manages HTTPS endpoints, handles OAuth callbacks. |
| **React Dashboard Frontend** | Cloud Run or Firebase Hosting | Fast global CDN distribution of static assets. |
| **PostgreSQL Database** | Cloud SQL for PostgreSQL (v16) | Fully managed, automated backups, encryption at rest, private VPC peering. |
| **Redis Cache & Celery Broker** | Cloud Memorystore for Redis | Low-latency in-memory data store with VPC isolation. |
| **Celery Ingestion Workers** | Cloud Run Jobs or GKE Autopilot | Scheduled background task execution. |
| **Persistent Voice Workers** | Google Kubernetes Engine (GKE) or Compute Engine VM | Persistent WebRTC / SIP voice streaming connections. |
| **Secrets & Keys** | Google Secret Manager | Secure encrypted storage for OAuth tokens, Fernet key, API keys. |

---

## 2. Step-by-Step GCP Deployment

### Step 1: Provision Secret Manager Secrets
```bash
gcloud services enable secretmanager.googleapis.com

# Create secrets
echo -n "your-fernet-encryption-key" | gcloud secrets create TOKEN_ENCRYPTION_KEY --data-file=-
echo -n "your-google-client-id" | gcloud secrets create GOOGLE_CLIENT_ID --data-file=-
echo -n "your-google-client-secret" | gcloud secrets create GOOGLE_CLIENT_SECRET --data-file=-
echo -n "your-livekit-api-key" | gcloud secrets create LIVEKIT_API_KEY --data-file=-
echo -n "your-livekit-api-secret" | gcloud secrets create LIVEKIT_API_SECRET --data-file=-
echo -n "your-deepgram-api-key" | gcloud secrets create DEEPGRAM_API_KEY --data-file=-
echo -n "your-cartesia-api-key" | gcloud secrets create CARTESIA_API_KEY --data-file=-
```

### Step 2: Provision Cloud SQL (PostgreSQL 16)
```bash
gcloud sql instances create personal-ai-twin-db \
    --database-version=POSTGRES_16 \
    --cpu=2 \
    --memory=7680MB \
    --region=us-central1 \
    --root-password="YourStrongSecurePassword123!"

gcloud sql databases create personal_ai_twin --instance=personal-ai-twin-db
```

### Step 3: Provision Cloud Memorystore (Redis 7)
```bash
gcloud redis instances create personal-ai-twin-redis \
    --size=1 \
    --region=us-central1 \
    --redis-version=redis_7_0
```

### Step 4: Deploy FastAPI Backend on Cloud Run
```bash
gcloud builds submit --tag gcr.io/$PROJECT_ID/personal-ai-twin-backend:latest .

gcloud run deploy personal-ai-twin-backend \
    --image gcr.io/$PROJECT_ID/personal-ai-twin-backend:latest \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars APP_ENV=production,OWNER_NAME=Abhishek,OWNER_EMAIL=abhishekkumarsaw414@gmail.com \
    --set-secrets TOKEN_ENCRYPTION_KEY=TOKEN_ENCRYPTION_KEY:latest,GOOGLE_CLIENT_ID=GOOGLE_CLIENT_ID:latest,GOOGLE_CLIENT_SECRET=GOOGLE_CLIENT_SECRET:latest,LIVEKIT_API_KEY=LIVEKIT_API_KEY:latest,LIVEKIT_API_SECRET=LIVEKIT_API_SECRET:latest \
    --add-cloudsql-instances $PROJECT_ID:us-central1:personal-ai-twin-db
```

### Step 5: Deploy React Frontend on Cloud Run
```bash
cd frontend
gcloud builds submit --tag gcr.io/$PROJECT_ID/personal-ai-twin-frontend:latest .

gcloud run deploy personal-ai-twin-frontend \
    --image gcr.io/$PROJECT_ID/personal-ai-twin-frontend:latest \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated
```

---

## 3. Connecting a Real Phone Number to LiveKit SIP

1. **Acquire Phone Number**: Purchase a telephone number on Twilio, Telnyx, or direct SIP provider.
2. **Create SIP Trunk**: Configure an outbound SIP Trunk in Twilio pointing to your LiveKit SIP endpoint domain:
   - SIP URI: `sip:<your-livekit-sip-domain>`
   - Transport: TLS / UDP
3. **Configure LiveKit Inbound SIP Rule**:
   Create a SIP Inbound Dispatch Rule in LiveKit Console:
   - Match Phone Number: `+1...`
   - Target Room: `call_{caller_number}_{timestamp}`
   - Participant Metadata: Caller Number and Geo info.
4. **Agent Auto-Join**: The persistent LiveKit Agent Worker will automatically receive room creation webhooks, connect via WebRTC, and introduce itself: *"Hello, I'm Abhishek's AI assistant. He is currently unavailable. How may I help you?"*
