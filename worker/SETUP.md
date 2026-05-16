# Drive Upload Worker — Setup Guide

This Cloudflare Worker receives PDF blobs from the frontend and saves them to your Google Drive using a service account. Users never need to sign in to Google.

---

## Prerequisites

- Cloudflare account (free tier is fine — 100k requests/day)
- Node.js + npm installed
- Your existing GCP service account JSON (`tl-helper-495507-a417ead24ef5.json`)

---

## Step 1 — Share the Drive folder with your service account

1. Create (or pick) a Google Drive folder where PDFs should land.
2. Copy the folder ID from its URL: `drive.google.com/drive/folders/<FOLDER_ID>`
3. Click **Share** → paste your service account email (found in the JSON as `"client_email"`) → set role to **Editor** → click Share.

The service account email looks like: `tl-helper@tl-helper-495507.iam.gserviceaccount.com`

---

## Step 2 — Install Wrangler and log in

```bash
cd worker
npm install
npx wrangler login
```

This opens a browser to authorize Wrangler with your Cloudflare account.

---

## Step 3 — Set secrets

Run each of these and paste the value when prompted:

```bash
# Service account email (the "client_email" field from the JSON)
npx wrangler secret put SA_EMAIL

# Full private key (the "private_key" field from the JSON — paste the entire PEM including
# "-----BEGIN PRIVATE KEY-----" and "-----END PRIVATE KEY-----" lines)
npx wrangler secret put SA_PRIVATE_KEY

# Drive folder ID from Step 1
npx wrangler secret put FOLDER_ID
```

---

## Step 4 — Deploy

```bash
npx wrangler deploy
```

Wrangler prints your worker URL, e.g.:
```
https://atc-pdf-drive.<your-subdomain>.workers.dev
```

---

## Step 5 — Wire up the frontend

Open `public/index.html` and set `DRIVE_WORKER_URL` near line 515:

```javascript
const DRIVE_WORKER_URL = 'https://atc-pdf-drive.<your-subdomain>.workers.dev';
```

Commit and push — GitHub Actions will redeploy the site automatically.

---

## How it works

1. User clicks **export pdf** with rows selected.
2. `html2pdf.js` (loaded on demand) renders the audit report HTML to a PDF blob in-browser.
3. The PDF downloads locally to the user's machine.
4. The blob is also POSTed to this worker.
5. The worker signs a JWT using the service account, exchanges it for a Google access token, and uploads the file to your Drive folder via the Drive v3 API.
6. A toast in the app shows "Saved to Drive — open" with a direct link to the file.

All credentials live in Cloudflare as encrypted secrets — they are never exposed to users or committed to git.
