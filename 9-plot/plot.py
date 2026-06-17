import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

COEFS  = 'coefs_stata.csv'
OUTPUT = 'fig1.png'

ORANGE ='#E87D3E'  

coefs = pd.read_csv(COEFS)
col_name = coefs.columns[0]
col_est  = 'Estimate'
col_se   = 'Std. Error'

rows = []
for _, r in coefs.iterrows():
    name = str(r[col_name])
    if 'rel_month_pre_' in name:
        k = int(name.split('pre_')[1][:2])
        rows.append((-k, r[col_est], r[col_se]))
    elif 'rel_month_post_' in name:
        k = int(name.split('post_')[1][:2])
        rows.append((k, r[col_est], r[col_se]))

df = pd.DataFrame(rows, columns=['rel_month', 'beta', 'se'])
df = pd.concat([df, pd.DataFrame([{'rel_month': -1, 'beta': 0.0, 'se': 0.0}])])
df = df.sort_values('rel_month').reset_index(drop=True)

df['pct']    = (np.exp(df['beta']) - 1) * 100
df['pct_lo'] = (np.exp(df['beta'] - 1.96 * df['se']) - 1) * 100
df['pct_hi'] = (np.exp(df['beta'] + 1.96 * df['se']) - 1) * 100

fig, ax = plt.subplots(figsize=(10, 6))

ax.yaxis.grid(True, color='#CCCCCC', linewidth=0.8)
ax.set_axisbelow(True)

ax.axhline(0, color='black', linewidth=1.8, zorder=2)
ax.axvline(0, color='black', linestyle='--', linewidth=1.2, zorder=2)

ax.errorbar(df['rel_month'], df['pct'],
            yerr=[df['pct'] - df['pct_lo'], df['pct_hi'] - df['pct']],
            fmt='o', color=ORANGE, ecolor=ORANGE,
            markersize=7, capsize=0, elinewidth=1.5, zorder=3,
            label='Difference between LLM adopters and nonadopters')

from matplotlib.lines import Line2D
handles = [
    Line2D([0], [0], marker='o', color='none', markerfacecolor=ORANGE,
           markersize=8, label='Difference between LLM adopters and nonadopters'),
    Line2D([0], [0], color=ORANGE, linewidth=1.5, label='95% confidence interval'),
]
ax.legend(handles=handles, loc='lower left', bbox_to_anchor=(0, 1.02),
          ncol=2, frameon=False, fontsize=10, handletextpad=0.5, columnspacing=1.5)

ax.set_xlabel('Months relative to first adoption', fontsize=12, fontweight='bold')
ax.set_ylabel('Change in author productivity (%)', fontsize=12, fontweight='bold')

ax.set_xticks([-12, -6, 0, 6, 12, 18])
ax.set_yticks([-25, 0, 25, 50, 75])
ax.set_xlim(-13, 18.8)
ax.set_ylim(-30, 80)

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.tight_layout()
plt.savefig(OUTPUT, dpi=300, bbox_inches='tight')

