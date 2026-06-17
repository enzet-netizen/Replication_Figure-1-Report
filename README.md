# Replication Package for Figure 1 on Scientific Production in the Era of Large Language Models

Replicator: Enzo Tang

Original paper: Kusumegi, K., de Vaan, M., Stuart, T., & Yin, Y. (2025).
Scientific production in the era of large language models.
*Science*, 390, 1240. https://doi.org/10.1126/science.adw3000

Last updated: June 2026

---

## 数据来源
下载arXiv元数据，根据论文提供的链接（https://www.kaggle.com/datasets/Cornell-University/arxiv?resource=download）
下载arxiv数据

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

## 4.改写摘要
SM S2.1（用 GPT-3.5-turbo-0125 改写 2022 年摘要，以改写文本估计 LLM 写作的 token 分布）
SM §S4 明确承认 prompt 与超参数均未公开 ——"The resulting token distribution may vary depending on the specific language model, the prompts executed, and the hyperparameters used." 因此可照搬的只有模型、任务（改写摘要）、训练数据、 prompt。 temperature=1.5 为本复现的自主设计。

#### 1.
逐篇读取人类语料的原始摘要，调用 GPT，只保留信息骨架。
#### input文件：human_corpus.csv
#### 运行文件：rewrite_step1.py
#### output文件：step1_bullets_new.jsonl

prompt：
"The aim here is to reverse-engineer the author's writing process by taking a piece of text "
    "from a paper and compressing it into a more concise form. This process simulates how an author "
    "might distill their thoughts and key points into a structured, yet not overly condensed form. "
    "Now as a first step, first summarize the goal of the text, e.g., is it introduction, or method, "
    "results? and then given a complete piece of text from a paper, reverse-engineer it into a list "
    "of bullet points.
    
model = "gpt-3.5-turbo-0125"
max_tokens = 500
temperature = 1.5
ThreadPoolExecutor 并发 CONCURRENCY = 5（自行定义）；断点续跑（启动扫描已完成 id 跳过）；写文件加 threading.Lock。

#### 2.
逐行读取 Step 1 的要点，调用 GPT，结果保存 id、month、original、rewritten。

#### input文件：step1_bullets_new.jsonl
#### 运行文件：rewrite_step2.py
#### output文件：rewritten_abstracts_new.jsonl

prompt：
"The aim here is to reverse-engineer the author's writing process by taking a piece of text "
    "from a paper and compressing it into a more concise form. This process simulates how an author "
    "might distill their thoughts and key points into a structured, yet not overly condensed form. "
    "Now as a first step, first summarize the goal of the text, e.g., is it introduction, or method, "
    "results? and then given a complete piece of text from a paper, reverse-engineer it into a list "
    "of bullet points.

