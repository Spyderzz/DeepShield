# DeepShield Deployment Guide

This guide will walk you through hosting your DeepShield project for free using **Hugging Face Spaces** (Backend), **Vercel** (Frontend), and **Neon** (Database).

---

## 1. Set Up the Database (Neon)

Since local SQLite databases are wiped on free cloud hosts when the server goes to sleep, you must use a free cloud Postgres database.

1. Go to [Neon.tech](https://neon.tech/) and sign up for a free account.
2. Create a new project (e.g., `deepshield-db`).
3. Once created, copy the **Connection String** from your dashboard. It will look something like this:
   `postgresql://username:password@ep-cool-butterfly-12345.us-east-2.aws.neon.tech/neondb?sslmode=require`
4. Update your backend `.env` file (locally and when deploying) to use this new URL:
   ```env
   DATABASE_URL=postgresql://username:password@ep-cool-butterfly...
   ```

---

## 2. Deploy the Backend (Hugging Face Spaces)

Hugging Face Spaces provides 16GB of RAM for free, which is perfect for your PyTorch/EfficientNet ML models.

### Step 1: Create the Space
1. Go to [Hugging Face Spaces](https://huggingface.co/spaces) and log in or create an account.
2. Click **Create new Space**.
3. Set the **Space name** (e.g., `deepshield-api`).
4. Select **Docker** as the Space SDK and choose the **Blank** template.
5. Set Space hardware to the free tier (16GB RAM, 2 vCPU).
6. Click **Create Space**.

### Step 2: Upload Your Code
1. Once created, you will see instructions to clone the Space repository.
2. In your local terminal, navigate outside your current project and clone the space:
   ```bash
   git clone https://huggingface.co/spaces/YOUR_USERNAME/deepshield-api
   ```
3. Copy **the contents of your `backend` folder** (including the `Dockerfile` I just created for you) into this new cloned folder.
4. Add your `.env` variables to Hugging Face:
   - Go to your Space's **Settings**.
   - Scroll down to **Variables and secrets**.
   - Add your environment variables as **Secrets** (e.g., `DATABASE_URL`, `JWT_SECRET`, `GEMINI_API_KEY`).

### Step 3: Push to Deploy
1. In the terminal, inside the cloned Space folder:
   ```bash
   git add .
   git commit -m "Initial deploy"
   git push
   ```
2. Hugging Face will start building your Docker image automatically. Once it says "Running", your backend is live!
3. **Get your API URL:** Your API URL will be `https://YOUR_USERNAME-deepshield-api.hf.space`.

---

## 3. Deploy the Frontend (Vercel)

Vercel is the easiest place to host a React/Vite app.

### Step 1: Update API Connection
Before deploying, make sure your frontend knows where to find the Hugging Face API.
1. Open `frontend/.env` (or create it if it doesn't exist).
2. Set the API URL to your new Hugging Face Space URL:
   ```env
   VITE_API_BASE_URL=https://YOUR_USERNAME-deepshield-api.hf.space/api/v1
   ```

### Step 2: Push to GitHub
If your project isn't on GitHub yet, push it! Vercel deploys directly from your GitHub repository.

### Step 3: Deploy on Vercel
1. Go to [Vercel](https://vercel.com/) and sign up with your GitHub account.
2. Click **Add New** -> **Project**.
3. Import your GitHub repository (`minor2` or whatever you named it).
4. In the configuration settings:
   - **Framework Preset:** Vite
   - **Root Directory:** Edit this and select the `frontend` folder (since your React app is inside `frontend/`).
   - **Environment Variables:** Add `VITE_API_BASE_URL` and paste your Hugging Face API URL.
5. Click **Deploy**.

Within 2 minutes, Vercel will give you a live URL for your React app!

---

## Testing Your Deployment
1. Open your Vercel URL.
2. Try to register a new user (this tests the Neon Database).
3. Try to upload an image for analysis (this tests the Hugging Face Backend and ML models).
