# UI demo

This Vercel-ready Next.js demo simulates the four main outcomes of the hybrid system: automatic approval, a model decision corrected to rejection, escalation to human review, and collection of missing information.

Run locally:

```bash
cd demo
npm install
npm run dev
```

Requires Node.js 20.9 or newer. For Vercel, import the GitHub repository and set the project root directory to `demo`.

The current UI uses representative simulated model outputs. When an inference endpoint is available, replace the selected example payload in `app/page.js` with a server-side API call. Keep the deterministic rules engine authoritative.
