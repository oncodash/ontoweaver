import pandas as pd
df = pd.read_csv('cutpath.csv')
translations_file = "./hgnc_complete_set.txt"
translations_table = pd.read_table(translations_file, sep="\t")

df['source_genesymbol'] = df['source_genesymbol'].str.upper()
df['target_genesymbol'] = df['target_genesymbol'].str.upper()

filtered_df = df[
    ((df['source_genesymbol'].isin(translations_table.symbol)) | (df.entity_type_source!="protein")) & 
    ((df['target_genesymbol'].isin(translations_table.symbol)) | (df.entity_type_target!="protein"))
]
result = (
    filtered_df.groupby(['entity_type_source', 'entity_type_target'], group_keys=False)
                .apply(lambda x: x.sample(1, random_state=1))  # Take 1 random row per group
                .reset_index(drop=True)
)
result.to_csv('path.csv', index=False)