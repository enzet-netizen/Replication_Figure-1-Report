
import pandas as pd
import ast
from collections import defaultdict
import csv

INPUT  = 'arxiv_clean.csv'
OUTPUT = 'disambig_clean.csv'

COLLAB_KEYWORDS = {
    'collaboration', 'consortium', 'team', 'group', 'project','survey', 'observatory', 'telescope', 'experiment', 'institute',
    'laboratory', 'center', 'centre', 'university', 'department','committee', 'society', 'network', 'mission', 'facility','detector', 'foundation', 'association', 'council', 'agency',
    'corporation', 'company', 'collab.',
}


def get_all_major_categories(categories_str):
    if not categories_str or pd.isna(categories_str):
        return {'unknown'}
    majors = set()
    for cat in str(categories_str).strip().split():
        majors.add(cat.split('.')[0])
    return majors


def is_collaboration(last, first):
    text = (str(last) + ' ' + str(first)).lower()
    for kw in COLLAB_KEYWORDS:
        if kw in text:
            return True
    return False


df = pd.read_csv(INPUT)
papers_by_subject = defaultdict(list)
for i, row in enumerate(df.itertuples(), 1):
    if i % 100_000 == 0:
        print(f"Processed:  {i:,} / {len(df):,}")
    try:
        authors = ast.literal_eval(row.authors_parsed)
    except Exception:
        continue
    paper_id = str(row.arxiv_id)
    for subject in get_all_major_categories(row.categories):
        papers_by_subject[subject].append((paper_id, authors))

index = defaultdict(list)
for subject in sorted(papers_by_subject.keys()):
    for paper_id, authors in papers_by_subject[subject]:
        for entry in authors:
            last  = entry[0].strip() if len(entry) > 0 else ''
            first = entry[1].strip() if len(entry) > 1 else ''
            if not last:
                continue
            index[(subject, last, first)].append(paper_id)


removed_1letter = 0
removed_numpunct = 0
removed_collab = 0
clean_rows = []

for (subject, last, first), paper_ids in sorted(index.items()):
    if len(last) <= 1:
        removed_1letter += 1
        continue

    if (last and not last[0].isalpha()) or (first and not first[0].isalpha()):
        removed_numpunct += 1
        continue

    if is_collaboration(last, first):
        removed_collab += 1
        continue

    clean_rows.append((subject, last, first, len(paper_ids), '|'.join(paper_ids)))

print(f"letter: {removed_1letter:,}")
print(f" numpunct: {removed_numpunct:,}")
print(f"collab: {removed_collab:,}")
print(f"kept:  {len(clean_rows):,}")


with open(OUTPUT, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['subject', 'last', 'first', 'paper_count', 'paper_ids'])
    for r in clean_rows:
        writer.writerow(r)

