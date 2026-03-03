#!/usr/bin/env sh
rm -rf doc_built
uv run sphinx-build --builder html docs/ doc_built $*
