# Airliny Status

A bilingual, static website status page hosted on GitHub Pages. GitHub Actions performs actual HTTP checks on a five-minute schedule and commits observed results. No browser-side cross-origin requests are used for monitoring, and no synthetic uptime history is generated.

## 1. Configure targets first

Edit [config/monitors.json](config/monitors.json) and replace the example URLs with real sites or health endpoints you control. Example:

```json
[
  {
    "id": "homepage",
    "name": "My website",
    "url": "https://your-domain.example/",
    "group": "Website",
    "timeout_seconds": 15,
    "expected_status": [200]
  }
]
```

Each monitor requires a unique `id`, display `name`, and absolute HTTP(S) `url`. `expected_status` lists acceptable HTTP response codes. Prefer a lightweight health endpoint for APIs. Only add endpoints you are authorized to monitor. Do not put private URLs, credentials, tokens, or secrets in this public repository.

## 2. Enable GitHub Actions write permission

Open repository **Settings → Actions → General → Workflow permissions**, select **Read and write permissions**, and save. The monitoring workflow needs permission to commit the real check results to `data/status.json` and `data/history.json`.

## 3. Enable GitHub Pages

Open **Settings → Pages** and choose **GitHub Actions** as the build and deployment source. The `Deploy status page to GitHub Pages` workflow deploys the static files from the repository root. You can also open the **Actions** tab and manually run both workflows.

For this repository, the expected Pages URL is:

`https://airliny.github.io/airliny-status/`

It will work only after the Pages workflow completes successfully and Pages is enabled.

## 4. First run and real data

Go to **Actions → Website monitoring → Run workflow** to perform the first check. The first history day is populated only after actual requests run. Historical days without observations are shown as no data, not as 100% uptime. A daily uptime percentage is calculated from the number of successful versus total checks recorded for that day.

The scheduled job requests each URL from a GitHub-hosted runner. HTTP status and response latency are recorded. A non-expected status or network error is marked as a failed check. This is an HTTP availability check, not a full end-to-end test of your application.

## 5. Scheduling caveats

The workflow uses `*/5 * * * *`. GitHub Actions scheduled workflows can start late or be temporarily delayed, so five minutes is the intended cadence, not a guaranteed SLA. The page refreshes its JSON data once per minute, but it cannot show a check until the monitoring workflow commits it.

## 6. Languages and layout

Use the top-right language toggle to switch between Simplified Chinese and English. Edit `assets/style.css` for visual styling and `assets/app.js` for page rendering. Configure all monitored targets in `config/monitors.json`.

## Data files

- `data/status.json`: latest actual result and recent state-change events.
- `data/history.json`: daily counters derived from actual checks.
- `scripts/monitor.py`: Python standard-library HTTP checker.
- `.github/workflows/monitor.yml`: scheduled monitoring and result commit.
- `.github/workflows/pages.yml`: GitHub Pages deployment.

This project is inspired by the clean layout of modern service status pages; it is not an official DeepSeek website or an exact pixel-for-pixel copy.