model = "gpt-3.5-turbo-0125"
max_tokens = 500
temperature = 1.5
ThreadPoolExecutor 并发 CONCURRENCY = 5(自行定义）；断点续跑（启动扫描已完成 id 跳过）；写文件加 threading.Lock。

---

## 5.分句tokenize + 构建词概率字典
SM S2.1: α 检测以句子为基本数据单位，所以算 α 之前必须先把每篇摘要切成句子、再把句子切成词，词概率用指示函数估计，分母是句子总数，待检测论文起点 2023-01，数据终点 2024-06
分词方式用正则切句 + lower().split()，正文未规定具体工具，本复现沿用论文所依据的 Liang et al.（S29/S30）的 .split() 分词逻辑，并要求与阶段 7 算 α 时保持一致。

#### input文件：rewritten_abstracts_new.jsonl, arxiv_clean.csv
#### 运行文件：corpus_building.py
#### output文件：human_sentences.parquet, ai_sentences.parquet, inference_data.parquet, Word.parquet
从 arxiv_clean.csv 中筛选发表月份在 2022-01 至 2022-10 的论文，按月份分组，每个月用固定随机种子随机抽取 2,000 篇，共 10 个月一共20000篇。取每篇的原始 abstract 字段作为人类写作的真实样本，写入 human_corpus.csv。

脚本先定义两个工具函数。split_sentences 用正则 (?<=[.!?])\s+ 把一段文字按句号、问号、感叹号切成若干句子。tokenize 把一个句子先全部转小写，再按空格 .split() 切成词列表。逐行读取 rewritten_abstracts_new.jsonl，取每条记录的 original 字段。对每篇摘要先 split_sentences 切句，再对每句 tokenize 分词，只保留词数大于 1 的句子。所有句子汇总后，以"空格连接的句子字符串"形式存进 human_sentences.parquet。这批句子代表人类写作，用来估计人类词频分布。读同一个文件，但取每条记录的 rewritten 字段，同样切句、分词、保留词数大于 1 的句子，存进 ai_sentences.parquet。这批句子代表 LLM 写作，用来估计 AI 词频分布。从 arxiv_clean.csv 读全部论文，筛出发表月份在 2023-01 至 2024-06的论文。对筛出的每一篇，切句分词，每篇保留三个字段：论文 id、发表月份 month、以及这篇摘要的句子列表。结果存进 inference_data.parquet，约 218,634 篇。

对每个句子先用 set(sent) 去重，再数每个词在多少个句子里出现过。分别对人类句子和 AI 句子统计，得到 human_counts 和 ai_counts。estimate_log_probs 把每个词的出现次数除以句子总数、取对数，得到该词在人类语料里的对数概率和在 AI 语料里的对数概率。只保留满足三个条件的词：人类语料和 AI 语料里都出现过，在人类句子里出现 ≥ 5 次，在AI 句子里出现 ≥ 3 次。三个条件取交集得到最终词表 vocab。这一步是为了剔除只在某一方零星出现、统计不可靠的低频词，沿用 Liang et al. 实现的设定。calculate_log_probability对词表里每个词，算出四个值并存进 Word.parquet：logP、log(1-P)、logQ、log(1-Q)。
OOV=-13.8、<3句剔除、L-BFGS-B 为 Liang et al.(S29/S30) 官方实现细节

---
## 6.计算 α
SM §S2.1：α 由混合分布的极大似然估计得到,we define α₀ = 0.1 ... A paper is classified as LLM-assisted if it (i.) is posted after Dec 2022; and (ii.) registers an α > α₀
#### input文件：Word.parquet, inference_data.parquet
#### 运行文件：compute_alpha.py
#### output文件：alpha_scores.csv

读入 Word.parquet，把每个词的 logP、log(1-P)、logQ、log(1-Q) 装进字典。对 inference_data.parquet 的每篇论文，每个句子先取词集合（set，对应指示函数），只保留词表内词数 > 1 的句子，sentence_logP_logQ 算该句在人类分布和 AI 分布下的对数似然（句内出现的词加 logP/logQ，未出现的词表词补 log(1-P)/log(1-Q)，词表外 OOV 统一取 −13.8，沿用 Liang 实现，有效句子 < 3 句的论文返回 NaN（防 MLE 边界塌缩）；其余用 scipy L-BFGS-B 在 α∈[0,1] 上最小化负对数似然 −mean(log((1−α)+α·exp(logQ−logP)))，得到每篇的 α。判定 is_llm = (α > 0.1)，日期条件（posted after Dec 2022）由 

---

## 7.构建panel

#### input文件：disambig_clean.csv, alpha_scores.csv, arxiv_clean.csv
#### 运行文件：build_panel.py
#### output文件：panel.csv

作者email:
"Active periods: see S2.3 “For each author, we track the number of preprints they posted each month,” so the panel is not conditioned on active publication periods.
Control construction: see S2.4 “Each author in this group is assigned a unique event time,” so control observations are not reused.
Hope this clarifies the design. We’re also aware of other groups that have independently replicated the pattern without clear pre-trends, following the paper and SM."


| # | 实现 | 原文 |
|---|---|---|
| 1 | incumbent = 2018-01~2021-12 发文 ≥4 篇 | S2.3 "researchers with at least 4 works published between 2018 and 2021" |
| 2 | 观测窗 2022-01~2024-06，零产出月记 0 保留 | S2.3 "the number of preprints they posted each month during a 30-month period (Jan 2022 - June 2024) |
| 3 | treated = 第一篇 is_llm 论文的月份 | S2.4 "treatment time as the author's first month of LLM adoption" |
| 4 | control = incumbents − ever_llm | S2.4 "never-treated authors–those with no LLM-assisted publications as of June 2024" |
| 5 | placebo 在 2023-01~2024-06 均匀随机，seed=42 | S2.4 "assigned a unique event time, randomly drawn between January 2023 and June 2024" |
| 6 | 事件窗 −12~+18，排除 τ=0，参照期 τ=−1 | 3.1 "we exclude the month of treatment"、"D^k for k ≥ −1 |
| 7 | control 只进 stack 一次 | 作者email回信 |

---

## 8.回归
作者提供回归和生图代码：https://figshare.com/articles/dataset/Scientific_production_in_the_era_of_Large_Language_Models/30359437

#### input文件：panel.csv
#### 运行文件：regression.do
#### output文件：fig1A_productivity.pdf，coefs_stata.csv

<img width="808" height="475" alt="image" src="https://github.com/user-attachments/assets/dcdec330-53fa-48b4-844b-b79f5cff7651" />

## 8.生图
#### input文件：coefs_stata.csv
#### 运行文件：rplot.do
#### output文件：fig1.pdf


