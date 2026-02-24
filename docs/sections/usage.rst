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
BioCypher configuration file (which mainly indicate your ontologoy and
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


Typical example
~~~~~~~~~~~~~~~

A typical use-case is to weave several data sources at once, using a default
configuration, generating the schema on-the-fly and running the script that
create the final database:

.. code:: sh

   ontoweave things.csv:map_things.yaml stuff-part*.parquet:map_stuff.yaml --auto-schema autoschema.yaml --import-script-run

