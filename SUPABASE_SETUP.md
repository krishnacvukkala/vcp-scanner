# Supabase setup — Aaroquant VCP Scanner

Follow these in order. It takes about 15 minutes, and everything on the free
tier. **Do not paste any key into a chat window** — every key goes straight
from the Supabase dashboard into GitHub or Vercel.

---

## Why this exists

A full scan takes minutes. A Vercel request has to finish in under a minute.
That is the whole reason "Run Scan Now" was failing: the hosted app was trying
to do a multi-minute job inside a web request, on a filesystem it is not
allowed to write to.

So the work moves off the request path:

```
GitHub Actions (scheduled)  ──scans──▶  Supabase  ◀──reads──  Vercel dashboard
        minutes, free                   Postgres              milliseconds
```

The dashboard never scans the universe again. It reads a finished scan out of
Postgres. Searching a single ticker still runs live, because one symbol
comfortably fits inside a request.

---

## Step 1 — Create the Supabase account

1. Go to **https://supabase.com** and click **Start your project**.
2. Sign in with **GitHub** (you already have an account —
   `krishnacvukkala`). This is the quickest route and means no new password.
3. If asked, authorise Supabase to read your GitHub profile. It does not need
   repository access for this.
4. You will land on the Supabase dashboard.

## Step 2 — Create the project

1. Click **New project**.
2. **Organization**: accept the personal one it offers, or create one.
3. **Name**: `aaroquant`
4. **Database Password**: click **Generate a password** and then **Copy** it.
   Save it in your password manager. You will not need it for this app (the
   app authenticates with an API key, not this password), but you cannot
   recover it later and you will want it if you ever connect directly with
   `psql` or a GUI.
5. **Region**: pick the one closest to you — **Central EU (Frankfurt)** for
   Munich. This is the single biggest factor in query latency.
6. **Pricing plan**: **Free**.
7. Click **Create new project** and wait ~2 minutes while it provisions.

## Step 3 — Create the tables

1. In the left sidebar, click **SQL Editor**.
2. Click **New query**.
3. Open `supabase/schema.sql` from this repository, copy the whole file, and
   paste it in.
4. Click **Run** (or ⌘↵).
5. You should see `Success. No rows returned`.
6. Click **Table Editor** in the sidebar and confirm four tables exist:
   `scan_runs`, `scan_results`, `ohlcv_cache`, `fundamentals_cache`.

The script turns on row-level security with no policies, so the public key can
read nothing. Only the service-role key — used server-side only — can touch
these tables.

## Step 4 — Copy your two credentials

1. Sidebar → **Project Settings** (the gear) → **API**.
2. Note these two values. Keep the tab open for the next two steps.

   | What | Where | Looks like |
   |---|---|---|
   | **Project URL** | "Project URL" | `https://abcdefgh.supabase.co` |
   | **service_role key** | "Project API keys" → `service_role`, click **Reveal** | a long `eyJ...` string |

**The `service_role` key bypasses all security.** It goes only into GitHub
Actions secrets and Vercel environment variables, both of which are encrypted
and server-side. Never put it in the browser, in `index.html`, in a commit, or
in a chat message. The `anon` key on the same page is not used by this project.

## Step 5 — Give GitHub Actions the keys (this runs the scans)

1. Go to **https://github.com/krishnacvukkala/vcp-scanner/settings/secrets/actions**
2. Click **New repository secret**, twice:

   | Name | Value |
   |---|---|
   | `SUPABASE_URL` | the Project URL from step 4 |
   | `SUPABASE_SERVICE_ROLE_KEY` | the service_role key from step 4 |

   The names must match exactly — the workflow reads them by name.

## Step 6 — Run the first scan by hand

1. Go to the repo's **Actions** tab.
2. If GitHub asks you to enable workflows on this repository, click
   **I understand my workflows, go ahead and enable them**.
