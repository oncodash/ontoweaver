CHANGELOG
=========

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


[Unreleased]
------------

[v1.10.3] -- 2026-09-12
-----------------------

### Changed

- Adds the `type_of` helper function to transformers.

### Fixed

- Force value conversion to string when calling the `replace` transformer (with a warning).


[v1.10.2] -- 2026-09-04
-----------------------

### Changed

- CHANGE LICENSE FOR APACHE2 (aligns with BioCypher's license).

### Fixed

- adds the missing single letter option for sub-sampling
- merge.Append should deserialize if necessary (Was wrongly aggregating duplicate properties).


[v1.10.1] -- 2026-08-25
-----------------------

### Added

- Adds 3 new serializers:
    - `PerType`, which allows to serialize different types with different serializers.
    - `FromTransformer`, which allows to (re)use mapping transformers to serialize elements.
    - `IDWesternNameInitials`, which allows serializing first names as initials.
- The `ontoweaver.ontoweave` modules makes it easier to create ontoweave-like CLI, but with one's own fusion engine.

### Fixed

- Fix the Reduce function of the fusion engine, which was preventing a correct edges remaping in some cases.
- Fix some logging format inconsistencies.


[v1.9.2] -- 2026-08-19
----------------------

### Fixed

- Several fixes on the autoschema feature.


[v1.9.0] -- 2026-08-17
----------------------

### Added

- Adds the (long awaited) `compose` transformer, to call several transformers on the same data.
- Adds the `western_name` transformer, that extracts first/last names in an unambiguous canonical form.

### Changed

- Case manipulation transformers now operate on all space-separated words instead of the whole string.
- The `split` transformer now defaults to splitting on any space character.
- Documentation improvements.

### Fixed

- Fix a bug when using a transformer with properties as a subject.
- Deallocate element class only if it exists in the type module.
- Remove several warnings about deprecated features in dependencies.


[v1.8.13] -- 2026-07-31
-----------------------

### Changed

- Performance improvement: the congregate step is now faster, especially in cases where one have few elements, but a lot of duplicates. (Thanks to @RaphaelDeGottardi for spotting this).
- Refactor the doc building process.

### Fixed

- Fix: deallocate classes created by previous mapping calls. Fix a bug where edge properties were called again on a mapping that's called after another in the same session.
- Fix: move a superfluous log from info to debug.


[v1.8.5] -- 2026-07-21
----------------------

### Fixed

- fix bug reverse relation by @njmmatthieu in #243


[v1.8.3] -- 2026-07-20
----------------------

### Changed

- OntoWeaver now requires Python >= 3.12

### Fixed

- Allows using `reverse_relation` when also using `from_subject` in a transformer section.
- Fix an error with `on_unknown_values` in the `translate` transformer.


[v1.8.0] -- 2026-07-12
----------------------

### Added

- Allow to query JSON files from mappings.
- Adds the `Function` fusion merger (allows using any Python binary function as a fusion strategy).
- Adds the `PerProperty` fusion merger (allows selecting a fusion strategy per property).
- Allows high-level random sub-sampling for all loaded files (useful for tests).
- Show more statistics (e.g. fusions by types) at the end of an `ontoweave` run.

### Changed

- More documentation about auto-schema, fusion and a more complete tutorial.
- Better error and warnings management.
- More automation in the documentation.
- Do not use progress-bars when not in an interactive terminal.
- Refactor `MultiType*` classes code.

### Fixed

- Fix an error about OS detection under Microsoft Windows.
- Fix a documentation encoding problem under Microsoft PowerShell.
- Fix passing additional arguments while loading files with third-party functions.


[v1.6.2] -- 2026-04-21
----------------------

### Added

- Adds the maths transformer, allowing basic arithmetic operations over cell values.

### Changed

- Avoids showing large bunch of non-blocking errors in the log, instead collect them and show an excerpt when done processing.


[v1.6.1] -- 2026-04-20
----------------------

### Fixed

- FIX: allow mapping several times the same data file
    Previous implementation was keeping only the last mapping for each input data file.
    This allows calling several mappings on the same input data.
- BREAKING CHANGE: the `validate_input_data` functions now take `filename_to_mapping` as a list of tuples, instead of a dictionary.


[v1.5.2] -- 2026-04-14
----------------------

### Fixed

- fix: Nan for boolean and setting output to lower case for neo4j by @njmmatthieu in #230
- fix(from_subject): allow ignoring non-matching rows + allow conditional user-made transformers by @jdreo in #228
- fix(progress_bar/read_excel): fixes unsupported progress bar when usi… by @clairelaudy in #231


[v1.5.1] -- 2026-04-01
----------------------

### Fixed

- fix(mapping): correctly detect that a transformer is an external one.
- fix(from_subject): allow ignoring non-matching rows + allow conditional user-made transformers.
- more impactful readme.


[v1.5] -- 2026-03-23
----------------------

### Added

- New transformer: split_replace, by @njmmatthieu in #226
- Enable split transformer on multiple delimiters by @njmmatthieu in #227

### Changed

- Better management of XLSX input files.
- More informative errors and log messages.


[v1.4] -- 2026-03-09
----------------------

### Added

- ontoweave (and the underlying functions) now have a `--progress-bars` option for potentially heavy processings.

### Changed

- General improvement on the documentation, with a lot more content.


[v1.3.4] -- 2026-03-03
----------------------

### Added

- Adds the split_translate transformer by @njmmatthieu in #223
- Adds transformer.register_all, to register a whole module at once.

### Changed

- A lot of work on the documentation.

### Removed

- Remove the (useless) validate_output argument from ontoweaver.autoschema.


[v1.3.1] -- 2026-02-27
----------------------

### Fixed

- fix(replace): dealing with np.nan values for replace transformer by @njmmatthieu in #219
- Proof read of the doc by @clairelaudy in #220


[v1.3] -- 2026-02-26
--------------------

### Added

- ontoweave can now load multiple compatible data files at once, for the same mapping, with a classical "shell glob". E.G. ontoweave data/*.parquet:mapping.yaml
- OntoWeaver now has the ability to automatically extend a BioCypher schema from its mapping (useful if you don't want to type a large but straightforward set of types).
- OntoWeaver will now detect how to load data files from their extensions.
- More transformers have been added to the default list.

### Changed

- The project now uses UV as a project manager (instead of poetry).
- Errors and warnings management is quite improved, with better error and warning messages, more information and specific error codes from ontoweave.
- The documentation has been extended an improved a lot, with tutorials, a basic introduction to SKGs, and more diagrams.
- Duplicate property values encountered in the same mapping will be aggregated in a list (prior to this version, the firsts encountered were discarded).
- The split transformer can now (try to) split any data structure that would be stored within a cell. If a cell contains an iterable, it can just iterate over it. A `nested1 transformer allows to access dictionaries.
- Any transformer yielding multiple items can now be used in the subject/row section (e.g. you can split a column into multiple subjects, and it works).
- The fusion engine is updated to handle merging data structures.

### Fixed

- The boolean transformer has some fixes.


[v1.2.0] -- 2026-01-13
----------------------

### Added

- Adds a boolean transformer
- Adds new adapters: OWL, for loading populated ontology files.
- Adds new adapters: XML and JSON, to loaded structured data documents, using queries.
- Now shows all data validation error at once.

### Changed

- Switch to the uv package manager.
- Documentation update.
- Documentation for user-made transformers.
- Default property aggregation separator becomes "|".

### Fixed

- Some minor fixes.


[v1.0.0] -- 2025-12-02
----------------------

### Added

- OWL Adapter for ontologies.
- Automatic extraction of reverse edges.
- Refactoring of run functions and parsing stage.
- Detection of Null data.


[v0.2.5] -- 2025-08-06
----------------------

### Changed

- Better error management for NetworkX.
- Improved documentation.
- Wider range of Python versions accepted.


[v0.2.4_JOBIM-25] -- 2025-07-09
-------------------------------

### Added

- Adds new entry point for CLI.


[v0.2.3] -- 2025-05-19
----------------------

### Fixed

- Fixes bug with final_type usage with SimpleLabelMaker.
- Fixes bug with rowIndex usage with target type nodes.


[v0.2.2] -- 2025-05-13
----------------------

### Added

- Enables usage of `final_type` option within the `match` section of branching transformers.

### Fixed

- Fixes minor bugs.

### Changed

- Updates documentation.


[v0.2.1] -- 2025-05-05
----------------------

### Added

- Allows to enable or disable validation of outputs, enabling a faster build of graphs for larger databases.

### Fixed

- Fixes bugs with `cat_format` transformer usage.


[v0.1.3] -- 2025-03-11
----------------------

### Added

- Multi-type transformers.
- Final_type definition in YAML mappings.

### Fixed

- Fixed CLI execution errors within Poetry.
- Fixes for data validation bugs (Separator definition for data loading, OutputValidator fails, validation failing when mapping not present).
- Fixes for in memory data frame loading.
- Fixes for fusion bugs (setter functions for Edge objects)

### Changed

- Modules from tools moved to ontoweaver.
- Refactored tests to assert of OntoWeaver tuples instead of BioCypher output.
- Updated dependencies.
- Updated docs.


[v0.1.2] -- 2025-02-20
----------------------

### Added

- Data validation module using Pandera.
- Tool for conversion of OWL ontologies to BioCypher constraints.

### Changed

- Better error management.
- Updated function naming and enabled loading of in memory data frames.
- Downgrade Python to 3.12.


[v0.1.1] -- 2025-01-13
----------------------

### Fixed

- Loop until end of transformers before raising error


[v0.2.0] -- 2025-11-04
----------------------

### Added

- Introduces type branching based on value from another column.
- Adds new interfaces for defining logic of cell value extraction and type definition.
- Decouples the YAML parsing stage into three distinct steps.
- Introduces more synonyms to be used in the YAML mapping.

### Fixed

- Fixes bugs for usage of multi type transformers on subjects.

### Changed

- Updates dependencies to newest versions.
- Updates documentation.

