#!/usr/bin/env python3
"""Publish a link-flow audit run as a dashboard snapshot.

Converts the internal-linking-audit outputs (flow_results.csv merged with cluster
classifications, plus metrics.json) into data/<client>/<date>.json and updates the
client manifest and the top-level clients.json.

Usage:
  python publish_run.py --client amazon-business --display-name "Amazon Business (US)" \
      --base-url https://business.amazon.com \
      --flow path/to/flow_clustered.csv --metrics path/to/flow/metrics.json \
      --date 2026-08-05 --label "Post-Batch-1 recrawl" [--hubs hubs.json] [--repo-dir .]

Then: git add data/ && git commit -m "Add <client> <date> run" && git push
"""
import argparse, json, os
import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument('--client', required=True, help='slug, e.g. amazon-business')
ap.add_argument('--display-name', default=None)
ap.add_argument('--base-url', default='')
ap.add_argument('--flow', required=True, help='flow results CSV with url,flow_share_pct,flow_rank,tier,cluster,page_type,traffic,refdomains')
ap.add_argument('--metrics', required=True, help='metrics.json from compute_flow.py')
ap.add_argument('--date', required=True, help='YYYY-MM-DD')
ap.add_argument('--label', default='Audit run')
ap.add_argument('--hubs', default=None, help='optional JSON file {cluster: hub_path_or_null}')
ap.add_argument('--repo-dir', default='.')
a = ap.parse_args()

f = pd.read_csv(a.flow)
m = json.load(open(a.metrics))
col = lambda *names: next((c for c in f.columns if c.lower() in names), None)
cU, cC, cT, cP = col('url'), col('cluster'), col('tier'), col('page_type')
cD = col('crawl depth', 'depth_sf', 'click depth')
pages = []
for _, r in f.sort_values('flow_rank').iterrows():
    pages.append({
        'u': str(r[cU]).replace(a.base_url, ''),
        'c': r[cC] if cC and pd.notna(r[cC]) else 'None',
        't': int(r[cT]) if cT and pd.notna(r[cT]) else 3,
        'pt': r[cP] if cP and pd.notna(r[cP]) else 'other',
        'fs': round(float(r['flow_share_pct']), 5),
        'fr': int(r['flow_rank']),
        'tr': int(r['traffic']) if pd.notna(r.get('traffic')) else 0,
        'rd': int(r['refdomains']) if pd.notna(r.get('refdomains')) else 0,
        'd': int(r[cD]) if cD and pd.notna(r[cD]) else None})

snap = {'id': a.date, 'date': a.date, 'label': a.label, 'base_url': a.base_url,
        'metrics': {'nodes': m['nodes'], 'edges': m['edges'], 'gini': m['gini'],
                    'link_loss_pct': m.get('link_loss_pct_tier4'),
                    'tier_flow_share_pct': m.get('tier_flow_share_pct', {}),
                    'spearman_vs_ahrefs': m.get('spearman_vs_ahrefs_page_rating')},
        'hubs': json.load(open(a.hubs)) if a.hubs else {},
        'pages': pages}

ddir = os.path.join(a.repo_dir, 'data', a.client)
os.makedirs(ddir, exist_ok=True)
json.dump(snap, open(os.path.join(ddir, f'{a.date}.json'), 'w'), separators=(',', ':'))

mpath = os.path.join(ddir, 'manifest.json')
man = json.load(open(mpath)) if os.path.exists(mpath) else {
    'client': a.client, 'display_name': a.display_name or a.client, 'base_url': a.base_url, 'runs': []}
man['runs'] = [r for r in man['runs'] if r['id'] != a.date]
t2 = snap['metrics']['tier_flow_share_pct'].get('2')
man['runs'].append({'id': a.date, 'date': a.date, 'label': a.label, 'nodes': m['nodes'],
                    'edges': m['edges'], 'gini': m['gini'],
                    'link_loss_pct': snap['metrics']['link_loss_pct'], 'tier2_share': t2})
man['runs'].sort(key=lambda r: r['date'])
json.dump(man, open(mpath, 'w'), indent=1)

cpath = os.path.join(a.repo_dir, 'data', 'clients.json')
cl = json.load(open(cpath)) if os.path.exists(cpath) else {'clients': []}
if not any(c['id'] == a.client for c in cl['clients']):
    cl['clients'].append({'id': a.client, 'display_name': a.display_name or a.client})
    json.dump(cl, open(cpath, 'w'), indent=1)

print(f'Wrote {ddir}/{a.date}.json ({len(pages)} pages); manifest now has {len(man["runs"])} run(s).')
print('Next: git add data/ && git commit && git push')
