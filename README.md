# Replication Package for Figure 1 on Scientific Production in the Era of Large Language Models

**Replicator:** Enzo Tang
**Original paper:** Kusumegi, K., de Vaan, M., Stuart, T., & Yin, Y. (2025).
Scientific production in the era of large language models.
*Science*, 390, 1240. https://doi.org/10.1126/science.adw3000
**Last updated:** June 2026

---

## 数据来源
下载arXiv元数据，根据论文提供的链接（https://www.kaggle.com/d	atasets/Cornell-University/arxiv?resource=download）下载arxiv数据

---

## 1.数据清洗

#### input文件：arxiv-metadata-oai-snapshot.json
#### 运行文件：data_cleaning.py
#### output文件：arxiv_clean.csv，保留数据共860,421篇，符合论文859k数据  

| # | 清洗内容 | 来源 | 保留的数据量 |
|---|---|---|---|
| 1 | 时间窗口过滤，只保留2018-01到2024-06的论文 | SM1.1 | 1,170,473 |
| 2 | 剔除 AI 类论文 | SM1.1 | 860,421 |

---


## 2.作者姓名消歧，去噪
#### input文件：arxiv_clean.csv
#### 运行文件：name_disambig.py
#### output文件：disambig_clean.csv

逐篇论文，从 authors_parsed 字段取出每个作者的 last name 和 first name，从 categories 字段取学科大类作为 subject。把三者拼成 (subject, last, first) 三元组，作为唯一作者键。同一个人若跨学科发文会被拆成多个键。把每个作者键对应的论文 ID 聚合起来。

在聚合好的作者条目上依次删除三类噪声（删除数为去重后的作者条目数）

| # | 去噪内容 | 去除掉的数据量 |
|---|---|---|
| 1 | last name只含有一个字母 | 2250 |
| 2 | 数字/标点开头 | 1145 |
| 3 | 名字带有合作组（last或first含任一合作组关键词判为合作组） | 1749 |

去噪后，最终保留1,699,920

---


## 3.人类语料抽样
SM2.1: randomly selecting 2,000 papers each month from January 2022 to October 2022,used the original abstracts to estimate the token distribution of human-written text
#### input文件：arxiv_clean.csv
#### 运行文件：sample human corpus.py
#### output文件：human_corpus.csv  

从 arxiv_clean.csv 中筛选发表月份在 2022-01 至 2022-10 的论文，按月份分组，每个月用固定随机种子随机抽取 2,000 篇，共 10 个月一共20000篇。取每篇的原始 abstract 字段作为人类写作的真实样本，写入 human_corpus.csv。

---




## Methodological Notes and Deviations

1. **Rewrite prompt.** The original paper does not disclose its
   GPT rewrite prompt (acknowledged in SM §S4). This replication
   uses a two-step compress–expand prompt with `temperature=1.5`.
2. **Incumbent author count.** This replication identifies ~157K
   incumbent authors versus the paper's 302,474. Three candidate
   explanations were tested and ruled out (see `docs/diagnostics.md`);
   the gap is attributed to unpublished upstream name-parsing choices.
3. **Residual pre-trend.** A mild negative pre-trend remains,
   consistent with the detector-lag mechanism the paper itself
   documents (SM §S5.2–S5.3).

## References

Liang, W., et al. (2024). Monitoring AI-modified content at scale. *ICML*.
