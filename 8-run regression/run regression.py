import pandas as pd
import pyfixest as pf

INPUT = 'panel.csv'
OUTPUT_COEFS = 'coefs.csv'


panel = pd.read_csv(INPUT)

pre_cols  = [f"rel_month_pre_{str(k).zfill(2)}_treated"  for k in range(2, 13)]  
post_cols = [f"rel_month_post_{str(k).zfill(2)}_treated" for k in range(1, 19)]  
rhs_cols  = pre_cols + post_cols

fml = f"monthly_productivity ~ {' + '.join(rhs_cols)} + C(rel_month) | hashed_author + month"

fit = pf.fepois(data=panel, fml=fml, vcov={'CRV1': 'hashed_author'})

coefs = fit.tidy().reset_index()
coefs.to_csv(OUTPUT_COEFS, index=False)
print(f"Saved: {OUTPUT_COEFS}")
