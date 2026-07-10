# Omniscient Link Flow Dashboard

Static dashboard for internal-linking audit results. One snapshot per crawl, per client. No build step; GitHub Pages serves `index.html` directly.

## Structure

```
index.html                      dashboard (ECharts via CDN, brand-styled)
publish_run.py                  converts audit outputs into a snapshot + manifest entry
data/clients.json               list of clients for the switcher
data/<client>/manifest.json     run list with headline metrics
data/<client>/<YYYY-MM-DD>.json one snapshot per crawl (metrics + all pages)
```

## Adding a new run

After an audit's flow stage (`compute_flow.py`) finishes:

```
python publish_run.py --client amazon-business \
  --base-url https://business.amazon.com \
  --flow flow_clustered.csv --metrics flow/metrics.json \
  --date 2026-08-05 --label "Post-Batch-1 recrawl"
git add data/ && git commit -m "amazon-business 2026-08-05 run" && git push
```

The dashboard picks it up automatically: it appears in the Report dropdown, and any two runs can be compared (delta chips on the scorecard, movement columns and top gainers/decliners in the leaderboard).

Adding a new client is the same command with a new `--client` slug and `--display-name`; the client switcher updates automatically.

## Sharing

Deep links carry state: `?client=amazon-business&run=2026-07-08&compare=2026-06-01`.

## Visibility: public for now, private on migration

This repo is temporarily public while the team reviews the prototype (rationale: URL-level data is obtainable from any crawl; the proprietary part is the analysis). If adopted, flip to private:

- [ ] Upgrade plan so private repos can use Pages (GitHub Enterprise), or move hosting (Cloudflare Pages / Netlify with access control)
- [ ] Repo Settings → General → Danger Zone → Change visibility → Private
- [ ] Repo Settings → Pages → confirm Pages still enabled (Enterprise) or point DNS/hosting at the new provider
- [ ] Update any shared dashboard links if the URL changes
- [ ] index.html hotlinks the logo from beomniscient.com → optionally vendor it into `assets/`
- [ ] Remove the "temporarily public" line from the dashboard footer and this section

No data or code changes are required to flip; snapshots and manifests are host-agnostic.
