#!/usr/bin/env bash

if [[ -z $READTHEDOCS_OUTPUT ]] ; then
    READTHEDOCS_OUTPUT="doc_built"
fi

echo "Remove output directory: $READTHEDOCS_OUTPUT" >&2
rm -rf $READTHEDOCS_OUTPUT

echo "Extract keywords" >&2
keywords="$(./docs/keywords_from_code.py)"
echo "$keywords" >&2
cat docs/sections/mapping_api.TPL.rst | sed "s/{{{KEYWORDS}}}/$keywords/g" > docs/sections/mapping_api.rst
echo "Done" >&2

uv run sphinx-build --builder html docs/ $READTHEDOCS_OUTPUT $*

