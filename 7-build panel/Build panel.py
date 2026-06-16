import pandas as pd
import numpy as np
from collections import defaultdict

DISAMBIG = 'disambig_clean.csv'
ALPHA = 'alpha_scores.csv'
ARXIV = 'arxiv_clean.csv'
OUTPUT = '/panel.csv'

np.random.seed(42)
PRE_START, PRE_END = '2018-01', '2021-12'
OBS_START, OBS_END = '2022-01', '2024-06'

arxiv = pd.read_csv(ARXIV, usecols=['arxiv_id', 'pub_month'], dtype={'arxiv_id': str})
arxiv['arxiv_id'] = arxiv['arxiv_id'].astype(str)
date_map = dict(zip(arxiv['arxiv_id'], arxiv['pub_month']))

alpha = pd.read_csv(ALPHA, dtype={'id': str})
alpha['id'] = alpha['id'].astype(str)
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
print(f"Incumbent authors: {len(incumbents):,}")

filtered_records = []
for a, pid, m in records:
    if a in incumbents:
        filtered_records.append((a, pid, m))
records = filtered_records

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

count_map = defaultdict(int)
seen = set()
for a, pid, m in records:
    if (a, pid) in seen:
        continue
    seen.add((a, pid))
    if OBS_START <= m <= OBS_END:
        count_map[(a, m)] += 1

obs_months = pd.period_range(OBS_START, OBS_END, freq='M').astype(str).tolist()
control_pool = list(control_authors)
n_controls = 5

stacked_rows = []
for treated_author in treated_authors:
    event_month = first_llm_month[treated_author]
    chosen_controls = np.random.choice(control_pool, size=min(n_controls, len(control_pool)), replace=False)
    cohort_authors = [treated_author] + list(chosen_controls)
    for auth in cohort_authors:
        is_treated = 1 if auth == treated_author else 0
        for m in obs_months:
            rel = int((pd.Period(m, freq='M') - pd.Period(event_month, freq='M')).n)
            if not (-12 <= rel <= 18) or rel == 0:
                continue
            stacked_rows.append({
                'hashed_author': auth,
                'monthly_productivity': count_map.get((auth, m), 0),
                'month': m,
                'cohort': event_month,
                'rel_month': rel,
                'treated': is_treated,
            })

panel = pd.DataFrame(stacked_rows)

pre_months = list(range(2, 13))
post_months = list(range(1, 19))
for k in pre_months:
    panel[f"rel_month_pre_{str(k).zfill(2)}_treated"] = ((panel['rel_month'] == -k) & (panel['treated'] == 1)).astype(int)
for k in post_months:
    panel[f"rel_month_post_{str(k).zfill(2)}_treated"] = ((panel['rel_month'] == k) & (panel['treated'] == 1)).astype(int)

panel.to_csv(OUTPUT, index=False)
print(f"Saved: {OUTPUT}  ({len(panel):,} rows)")
