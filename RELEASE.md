How to release OntoWeaver:

1. Edit `pyproject.toml` and change the `version` field.
2. Tag the version with `git tag` and `git push --tags`.
3. Check that the continuous deployment action ended gracefully on [Github/CD](https://github.com/oncodash/ontoweaver/actions)]
4. Check that the package exists on [PyPi](https://pypi.org/manage/project/ontoweaver/releases/)
5. Check that the version is being buit on [RTD](https://app.readthedocs.org/dashboard/ontoweaver/builds)
6. Once done, create the corresponding doc version exists on: https://ontoweaver.readthedocs.io/en/<tag>

