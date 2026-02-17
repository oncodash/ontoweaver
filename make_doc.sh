#!/usr/bin/env sh
rm -rf doc_built
uv run sphinx-build -M html docs/ doc_built
