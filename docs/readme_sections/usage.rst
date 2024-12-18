Usage
-----

OntoWeaver actually automatically provides a working adapter for
BioCypher, without you having to do it.

The output of the execution of the adapter is thus what BioCypher is
providing (see `BioCypher’s documentation <https://biocypher.org>`__).
In a nutshell, the output is a script file that, when executed, will
populate the configured database. By default, the output script file is
saved in a subdirectory of ``./biocypher-out/``, which name is a
timestamp from when the adapter has been executed.

To actually insert data in an SKG database, you will have to use
Biocypher export API:

.. code:: python

       import yaml
       import pandas as pd
       import biocypher
       import ontoweaver

       # Load ontology
       bc = biocypher.BioCypher(
           biocypher_config_path = "tests/simplest/biocypher_config.yaml",
           schema_config_path = "tests/simplest/schema_config.yaml"
       )

       # Load data
       table = pd.read_csv("tests/simplest/data.csv")

       # Load mapping
       with open("tests/simplest/mapping.yaml") as fd:
           mapping = yaml.full_load(fd)

       # Run the adapter
       adapter = ontoweaver.tabular.extract_all(table, mapping)

       # Write nodes
       bc.write_nodes( adapter.nodes )

       # Write edges
       bc.write_edges( adapter.edges )

       # Write import script
       bc.write_import_call()

       # Now you have a script that you can run to actually insert data.

Additionally, you will have to define a strategy for the naming of
mapped items when creating nodes, by defining an ``affix`` and
``separator`` to be used during node creation. The ``affix`` used will
represent the ontology type of the item in question. Unless otherwise
defined, the ``affix`` defaults to ``suffix`` and ``separator`` defaults
to ``:``. This can be modified by changing the variables in the
``extract_all()`` function. ``Affix`` can be either a ``prefix``,
``suffix`` or ``none`` - in case you decide not to include the ontology
type in the node naming strategy. Special care should be exercised in
case there are several types of the same name in the database. There is
a possibility that nodes of the same name will be merged together during
mapping, so an ``affix`` should be present. Below are some examples of
node naming strategies. ``NAME`` refers to the name of the item in
question in your database, and ``TYPE`` refers to the type of the item
in the ontology.

.. code:: python

   [...]

      # Affix defaults to "suffix", and separator defaults to ":"
      # Node represented as [NAME]:[TYPE]
      adapter = ontoweaver.tabular.extract_all(table, mapping)

      # Node represented as [TYPE]-[NAME]
      adapter = ontoweaver.tabular.extract_all(table, mapping, affix = "prefix", separator = "-")

      # Node represented as [NAME]
      adapter = ontoweaver.tabular.extract_all(table, mapping, affix = "none")

   [...]
