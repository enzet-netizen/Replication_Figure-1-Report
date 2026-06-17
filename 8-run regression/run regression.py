import pandas as pd
import pyfixest as pf
import os

INPUT  = 'panel.csv'
OUTPUT_COEFS = 'coefs.csv'

panel = pd.read_csv('panel.csv',
                    dtype={'hashed_author': str, 'cohort': str, 'month': str})
print(f"  {len(panel):,} rows")

for k in range(2, 13):
    panel[f"rel_month_pre_{str(k).zfill(2)}_treated"]  = ((panel['rel_month'] == -k) & (panel['treated'] == 1)).astype('int8')
for k in range(1, 19):
    panel[f"rel_month_post_{str(k).zfill(2)}_treated"] = ((panel['rel_month'] == k) & (panel['treated'] == 1)).astype('int8')

pre_cols  = [f"rel_month_pre_{str(k).zfill(2)}_treated"  for k in range(2, 13)]
post_cols = [f"rel_month_post_{str(k).zfill(2)}_treated" for k in range(1, 19)]
rhs_cols  = pre_cols + post_cols

fml = f"monthly_productivity ~ {' + '.join(rhs_cols)} | hashed_author^cohort + month^cohort"

fit = pf.fepois(data=panel, fml=fml, vcov={'CRV1': 'hashed_author'})
coefs = fit.tidy().reset_index()
coefs.to_csv('coefs.csv', index=False)

