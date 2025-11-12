Usage
-----

What OntoWeaver actually does is to automatically provides a working "adapter"
for BioCypher, without you having to implement it.

The output of the execution of the adapter is thus what BioCypher is
providing (see `BioCypher’s documentation <https://biocypher.org>`__).
In a nutshell, the output is a script file that, when executed, will
populate the configured database. By default, the output script file is
saved in a subdirectory of ``./biocypher-out/``, which name is a
timestamp from when the adapter has been executed.

To configure your data mapping, you will have to first define the
mapping that you want to apply on your data. Then, you will need a
BioCypher configuration file (which mainly indicate your ontologoy and
backend), and a schema configuration file (indicating which node and
edge types you want).

To actually do something, you need to run OntoWeaver mapping onto your
data. We provide a command line interface to do so, called
``ontoweave``.

If you use some default config file (usually ``biocypher_config.yaml``)
and schema (usually ``schema_config.yaml``), the simplest call would be:

.. code:: sh

   ontoweave my_data.csv:my_mapping.yaml

If you want to indicate your own configuration files, pass their name as
options:

.. code:: sh

   ontoweave --biocypher-config biocypher_config.yaml --biocypher-schema schema_config.yaml data-1.1.csv:map-1.yaml data-1.2.csv:map-1.yaml data-A.csv:map-A.yaml

note that you can use the same mapping on several data files, and/or
several mappings.

To actually insert data in an SKG database, you need to run the import
files that are prepared by the previous command. Either you ask
*ontoweave* to run it for you:

.. code:: sh

   ontoweave my_data.csv:my_mapping.yaml --import-script-run

or you can capture the import script path and run it yourself:

.. code:: sh

   script="$(ontoweave my_data.csv:my_mapping.yaml)" # Capture.
   $script # Run.

You will find more options by running the help command:

.. code:: sh

   ontoweave --help
