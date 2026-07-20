How to release OntoWeaver:

1. Edit `pyproject.toml` and change the `version` field.
2. Backport any Python version change in `.readthedocs.yaml .github/actions/setup/action.yaml .github/actions/install/action.yaml .github/workflows/publish.yaml`
3. Commit this edited version.
4. Tag the version with `git tag` and `git push --tags`.
5. Check that the continuous deployment action ended gracefully on [Github/CD](https://github.com/oncodash/ontoweaver/actions)]
6. Check that the package exists on [PyPi](https://pypi.org/manage/project/ontoweaver/releases/)
7. Check that the version is being buit on [RTD](https://app.readthedocs.org/dashboard/ontoweaver/builds)
8. Once done, create the corresponding doc version exists on: https://ontoweaver.readthedocs.io/en/<tag>

