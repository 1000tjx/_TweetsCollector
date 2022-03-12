import pandas as pd
import os

df = pd.concat([pd.read_csv(fname, encoding='utf-8-sig')
               for fname in os.listdir(".") if not fname.startswith("all") and fname.endswith(".csv")])
dfs = []
print(df.shape)
df = df.drop_duplicates()
print(df.shape)
df.to_csv("all_data.csv", encoding='utf-8-sig', index=False)
