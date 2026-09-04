How to release OntoWeaver:

1. Edit `pyproject.toml` and change the `version` field.
2. Backport any Python version change in:
    - `.readthedocs.yaml`
    - `.github/actions/setup/action.yaml`
    - `.github/actions/install/action.yaml`
    - `.github/workflows/publish.yaml`
3. Edit CHANGELOG.md with the changes.
4. Commit this edited version.
5. Check that the continuous deployment test action ended gracefully on [Github/CD](https://github.com/oncodash/ontoweaver/actions)]
6. Tag the version with `git tag` and `git push --tags`.
7. Check that the package has been uploaded on [PyPi](https://pypi.org/manage/project/ontoweaver/releases/)
8. Check that the version is being built on [RTD](https://app.readthedocs.org/dashboard/ontoweaver/builds)
9. Once done, check the corresponding doc: https://ontoweaver.readthedocs.io/en/<tag>
10. Copy/paste the last CHANGELOG section in Github's release page.

