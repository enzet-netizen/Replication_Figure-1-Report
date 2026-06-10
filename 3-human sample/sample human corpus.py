import pandas as pd

INPUT  = 'arxiv_clean.csv'
OUTPUT = 'human_corpus.csv'

SAMPLES_PER_MONTH = 2000
TARGET_MONTHS = [f"2022-{str(i).zfill(2)}" for i in range(1, 11)]  
SEED = 42

df = pd.read_csv(INPUT)
df_2022 = df[df['pub_month'].isin(TARGET_MONTHS)]
sampled = []
for month in TARGET_MONTHS:
    month_df = df_2022[df_2022['pub_month'] == month]
    n = min(SAMPLES_PER_MONTH, len(month_df))
    s = month_df.sample(n=n, random_state=SEED)
    sampled.append(s)
    print(f" {month}: {n}")

work_df = pd.concat(sampled).reset_index(drop=True)
out = work_df.rename(columns={'arxiv_id': 'id', 'pub_month': 'month'})[['id', 'month', 'abstract']]
out.to_csv(OUTPUT, index=False)

print(f"\nTotal human corpus: {len(out):,} ")
