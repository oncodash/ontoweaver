.. _ontoweave:

Usage
-----

What OntoWeaver actually does is to automatically generate a working "adapter"
for BioCypher, and then call it for you.

The output of the execution of the adapter is thus what BioCypher is
providing (see `BioCypher’s documentation <https://biocypher.org>`__).
In a nutshell, the output is a script file that, when executed, will
populate the configured database. By default, the output script file is
saved in a subdirectory of ``./biocypher-out/``, which name is a
timestamp from when the adapter has been executed.

To configure your data mapping, you will have to first define the
mapping that you want to apply on your data. Then, you will need a
BioCypher configuration file (which mainly indicate your ontology and
backend). Optionally, you may need a schema configuration file
(indicating which node and edge types you want).

To actually do something, you need to run OntoWeaver mapping onto your
data. We provide a command line interface to do so, called
``ontoweave``.

To do so, you need to prepare at least a mapping file (usually ``mapping.yaml``),
and a Biocypher configuration file (usually ``biocypher_config.yaml``).

You will find all the options by running the help command:

.. code:: sh

   ontoweave --help


Simplest case
~~~~~~~~~~~~~

If your config file is named ``biocypher_config.yaml`` and if you do not already
have your own schema, OntoWeaver can generate it for you from the mapping:

.. code:: sh

   ontoweave --auto-schema autoschema.yaml my_data.csv:my_mapping.yaml


User-made schema
~~~~~~~~~~~~~~~~

If you have your own schema (in ``schema.yaml``) —for instance if you manually
extended your ontology— the simplest call would be:

.. code:: sh

   ontoweave my_data.csv:my_mapping.yaml


Extending a basic schema
~~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 1.3

Manually extending your types hierarchy can be as simple as adding a node class
in the schema file. BioCypher will then assemble a new taxonomy and use it.

To do so, BioCypher requires that you specify that the new class ``is_a``
existing parent class. For instance, you can prepare a ``basic_schema.yaml``
file:

.. code:: yaml

   my_class:  # Your new class, extending the ontology's taxonomy.
       is_a: parent_class  # parent_class is already in the ontology file.

However, BioCypher requires that you give it a full schema, with all the class
that your data are using. This schema file can be quite long and cumbersome
to write down if you plan to use the ontology without more tuning.
Fortunately, OntoWeaver can extend the schema for you, based on your mapping.
In that case, you will have to call:

.. code:: sh

   ontoweave --biocypher-schema basic_schema --auto-schema extended_schema.yaml my_data.csv:my_mapping.yaml

OntoWeaver will create the ``extended_schema.yaml`` file, which contains
both the content of ``basic_schema.yaml`` and the generated classes.


Specific configuration
~~~~~~~~~~~~~~~~~~~~~~

If you want to indicate your own configuration files, pass their name as
options:

.. code:: sh

   ontoweave --biocypher-config my_biocypher_config.yaml --biocypher-schema my_schema.yaml data-1.1.csv:map-1.yaml data-1.2.csv:map-1.yaml data-A.csv:map-A.yaml

.. note::

   You can use the same mapping on several data files!
   And/or you can use several mappings.


Multiple data files at once
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. include:: ./glob.rst


Pass parameters when loading data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can pass additional parameters to the function that loads the input data
file, by appending a JSON dictionary of named parameters to the input data
filename.

For example:

.. code:: sh

    # Change the default separator:
    ontoweave 'data.csv{"sep":";"}:mapping.yaml'
    # This will parse the data file as having columns separated by a semi-colon.
    # See below for the default parameters.

The parameters you can pass depends on the underlying loader function that is
used to load the file (most probably a *Pandas* ``read_*`` function, see below).
OntoWeaver will choose the loader function depending on the extension of the
input data file.

.. warning::

    The JSON dictionary of parameters SHOULD NOT contain space,
    and MUST BE  double-quoted.