3. Select **Scheduled VCP scan** in the left list.
4. Click **Run workflow** → leave the defaults → **Run workflow**.
5. It takes 2–5 minutes. Open the run to watch the log; you want to see
   `stored N result rows` near the end.

A quick sanity run first, if you prefer: set **limit** to `20` on that form. It
finishes in under a minute and proves the wiring before you commit to a full
scan.

After it succeeds, the schedule takes over on its own:

| When (UTC) | When (Munich) | Covers |
|---|---|---|
| 10:45, Mon–Fri | 12:45 CEST | NSE close (15:30 IST) |
| 21:45, Mon–Fri | 23:45 CEST | US close (16:00 ET) |

Change those in `.github/workflows/scan.yml`.

## Step 7 — Give Vercel the same keys (this serves the dashboard)

1. Open your project on Vercel → **Settings** → **Environment Variables**.
2. Add both, ticking **Production**, **Preview** and **Development**:

   | Name | Value |
   |---|---|
   | `SUPABASE_URL` | same as above |
   | `SUPABASE_SERVICE_ROLE_KEY` | same as above |

3. **Redeploy** — environment variables only apply to builds made after they
   are set. Deployments → the newest one → the `⋯` menu → **Redeploy**.

## Step 8 — Check it

Open `https://<your-app>.vercel.app/api/health`. You want:

```json
{
  "ok": true,
  "serverless": true,
  "supabase": {
    "configured": true,
    "reachable": true,
    "latest_run": { "source": "github-actions", "scanned": 164, "stale": false }
  }
}
```

Then open the dashboard and click **Run Scan Now**. It should return instantly
with the stored scan.

If `configured` is `false`, the environment variables did not reach the build —
recheck step 7 and redeploy. If `reachable` is `false`, the URL or key is
wrong. If `latest_run` is `null`, the scan in step 6 has not completed yet.

---

## Running the scanner from your own machine instead

The scheduled job is the normal path, but the same command works locally —
useful for an off-schedule refresh:

```bash
cd "VCP By TheChayyy"
export SUPABASE_URL="https://<project-ref>.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="eyJ..."

python -m gatewaydashboard.jobs.run_scan --source local          # full scan
python -m gatewaydashboard.jobs.run_scan --limit 20              # quick check
python -m gatewaydashboard.jobs.run_scan --dry-run               # writes nothing
```

Put those two exports in `~/.zshrc` (not in the repo) to make them permanent.

The local dashboard (`python gatewaydashboard/app.py`) picks the same variables
up. With them set it reads stored scans like the hosted one; without them it
behaves exactly as it always did — live scans, nothing stored. Storage is an
enhancement, never a dependency.

---

## What is stored

| Table | Holds | Written by |
|---|---|---|
| `scan_runs` | one row per scan: funnel counts, timing, settings, failures | the scheduled job |
| `scan_results` | one row per symbol per run — plus the full engine record as JSON | the scheduled job |
| `ohlcv_cache` | chart series per symbol and timeframe | the job, and the API on a miss |
| `fundamentals_cache` | quarterly statements and ratios | the API |

`scan_results.record` is the engine's own output, stored verbatim. The flat
columns beside it (`pivot`, `stop`, `close`, `risk_pct` …) exist so the
dashboard can filter in SQL; they are derived from that record and are `null`
wherever the engine had no value. Nothing is filled in to make a row look
complete.

Free-tier limits are 500 MB of database and 5 GB of egress per month. A run of
164 symbols is roughly 3–5 MB, and `prune_scan_history()` keeps only the newest
60 runs, so steady-state usage is a few hundred MB at most.

---

## Cost

Everything above is free: Supabase free tier, GitHub Actions (2,000 minutes a
month on free accounts; this uses roughly 150), and Vercel Hobby. The only
thing to watch is that Supabase pauses a free project after **7 days with no
activity** — the twice-daily scan is activity, so it will not pause while the
schedule is running.
