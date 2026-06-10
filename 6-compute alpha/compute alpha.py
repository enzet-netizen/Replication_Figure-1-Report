import pandas as pd
import numpy as np
import json
from scipy.optimize import minimize

WORD_FILE = 'Word.parquet'
INF_FILE  = 'inference_data.parquet'
OUTPUT    = 'alpha_scores.csv'

word_df = pd.read_parquet(WORD_FILE)
all_tokens  = set(word_df['Word'].tolist())
log_p_hat   = dict(zip(word_df['Word'], word_df['logP']))
log_q_hat   = dict(zip(word_df['Word'], word_df['logQ']))
log_1mp_hat = dict(zip(word_df['Word'], word_df['log1-P']))
log_1mq_hat = dict(zip(word_df['Word'], word_df['log1-Q']))
total_log_1mp = sum(log_1mp_hat.values())
total_log_1mq = sum(log_1mq_hat.values())
OOV = -13.8


def sentence_logP_logQ(tokens_set):
    logP = sum(log_p_hat.get(t, OOV) for t in tokens_set) + \
           (total_log_1mp - sum(log_1mp_hat[t] for t in tokens_set if t in all_tokens))
    logQ = sum(log_q_hat.get(t, OOV) for t in tokens_set) + \
           (total_log_1mq - sum(log_1mq_hat[t] for t in tokens_set if t in all_tokens))
    return logP, logQ


def neg_log_likelihood(alpha, log_p_values, log_q_values):
    a = alpha[0]
    ll = np.mean(np.log((1 - a) + a * np.exp(log_q_values - log_p_values)))
    return -ll


def estimate_alpha(sentences):
    logP_list, logQ_list = [], []
    for sent in sentences:
        toks = set(t for t in sent if t in all_tokens)
        if len(toks) > 1:
            lp, lq = sentence_logP_logQ(toks)
            logP_list.append(lp)
            logQ_list.append(lq)
    if len(logP_list) < 3:
        return np.nan
    result = minimize(neg_log_likelihood, x0=[0.5],
                      args=(np.array(logP_list), np.array(logQ_list)),
                      method='L-BFGS-B', bounds=[(0, 1)])
    return result.x[0] if result.success else np.nan


inf = pd.read_parquet(INF_FILE)
print(f"Papers to process: {len(inf):,}")

results = []
for i, row in enumerate(inf.itertuples()):
    sents = [s.split() for s in json.loads(row.sentences)]
    alpha = estimate_alpha(sents)
    is_llm = 1 if (not np.isnan(alpha) and alpha > 0.1 and row.month > '2022-12') else 0
    results.append({'id': row.id, 'month': row.month,
                    'alpha': round(alpha, 4) if not np.isnan(alpha) else np.nan,
                    'is_llm': is_llm})
    if (i + 1) % 5000 == 0:
        print(f"  {i+1:,} / {len(inf):,}")

alpha_df = pd.DataFrame(results)
alpha_df.to_csv(OUTPUT, index=False)
print(f"\nSaved: {OUTPUT}")
print(f"LLM-assisted rate: {alpha_df['is_llm'].mean()*100:.1f}%")