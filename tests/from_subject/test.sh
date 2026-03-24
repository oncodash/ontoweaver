#!/usr/bin/bash

set -e
# set -o pipefail

if [[ -z "$1" ]] ; then
    echo "Usage: $0 path/to/omnipath.tsv.gz [count]" >&2
    exit 2
fi

count=5
if [[ -n "$2" ]] ; then
    count="$2"
fi


rm -rf biocypher-*

if [[ -f omnipath.tsv ]] ; then
    echo "Reusing existing data" >&2
else
    cp $1  omnipath.tsv.gz
    gunzip omnipath.tsv.gz
fi

echo "Extracting test data..." >&2
csvcut --tabs --columns source,source_genesymbol,target_genesymbol,entity_type_source,entity_type_target,target,consensus_direction,consensus_stimulation --delete-empty-rows omnipath.tsv > cutpath.csv
# From there, this is a csv

csvgrep --columns entity_type_target --match protein  cutpath.csv | head -n $count >> path.csv
csvgrep --columns entity_type_target --match complex  cutpath.csv | head -n $count >> path.csv

csvgrep --columns entity_type_source --match protein  cutpath.csv | head -n $count >> path.csv
csvgrep --columns entity_type_source --match complex  cutpath.csv | head -n $count >> path.csv

echo "Weaving..." >&2
if=$(uv run ontoweave path.csv:path.yaml --biocypher-schema schema.yaml  --register path.py --debug --log-level DEBUG)

echo "Results" >&2
if [[ $? -eq 0 ]] ; then
    batcat --paging=never path.csv

    out=$(dirname $if)/*.csv
    batcat --paging=never $out

    echo "Number of rows in  input data: $(wc -l path.csv)" >&2
    echo "Number of rows in output data:" >&2
    wc -l $out
fi