.. hint::

    In most shells (like Bash or Zsh), double quotes are interpreted.
    Thus, the easiest way to avoid problems is to quote the data/mapping
    argument into single quotes: ``'data.csv{"name":"value"}:mapping.yaml'``
    AND NOT: ``data.csv{"name":"value"}:mapping.yaml`` (which FAILS).

.. hint::

    If you need to pass a space character, you can use an escaped regexp marker:
    ``'data.tsv{"sep":"\\s"}:mapping.yaml'``
    (note the double escaping of the "s").

.. note::

    If you want to pass shell variables into the JSON dictionary of parameters,
    you can escape the double quotes: ``"data.csv{\"dtype\":\"$MYDTYPE\"}:mapping.yaml"``

For tabular data, OntoWeaver use functions from
`Pandas <https://pandas.pydata.org>`_, with some default parameters:

{{{READFUNCS}}}

.. hint::

    The JSON syntax supports nested dictionaries, which allows you to force
    the *dtype* of any column, for example:

    ``'data.csv{"dtype":{"A":"string","B":"Int64"}}:mapping.yaml'``

    For the list of available string representations of types, see the
    `Pandas doc about dtypes <https://pandas.pydata.org/pandas-docs/stable/user_guide/basics.html#basics-dtypes>`_.

For OWL data, OntoWeaver uses `RDFlib <https://rdflib.readthedocs.io>`_:

- **.owl**: `rdflib.graph.Graph.parse <https://rdflib.readthedocs.io/en/latest/apidocs/rdflib.graph/#rdflib.graph.Graph.parse>`_ ``{"format":"xml"}``,
- **any other extension**: `rdflib.graph.Graph.parse <https://rdflib.readthedocs.io/en/latest/apidocs/rdflib.graph/#rdflib.graph.Graph.parse>`_ (without default parameter).

Other loader functions either do not take parameters, or those parameters are
Python objects, which OntoWeaver does not support so far.


Run the data importer
~~~~~~~~~~~~~~~~~~~~~

To insert data in an SKG database, you need to run the import
script that is prepared by *ontoweave*. Or you can ask
*ontoweave* to run it for you:

.. code:: sh

   ontoweave my_data.csv:my_mapping.yaml --import-script-run

You can capture the import script path and run it afterward, which comes in
handy if you run *ontoweave* in a script:

.. code:: sh

   script="$(ontoweave my_data.csv:my_mapping.yaml)"  # Capture.
   $script  # Run the import script.


Sub-sample every input data
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 1.8.0

The ``--sub-sample`` options allows to draw a random sample from each input
data file, during their loading. It takes as argument a percentage of items
(e.g. rows, for tabular data).

.. note::

    This option is applied independently to each input data.
    This means that if you integrate two data files, they both will be
    sub-sampled by the given percentage, withut regards for their relative
    sizes.

For example, the following command:

.. code:: sh

    ontoweave small.csv:map_s.yaml large.csv:map_l.yaml --sub-sample 50

will randomly draw 50% of rows from ``small.csv``, and then draw 50% of rows
from ``large.csv``.


Typical example
~~~~~~~~~~~~~~~

A typical use-case is to weave several data sources at once, using a default
configuration, generating the schema on-the-fly and running the script that
create the final database:

.. code:: sh

   ontoweave things.csv:map_things.yaml stuff-part*.parquet:map_stuff.yaml --auto-schema autoschema.yaml --import-script-run


Progress bars
~~~~~~~~~~~~~

.. versionadded:: 1.4

If you pass the ``--progress-bars`` option to ``ontoweave``,
OntoWeaver will do its best to show progress bars during processing
that are potentially heavy.

Note that this only really is useful with at least ``--log-level=INFO``.
With ``DEBUG``, the progress bar display is not always readable.

This feature is always disabled if ``ontoweave`` is not executed in an
interactive terminal.

.. note::

    When loading files that do not expose their number of entries as metadata
    (CSV files, for instance, especially ordered ones),
    the progress be may be over- or under-estimated.
    OntoWeaver does its best to guess a good estimate, but there is no guarantee
    that it guesses right.
    For files that have size metadata, or regular processing, the progress
    should be accurate.

