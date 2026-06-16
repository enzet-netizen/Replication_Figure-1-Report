import pandas as pd
import numpy as np
from collections import defaultdict
import os

DISAMBIG = 'disambig_clean.csv'
ALPHA    = 'alpha_scores.csv'
ARXIV    = 'arxiv_clean.csv'
OUTPUT   = 'panel.csv'

np.random.seed(42)
PRE_START, PRE_END = '2018-01', '2021-12'
OBS_START, OBS_END = '2022-01', '2024-06'

all_months = pd.period_range('2018-01', '2024-06', freq='M').astype(str).tolist()
m2i = {m: i for i, m in enumerate(all_months)}

arxiv = pd.read_csv(ARXIV, usecols=['arxiv_id', 'pub_month'], dtype={'arxiv_id': str})
date_map = dict(zip(arxiv['arxiv_id'], arxiv['pub_month']))

alpha = pd.read_csv(ALPHA, dtype={'id': str})
llm_map = dict(zip(alpha['id'], alpha['is_llm']))

dis = pd.read_csv(DISAMBIG, dtype=str).fillna('')

records = []
incumbent_count = defaultdict(int)
for r in dis.itertuples():
    author_id = f"{r.subject}|{r.last}|{r.first}"
    for pid in str(r.paper_ids).split('|'):
        month = date_map.get(pid)
        if month is None:
            continue
        if PRE_START <= month <= PRE_END:
            incumbent_count[author_id] += 1
        records.append((author_id, pid, month))

incumbents = {a for a, c in incumbent_count.items() if c >= 4}
records = [(a, pid, m) for (a, pid, m) in records if a in incumbents]
print(f"Incumbent authors: {len(incumbents):,}")

first_llm_month = {}
ever_llm = set()
for a, pid, m in records:
    if llm_map.get(pid, 0) == 1:
        ever_llm.add(a)
        if m > '2022-12':
            if a not in first_llm_month or m < first_llm_month[a]:
                first_llm_month[a] = m

treated_authors = set(first_llm_month.keys())
control_authors = incumbents - ever_llm
print(f"Treated: {len(treated_authors):,} | Control: {len(control_authors):,}")

control_list = list(control_authors)
placebo_months = pd.period_range('2023-01', '2024-06', freq='M').astype(str).tolist()
drawn = np.random.choice(placebo_months, size=len(control_list))
for a, c in zip(control_list, drawn):
    first_llm_month[a] = c

count_map = defaultdict(int)
seen = set()
for a, pid, m in records:
    if (a, pid) in seen:
        continue
    seen.add((a, pid))
    if OBS_START <= m <= OBS_END:
        count_map[(a, m)] += 1

obs_months = pd.period_range(OBS_START, OBS_END, freq='M').astype(str).tolist()
keep_authors = treated_authors | control_authors

panel_rows = []
for a in keep_authors:
    treated = 1 if a in treated_authors else 0
    ev_idx = m2i[first_llm_month[a]]
    for m in obs_months:
        rel = m2i[m] - ev_idx
        if not (-12 <= rel <= 18) or rel == 0:
            continue
        panel_rows.append({
            'hashed_author':        a,
            'monthly_productivity': count_map.get((a, m), 0),
            'month':                m,
            'cohort':               first_llm_month[a],
            'rel_month':            rel,
            'treated':              treated,
        })

panel = pd.DataFrame(panel_rows)

for k in range(2, 13):
    panel[f"rel_month_pre_{str(k).zfill(2)}_treated"]  = ((panel['rel_month'] == -k) & (panel['treated'] == 1)).astype(int)
for k in range(1, 19):
    panel[f"rel_month_post_{str(k).zfill(2)}_treated"] = ((panel['rel_month'] == k) & (panel['treated'] == 1)).astype(int)

panel.to_csv(OUTPUT, index=False)
print(f"Saved: {OUTPUT}  ({len(panel):,} rows)")
