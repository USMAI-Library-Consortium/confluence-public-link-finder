import os
from pandas import read_excel, concat, DataFrame

files_to_parse = []

# Get file from the PageCountViews Directory
for path, _, files in os.walk("PageCountViews"):
    for file in files:
        files_to_parse.append(os.path.join(path, file))

merged_df: DataFrame = read_excel(files_to_parse[0])
for file in files_to_parse[1:]:
    df = read_excel(file)
    merged_df = concat([merged_df, df], ignore_index=True)

merged_df.to_csv("PageCountViews.csv")