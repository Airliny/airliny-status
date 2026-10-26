# Airliny Status

A bilingual static status page hosted on GitHub Pages. GitHub Actions checks monitored sites every five minutes and stores real results. Optional email subscriptions use a Cloudflare Worker + D1 and Resend; the static page never receives mail credentials.

## Email subscriptions (free-tier friendly)

This feature requires one-time setup. It is not live until the Cloudflare Worker is deployed, its secrets are set, and the two GitHub Actions secrets are added. Cloudflare and Resend free-plan limits/policies can change; verify current quotas before relying on notifications.

### 1. Create Cloudflare D1 database

1. Sign in to Cloudflare and open **Workers & Pages → D1 SQL Database → Create database**.
2. Name it `airliny-status-subscriptions`.
3. Open the database's **Console** and run the complete SQL in [cloudflare/migrations/0001_init.sql](cloudflare/migrations/0001_init.sql).
4. Copy the database ID into `cloudflare/wrangler.toml` replacing `REPLACE_WITH_YOUR_D1_DATABASE_ID`.

### 2. Configure Resend email

1. Create a Resend account and an API key.
2. Verify a sender domain you control in Resend (DNS records must be added at your DNS provider). Use a sender such as `Airliny Status <status@your-verified-domain.example>`.
3. Do not put the API key in this repository.

### 3. Deploy Worker

Install Node.js and Wrangler on your computer, then run from the repository root:

```bash
cd cloudflare
npm install -g wrangler
wrangler login
wrangler d1 list
# Edit wrangler.toml and set database_id first
wrangler secret put RESEND_API_KEY
wrangler secret put FROM_EMAIL
wrangler secret put SITE_URL
wrangler secret put MONITOR_SECRET
wrangler deploy
```

Use a long random value for `MONITOR_SECRET` and keep it private. For `SITE_URL`, use `https://airliny.github.io/airliny-status`. When Wrangler asks for each secret, paste the value; do not commit it. The Worker URL will look like `https://airliny-status-subscriptions.<your-account>.workers.dev`.

### 4. Connect the static page

In `assets/app.js`, replace `https://REPLACE-WITH-YOUR-WORKER.workers.dev` in `SUBSCRIBE_API` with your deployed Worker URL, then commit and push. GitHub Pages will redeploy the frontend.

### 5. Add GitHub Actions secrets

Repository **Settings → Secrets and variables → Actions → New repository secret**:

- `MONITOR_API_URL`: your Worker base URL, without a trailing slash.
- `MONITOR_SECRET`: exactly the same random secret used for the Worker.

The monitor workflow calls the Worker after each check. The Worker sends mail only when a monitor changes state after its initial baseline (healthy → down or down → healthy), not on every five-minute run.

### 6. Test

- Visit the status page, click **Subscribe**, enter your email and submit.
- Open the confirmation email and click the confirmation link.
- Test notification flow by temporarily changing a monitored site's expected status only if you control that endpoint, or use a dedicated test monitor; restore the configuration afterwards.
- Use the unsubscribe link in an email to remove the address.

### Security and operational notes

- Pending subscriptions require email confirmation; unsubscribe links contain unguessable random tokens.
- Subscriber emails and tokens live in D1, not in the public Git repository.
- The monitor endpoint requires `MONITOR_SECRET`; never expose it in frontend code.
- Resend requires a verified sending domain for production delivery. Free service quotas and account verification requirements may change.
- Worker notifications run after the monitor script and before the monitoring data commit. If the notification call fails, the workflow fails visibly rather than silently pretending it worked.
- Consider adding rate limits/Turnstile before promoting the public form widely. A public endpoint can otherwise be abused to trigger confirmation emails.

## Monitoring setup

Open repository **Settings → Actions → General → Workflow permissions**, select **Read and write permissions**, and save. Under **Settings → Pages**, select **GitHub Actions** as the source. The expected URL is https://airliny.github.io/airliny-status/.

The scheduled workflow uses `*/5 * * * *`; GitHub may delay scheduled runs. The page refreshes JSON every minute, but data updates only after a check completes and commits.

## Files

- `config/monitors.json`: monitored targets
- `data/status.json`: latest actual checks and state-change events
- `data/history.json`: daily observed uptime counters
- `scripts/monitor.py`: real HTTP checker
- `.github/workflows/monitor.yml`: five-minute checks and optional email notifications
- `cloudflare/src/index.js`: subscribe, confirm, unsubscribe, and notification API
- `cloudflare/migrations/0001_init.sql`: D1 schema
