# 🚀 Zero-Cost Deployment Guide

To maintain a "Zero-Cost" footprint while using our new Reflex + FastAPI + Redis architecture, we recommend the following serverless stack.

## 🏗️ The Production Stack

| Component | Provider | Why? |
|-----------|----------|------|
| **Backend API** | [GCP Cloud Run](https://cloud.google.com/run) | Scales to 0 when idle. No ongoing costs if no traffic. |
| **Session Cache** | [Upstash Redis](https://upstash.com/) | Serverless Redis with a generous Free Tier (Serverless-optimized). |
| **Frontend UI** | [Reflex Cloud](https://reflex.dev/cloud) | Native hosting for Reflex apps with managed scaling. |

---

## 🛠️ Step 1: Managed Redis (Upstash)
Since Cloud Run shuts down between requests, you need a "Global" Redis to keep session IDs alive for 30 minutes.

1. Create a free account at [upstash.com](https://upstash.com/).
2. Create a "Serverless Redis" database in a region close to your users.
3. **Copy the URL**: `redis://default:password@your-endpoint:6379`.

---

## 🛠️ Step 2: Backend (GCP Cloud Run)
Your current `Dockerfile` is already optimized for Cloud Run. I have created a helper script to automate this for you.

1. **Wait!** First, customize the `scripts/deploy_backend.sh` with your unique `PROJECT_ID`.
2. **Run the script**:
   ```bash
   ./scripts/deploy_backend.sh
   ```

*(Alternatively, run the raw `gcloud` commands manually):*

1. **Build and push** the container:
   ```bash
   gcloud builds submit --tag gcr.io/your-project-id/securemed-api .
   ```

2. **Deploy** with zero instances minimum:
   ```bash
   gcloud run deploy securemed-api \
     --image gcr.io/your-project-id/securemed-api \
     --platform managed \
     --region southamerica-east1 \
     --min-instances 0 \
     --set-env-vars="REDIS_URL=your_upstash_url,SECUREMED_API_KEY=your_key" \
     --allow-unauthenticated
   ```

---

## 🛠️ Step 3: Frontend (Reflex Cloud)
Reflex simplifies the deployment of the UI and the management of the "Backend URL" out of the box.

1. From the `reflex_app` directory:
   ```bash
   reflex deploy
   ```
2. Follow the prompts to create an account and name your app.
3. Set your **API_BASE_URL** inside the Reflex environment variables to point to your new Cloud Run URL.

---

## 🔐 Security Reinforcement
*   **Secrets**: In production, use `GCP Secret Manager` instead of env vars for `SECUREMED_API_KEY`.
*   **CORS**: Update `securemed_chat/main.py` to only allow your Reflex Cloud domain to talk to the API.

---

## 📊 Estimated Monthly Cost: **$0.00**
*(Assuming < 100 concurrent users per month and < 10k Redis commands daily)*
