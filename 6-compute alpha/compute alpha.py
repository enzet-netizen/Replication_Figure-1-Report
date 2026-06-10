"""
阶段 7：逐篇论文 α 的 MLE 估计
SM §S2.1:
  - α 由混合分布 P̂_α = (1-α)P̂_H + αP̂_AI 的极大似然估计得到，句子为数据点
  - α₀ = 0.1；LLM-assisted = (i) posted after Dec 2022 且 (ii) α > α₀
    (本脚本显式加日期门控双保险；inference 窗口本身已是 2023-01~2024-06)
OOV=-13.8、<3句剔除、L-BFGS-B 为 Liang et al.(S29/S30) 官方实现细节
"""

import pandas as pd
import numpy as np
import json
from scipy.optimize import minimize

WORD_FILE = '/Users/enzotang/Desktop/project replication 2/ex/Word.parquet'
INF_FILE  = '/Users/enzotang/Desktop/project replication 2/ex/inference_data.parquet'
OUTPUT    = '/Users/enzotang/Desktop/project replication 2/ex/alpha_scores.csv'

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
    """sentences: list of token-lists"""
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
    # 衔接修复①：sentences 列是 JSON 字符串，每句是空格连接的字符串 -> 拆回 token 列表
    sents = [s.split() for s in json.loads(row.sentences)]
    alpha = estimate_alpha(sents)
    # 显式双重门控(SM §S2.1)：alpha>0.1 且 posted after Dec 2022
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