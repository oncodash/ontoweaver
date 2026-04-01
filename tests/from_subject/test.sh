#!/usr/bin/bash

# set -e
# set -o pipefail

# if [[ -z "$1" ]] ; then
#     echo "Usage: $0 path/to/omnipath.tsv.gz [count]" >&2
#     exit 2
# fi

# count=5
# if [[ -n "$2" ]] ; then
#     count="$2"
# fi


rm -rf biocypher-*

echo "Extracting test data..." >&2
if [[ -f omnipath.tsv ]] ; then
    echo "Reuse existing 'omnipath.tsv'" >&2
else
    cp $1  omnipath.tsv.gz
    gunzip omnipath.tsv.gz
fi

if [[ -f "cutpath.csv" ]] ; then
    echo "Reuse existing 'cutpath.csv'" >&2
else
    csvcut --tabs --columns source,source_genesymbol,target_genesymbol,entity_type_source,entity_type_target,target,consensus_direction,consensus_stimulation --delete-empty-rows omnipath.tsv > cutpath.csv
fi
# From there, this is a csv

if [[ -f "path.csv" ]] ; then
    echo "Reuse existing 'path.csv'" >&2
else
    python3 -c "
    import pandas as pd
    df = pd.read_csv('cutpath.csv')
    result = (
        df.groupby(['entity_type_source', 'entity_type_target'], group_keys=False)
          .apply(lambda x: x.sample(1))  # Take 1 random row per group
          .reset_index(drop=True)
    )
    result.to_csv('path.csv', index=False)
    "
fi

echo "Weaving..." >&2
if=$(uv run ontoweave path.csv:path.yaml --type-affix suffix --biocypher-schema schema.yaml --register path.py --debug --log-level DEBUG) # 2> ontoweave.log)

# cat ontoweave.log | grep -e ERROR -e WARNING | colout ERROR | colout WARNING magenta

echo "Results" >&2
if [[ $? -eq 0 ]] ; then
    batcat --paging=never path.csv

    out=$(dirname $if)/*.csv
    batcat --paging=never $out

    echo "Number of rows in  input data: $(wc -l path.csv)" >&2
    echo "Number of rows in output data:" >&2
    wc -l $out
fi

