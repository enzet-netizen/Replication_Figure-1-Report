
import json
import pandas as pd

INPUT  = '/arxiv-metadata-oai-snapshot.json'
OUTPUT = '/arxiv_clean.csv'

def get_v1_month(record):
    versions = record.get('versions')
    raw_date = None
    if versions and len(versions) > 0:
        raw_date = versions[0].get('created')
    if raw_date is None:
        raw_date = record.get('created')
    if raw_date is None:
        return None
    try:
        dt = pd.to_datetime(raw_date)
        return dt.strftime('%Y-%m')
    except Exception:
        return None

AI_CATEGORIES = {'cs.CV', 'cs.LG', 'cs.AI', 'cs.IR', 'cs.CL'}  
def has_ai_category(categories_str):
    if not categories_str:
        return False
    cats = set(categories_str.split())
    return len(cats & AI_CATEGORIES) > 0


def main():
    rows = []
    n_total = 0
    n_in_window = 0

    with open(INPUT, 'r') as f:
        for line in f:
            n_total += 1
            if n_total % 200000 == 0:
                print(f"Processed: {n_total:,}")

            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue

            pub_month = get_v1_month(rec)
            if pub_month is None:
                continue

            if not ('2018-01' <= pub_month <= '2024-06'):
                continue
            n_in_window += 1

            categories = rec.get('categories', '')
            if has_ai_category(categories):
                continue

            rows.append({
                'arxiv_id':  rec.get('id'),
                'doi':       rec.get('doi'),
                'title':     (rec.get('title') or '').replace('\n', ' ').strip(),
                'abstract':  (rec.get('abstract') or '').replace('\n', ' ').strip(),
                'pub_month': pub_month,
                'categories': categories,
                'authors_parsed': json.dumps(rec.get('authors_parsed', [])),
            })

    print(f" 2018-2024: {n_in_window:,}")
    print(f" kept: {len(rows):,}")

    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT, index=False)
  
if __name__ == '__main__':
    main()