import pandas as pd
import numpy as np
from collections import Counter
import json
import re

INPUT = 'rewritten_abstracts_new.jsonl'
ARXIV = 'arxiv_clean.csv'
BASE  = ''

INFER_START = '2023-01'
INFER_END   = '2024-06'

def split_sentences(text):
    return re.split(r'(?<=[.!?])\s+', str(text).strip())

def tokenize(sent):
    return sent.lower().split()

human_sentences = []
ai_sentences = []
with open(INPUT) as f:
    for line in f:
        try:
            rec = json.loads(line)
        except:
            continue
        for sent in split_sentences(rec['original']):
            toks = tokenize(sent)
            if len(toks) > 1:
                human_sentences.append(toks)
        for sent in split_sentences(rec['rewritten']):
            toks = tokenize(sent)
            if len(toks) > 1:
                ai_sentences.append(toks)

pd.DataFrame({'sentence': [' '.join(s) for s in human_sentences]}).to_parquet(f'{BASE}/human_sentences.parquet', index=False)
pd.DataFrame({'sentence': [' '.join(s) for s in ai_sentences]}).to_parquet(f'{BASE}/ai_sentences.parquet', index=False)

adf = pd.read_csv(ARXIV, dtype=str)
infer = adf[(adf['pub_month'] >= INFER_START) & (adf['pub_month'] <= INFER_END)]
print(f"Inference papers: {len(infer):,}")

rows = []
for i, row in enumerate(infer.itertuples(), 1):
    if i % 50000 == 0:
        print(f"    {i:,} / {len(infer):,}")
    sents = []
    for sent in split_sentences(row.abstract):
        toks = tokenize(sent)
        if len(toks) > 1:
            sents.append(' '.join(toks))
    rows.append({'id': str(row.arxiv_id), 'month': row.pub_month,
                 'sentences': json.dumps(sents)})

pd.DataFrame(rows).to_parquet(f'{BASE}/inference_data.parquet', index=False)

def count_binary(sentences):
    return dict(Counter(word for sent in sentences for word in set(sent)))

def estimate_log_probs(word_counts, total_sents):
    return {w: np.log(c / total_sents) for w, c in word_counts.items()}

def calculate_log_probability(human_probs, ai_probs, common_vocab):
    data = []
    for word in common_vocab:
        log_h = human_probs.get(word, -np.inf)
        log_a = ai_probs.get(word, -np.inf)
        log_1mh = np.log1p(-np.exp(log_h))
        log_1ma = np.log1p(-np.exp(log_a))
        lor = (log_h - log_1mh) - (log_a - log_1ma)
        if np.isinf(lor) or np.isnan(lor):
            continue
        data.append({"Word": word, "logP": log_h, "log1-P": log_1mh,
                     "logQ": log_a, "log1-Q": log_1ma, "Log Odds Ratio": lor})
    df = pd.DataFrame(data).sort_values('Log Odds Ratio').reset_index(drop=True)
    return df.drop(columns=['Log Odds Ratio'])

human_counts = count_binary(human_sentences)
ai_counts    = count_binary(ai_sentences)
n_human = len(human_sentences)
n_ai    = len(ai_sentences)

human_logp = estimate_log_probs(human_counts, n_human)
ai_logp    = estimate_log_probs(ai_counts, n_ai)

common = set(human_counts) & set(ai_counts)
freq_h = {w for w, c in human_counts.items() if c >= 5}
freq_a = {w for w, c in ai_counts.items() if c >= 3}
vocab  = common & freq_h & freq_a

df = calculate_log_probability(human_logp, ai_logp, vocab)
df.to_parquet(f'{BASE}/Word.parquet', index=False)
