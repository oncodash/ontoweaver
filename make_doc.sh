#!/usr/bin/env sh
rm -rf doc_built

echo "Extract keywords" >&2
keywords="$(./docs/keywords_from_code.py)"
echo "$keywords" >&2
cat docs/sections/mapping_api.TPL.rst | sed "s/{{{KEYWORDS}}}/$keywords/g" > docs/sections/mapping_api.rst
echo "Done" >&2

uv run sphinx-build --builder html docs/ doc_built $*
