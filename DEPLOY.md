# Deploying WhollyFare to Streamlit Community Cloud

Streamlit Community Cloud is free, takes about 5 minutes, and gives you a public URL
you can share for outside feedback. No server, no Docker, no ops.

---

## Step 1 — Push to GitHub

Open GitHub Desktop (or your terminal) and commit + push everything:

```
git add .
git commit -m "WhollyFare POC — initial public deployment"
git push
```

If the repo isn't on GitHub yet, create a new repo at https://github.com/new
(name it `whollyfare`, keep it **private** for now), then push.

---

## Step 2 — Deploy on Streamlit Community Cloud

1. Go to **https://share.streamlit.io** and sign in with your GitHub account.
2. Click **"New app"**.
3. Fill in:
   - **Repository:** `timhislop/whollyfare` (or whatever you named it)
   - **Branch:** `main`
   - **Main file path:** `app.py`
4. Click **"Deploy"**. Streamlit installs from `requirements.txt` automatically.
5. In about 60–90 seconds you'll get a live URL like:
   `https://whollyfare.streamlit.app`

---

## Step 3 — Set environment secrets (optional for POC)

The app works without API keys — you'll just use PDF upload and sample data.
If you want live Kroger API pulls, add secrets in the Streamlit Cloud dashboard:

**App settings → Secrets → Add secrets:**

```toml
KROGER_CLIENT_ID     = "your-kroger-client-id"
KROGER_CLIENT_SECRET = "your-kroger-client-secret"
USDA_API_KEY         = "your-usda-api-key"
```

These stay private — never committed to the repo.

---

## Step 4 — Share the link

Send the URL to anyone you want feedback from. The investor page is at:
`https://[your-app].streamlit.app/Investor`

The app resets session state on each visit (POC behaviour — no database yet),
so each reviewer starts fresh. That's fine for feedback purposes.

---

## Updating the app

Every `git push` to `main` triggers an automatic redeploy.
Reviewers just refresh the page to get the latest version.

---

## Switching to private / password-protected

In Streamlit Cloud dashboard → **Sharing** → set to "Only specific people"
and add email addresses. Useful for investor-only access.
