OntoWeaver
==========

Overview
--------

OntoWeaver is a tool for importing table data in Semantic Knowledge
Graphs (SKG) databases.

OntoWeaver allows writing a simple declarative mapping to express how
columns from a `Pandas <https://pandas.pydata.org/>`__ table are to be
converted as typed nodes or edges in an SKG.

|OntoWeaver logo|

It provides a simple layer of abstraction on top of
`Biocypher <https://biocypher.org>`__, which remains responsible for
doing the ontology alignment, supporting several graph database
backends, and allowing reproducible & configurable builds.

With a pure Biocypher approach, you would have to write a whole adapter
by hand, with OntoWeaver, you just have to express a mapping in YAML,
looking like:

.. code:: yaml

   row: # The meaning of an entry in the input table.
      map:
         column: <column name in your CSV>
         to_subject: <ontology node type to use for representing a row>

   transformers: # How to map cells to nodes and edges.
       - map: # Map a column to a node.
           column: <column name>
           to_object: <ontology node type to use for representing a column>
           via_relation: <edge type for linking subject and object nodes>
       - map: # Map a column to a property.
           column: <another name>
           to_property: <property name>
           for_object: <type holding the property>

   metadata: # Optional properties added to every node and edge.
       - source: "My OntoWeaver adapter"
       - version: "v1.2.3"

Installation and quick setup guide
----------------------------------

Python Module
~~~~~~~~~~~~~

The project is written in Python and uses
`Poetry <https://python-poetry.org>`__. You can install the necessary
dependencies in a virtual environment like this:

::

   git clone https://github.com/oncodash/ontoweaver.git
   cd ontoweaver
   poetry install

Poetry will create a virtual environment according to your configuration
(either centrally or in the project folder). You can activate it by
running ``poetry shell`` inside the project directory.

Output Database
~~~~~~~~~~~~~~~

Theoretically, the graph can be imported in any [graph] database
supported by BioCypher (Neo4j, ArangoDB, CSV, RDF, PostgreSQL, SQLite,
NetworkX, … see `BioCypher’s
documentation <https://biocypher.org/output/index.html>`__).

Graph visualization with Neo4j
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Neo4j is a popular graph database management system that offers a
flexible and efficient way to store, query, and manipulate complex,
interconnected data. Cypher is the query language used to interact with
Neo4j databases. In order to visualize graphs extracted from databases
using OntoWeaver and BioCypher, you can download the `Neo4j Graph
Database Self-Managed <https://neo4j.com/deployment-center/>`__ for your
operating system. It has been extensively tested with the Community
edition.

To create a global variable to Neo4j, add the path to ``neo4j-admin`` to
your ``PATH`` and ``PYTHONPATH``. In order to use the Neo4j browser, you
will need to install the correct Java version, depending on the Neo4j
version you are using, and add the path to ``JAVA_HOME``. OntoWeaver and
BioCypher support versions 4 and 5 of Neo4j.

To run Neo4j (version 5+), use the command ``neo4j-admin server start``
after importing your results via the neo4j import sequence provided in
the ``./biocypher-out/`` directory. Use ``neo4j-admin server stop`` to
disconnect the local server.

Tests
~~~~~

Tests are located in the ``tests/`` subdirectory and may be a good
starting point to see OntoWeaver in practice. You may start with
``tests/test_simplest.py`` which shows the simplest example of mapping
tabular data through BioCypher.

To run tests, use ``pytest``:

::

   poetry run pytest

or, alternatively:

::

   poetry shell
   pytest

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

To configure your data mapping, you will have to first define the
mapping that you want to apply on your data. Then, you will need a
BioCypher configuration file (which mainly indiciate your ontologoy and
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

   script=$(ontoweave my_data.csv:my_mapping.yaml) # Capture.
   $script # Run.

You will find more options by running the help command:

.. code:: sh

   ontoweave --help

Mapping API
-----------

OntoWeaver essentially creates a Biocypher adapter from the description
of a mapping from a table to ontology types. As such, its core input is
a dictionary, that takes the form of a YAML file. This configuration
file indicates:

- to which (node) type to map each line of the table,
- to which (node) type to map columns of the table,
- with which (edge) types to map relationships between nodes.

The following explanations assume that you are familiar with
`Biocypher’s
configuration <https://biocypher.org/tutorial-ontology.html>`__, notably
how it handles ontology alignment with schema configuration.

Common Mapping
~~~~~~~~~~~~~~

The minimal configuration would be to map lines and one column, linked
with a single-edge type.

For example, if you have the following CSV table of phenotypes/patients:

::

   phenotype,patient
   0,A
   1,B

and if you target the Biolink ontology, using a schema configuration
(i.e. subset of types), defined in your ``shcema_config.yaml`` file, as
below:

.. code:: yaml

   phenotypic feature:
       represented_as: node
       label_in_input: phenotype
   case:
       represented_as: node
       label_in_input: case
   case to phenotypic feature association:
       represented_as: edge
       label_in_input: case_to_phenotype
       source: phenotypic feature
       target: case

you may write the following mapping:

.. code:: yaml

   row:
      rowIndex:
         # No column is indicated, but OntoWeaver will map the indice of the row to the node name.
         to_subject: phenotype
   transformers:
       - map:
           column: patient # Name of the column in the table.
           to_object: case # Node type to export to (most probably the same as in the ontology).
           via_relation: case_to_phenotype # Edge type to export to.

This configuration will end in creating a node for each phenotype, a
node for each patient, and an edge for each phenotype-patient pair:

::

             case to phenotypic
             feature association
                       ↓
              ╭───────────────────╮
              │              ╔════╪════╗
              │              ║pati│ent ║
              │              ╠════╪════╣
   ╭──────────┴──────────╮   ║╭───┴───╮║
   │phenotypic feature: 0│   ║│case: A│║
   ╰─────────────────────╯   ║╰───────╯║
                             ╠═════════╣
   ╭─────────────────────╮   ║╭───────╮║
   │          1          │   ║│   B   │║
   ╰──────────┬──────────╯   ║╰───┬───╯║
              │              ╚════╪════╝
              ╰───────────────────╯

Available Transformers
~~~~~~~~~~~~~~~~~~~~~~

If you want to transform a data cell before exporting it as one or
several nodes, you will use other *transformers* than the “map” one.

``map``
^^^^^^^

The *map* transformer simply extracts the value of the cell defined, and
is the most common way of mapping cell values.

For example:

.. code:: yaml

       - map:
           column: patient
           to_object: case

Although the examples usually define a mapping of cell values to nodes,
the transformers can also used to map cell values to properties of nodes
and edges. For example:

.. code:: yaml

       - map:
           column: version
           to_property: version
           for_objects:
               - patient # Node type.
               - variant
               - patient_has_variant # Edge type.

``split``
^^^^^^^^^

The *split* transformer separates a string on a separator, into several
items, and then inserts a node for each element of the list.

For example, if you have a list of treatments separated by a semicolon,
you may write:

.. code:: yaml

   row:
      map:
         to_subject: phenotype
   transformers:
       - map:
           column: variant
           to_object: variant
           via_relation: phenotype_to_variant
       - split:
           column: treatments
           from_subject: variant
           to_object: drug
           via_relation: variant_to_drug
           separator: ";"

::

        phenotype to variant      variant to drug
                ↓                       ↓
          ╭───────────────╮   ╭────────────────╮
          │         ╔═════╪═══╪═╦══════════════╪═════╗
          │         ║ vari│ant│ ║  treatments  │     ║
          │         ╠═════╪═══╪═╬══════════════╪═════╣
          │         ║     │   │ ║variant       │     ║
          │         ║     │   │ ║to drug       │     ║
   ╭──────┴─────╮   ║╭────┴───┴╮║  ↓    ╭──╮ ╭─┴────╮║
   │phenotype: 0│   ║│variant:A├╫───────┤ X│;│drug:Y│║
   ╰────────────╯   ║╰─────────╯║       ╰┬─╯ ╰──────╯║
                    ╠═══════════╬════════╪═══════════╣
   ╭────────────╮   ║╭─────────╮║       ╭│ ╮ ╭──╮    ║
   │      1     │   ║│    B    ├╫────────╯X ;│ Z│    ║
   ╰──────┬─────╯   ║╰────┬───┬╯║       ╰  ╯ ╰─┬╯    ║
          │         ╚═════╪═══╪═╩══════════════╪═════╝
          ╰───────────────╯   ╰────────────────╯

``cat``
^^^^^^^

The *cat* transformer concatenates the values cells of the defined
columns and then inserts a single node. For example, the mapping below
would result in the concatenation of cell values from the columns
``variant_id``, and ``disease``, to the node type ``variant``. The
values are concatenated in the order written in the ``columns`` section.

.. code:: yaml

   row:
      cat:
         columns: # List of columns whose cell values are to be concatenated
           - variant_id
           - disease
         to_subject: variant # The ontology type to map to

``cat_format``
^^^^^^^^^^^^^^

The user can also define the order and format of concatenation by
creating a ``format_string`` field, which defines the format of the
concatenation. For example:

.. code:: yaml

   row:
      cat_format:
         columns: # List of columns whose cell values are to be concatenated
           - variant_id
           - disease
         to_subject: variant # The ontology type to map to
         # Enclose column names in brackets where you want their content to be:
         format_string: "{disease}_____{variant_id}"

``string``
^^^^^^^^^^

The *string* transformer allows mapping the same pre-defined static
string to properties of *some* nodes or edge types.

It only needs the string *value*, and then a regular property mapping:

.. code:: yaml

       - string:
           value: "This may be useful"
           to_property: comment
           for_objects:
               - patient
               - variant

``translate``
^^^^^^^^^^^^^

The *translate* transformer changes the targeted cell value from the one
contained in the input table to another one, as configured through
(another) mapping, extracted from (another) table.

This is useful to *reconciliate* two sources of data using two different
references for the identifiers of the same object. The translate
transformer helps you translate one of the identifiers to the other
reference, so that the resulting graph only uses one reference, and
there is no duplicated information at the end.

For instance, let’s say that you have two input tables providing
information about the same gene, but one is using the HGCN names, and
the other the Ensembl gene IDs:

===== =============
Name  Source
===== =============
BRCA2 PMID:11207365
===== =============

=============== ============
Gene            Organism
=============== ============
ENSG00000139618 Mus musculus
=============== ============

Then, to map a gene from the second table (the one using Ensembl), you
would do:

.. code:: yaml

       - translate:
           column: Gene
           to_object: gene
           translations:
               ENSG00000139618: BRCA2

Of course, there could be hundreds of thousands of translations to
declare, and you don’t want to declare them by hand in the mapping file.
Fortunately, you have access to another table in a CSV file, showing
which one corresponds to the other:

=============== ===== ========
Ensembl         HGCN  Status
=============== ===== ========
ENSG00000139618 BRCA2 Approved
=============== ===== ========

Then, to declare a translation using this table, you would do:

.. code:: yaml

       - translate:
           column: Gene
           to_object: gene
           translations_file: <myfile.csv>
           translate_from: Ensembl
           translate_to: HGCN

To load the translation file, OntoWeaver uses `Pandas’
read_csv <https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html>`__
function. You may pass additional string arguments in the mapping
section, they will be passed directly as ``read_csv`` arguments. For
example:

.. code:: yaml

       - translate:
           column: Gene
           to_object: gene
           translations_file: <myfile.csv.zip>
           translate_from: Ensembl
           translate_to: HGCN
           sep: ;
           compression: zip
           decimal: ,
           encoding: latin-1

replace
^^^^^^^

The *replace* transformer allows the removal of forbidden characters
from the values extracted from cells of the data frame. The pattern
matching the characters that are *forbidden* characters should be passed
to the transformer as a regular expression. For example:

.. code:: yaml

       - replace:
           columns:
               - treatment
           to_object: drug
           via_relation: alteration_biomarker_for_drug
           forbidden: '[^0-9]' # Pattern matching all characters that are not numeric. 
           # Therefore, you only allow numeric characters. 
           substitute: "_" # Substitute all removed characters with an underscore, in case they are  
           # located inbetween allowed_characters.

Here we define that the transformer should only allow numeric characters
in the values extracted from the *treatment* column. All other
characters will be removed and substituted with an underscore, in case
they are located inbetween allowed characters.

By default, the transformer will allow alphanumeric characters (A-Z,
a-z, 0-9), underscore (\_), backtick (\`), dot (.), and parentheses (),
and the substitute will be an empty string. If you wish to use the
default settings, you can write:

.. code:: yaml

       - replace:
           columns:
               - treatment
           to_object: drug
           via_relation: alteration_biomarker_for_drug

Let’s assume we want to map a table consisting of contact IDs and phone
numbers.

======== ============
id       phone_number
======== ============
Jennifer 01/23-45-67
======== ============

We want to map the ``id`` column to the node type ``id`` and the
``phone_number`` column to the node type ``phone_number``, but we want
to remove all characters that are not numeric, using the default
substitute (““), meaning the forbidden characters will only be removed,
and not replaced by another character. The mapping would look like this:

.. code:: yaml

   row:
       map:
           column: id
           to_subject: id
   transformers:
       - replace:
           column: phone_number
           to_object: phone_number
           via_relation: phone_number_of_person
           forbidden: '[^0-9]'

The result of this mapping would be a node of type ``phone_number``,
with the id of the node being ``01234567``, connected to a node of type
``id`` with the id ``Jennifer``, via an edge of type
``phone_number_of_person``.

Multi-type Transformers
~~~~~~~~~~~~~~~~~~~~~~~

In some cases there might be a need to apply multiple type mappings to
cell values within a single column. For example, in the table below, you
might want to map the column ``WORDS`` based on the word type detected.

::

   | LINE | WORDS |
   | ---- | ---------- |
   | 0 | sensitive |
   | 1 | sensitivity |
   | 2 | productive |
   | 3 | productivity |

.. code:: yaml

   row:
      map:
        column: LINE
        to_subject: line
   transformers:
       - map:
           column: WORDS
           match:
               - ive\b:
                   to_object: adjective
                   via_relation: line_is_adjective
               - ivity\b:
                   to_object: noun
                   via_relation: line_is_noun

Here we see a mapping that uses the ``match`` clause to apply different
type mappings to cell values based on the word type detected. We define
two regex rules:

- ``ive\b`` which matches words ending with ``ive`` and maps them to the
  node type ``adjective`` via the edge type ``line_is_adjective``.
- ``ivity\b`` which matches words ending with ``ivity`` and maps them to
  the node type ``noun`` via the edge type ``line_is_noun``.

This way we have managed to handle a case where a single column of words
can result in multiple node types which should be connected to the
subject type ``line`` with different edge types. The cell values
``sensitive`` and ``productive`` would be mapped to the node type
``adjective`` via the edge type ``line_is_adjective``, while the cell
values ``sensitivity`` and ``productivity`` would be mapped to the node
type ``noun`` via the edge type ``line_is_noun``.

User-defined Transformers
~~~~~~~~~~~~~~~~~~~~~~~~~

It is easy to create your own transformer, if you want to operate
complex data transformations, but still have them referenced in the
mapping.

This may even be a good idea if you do some pre-processing on the input
table, as it keeps it obvious for anyone able to read the mapping (while
it may be difficult to read the pre-processing code itself).

A user-defined transformer takes the form of a Python class inheriting
from ``ontoweaver.base.Transformer``:

.. code:: python

   class my_transformer(ontoweaver.base.Transformer):

       # The constructor is called when parsing the YAML mapping.
       def __init__(self, target, properties_of, edge=None, columns=None, **kwargs):

           # All the arguments passed to the super class are available as member variables.
           super().__init__(target, properties_of, edge, columns, **kwargs)

           # If you want user-defined parameters, you may get them from
           # the corresponding member variables (e.g. `self.my_param`).
           # However, if you want to have a default value if they are not declared
           # by the user in the mapping, you have to get them from kwargs:
           self.my_param = kwargs.get("my_param", None) # Defaults to None.

       # The call interface is called when processing a row.
       def __call__(self, row, index):

           # You should take care of your parameters:
           if not self.my_param:
               raise ValueError("You forgot the `my_param` keyword")

           # The columns declared by the user (with the "column(s)" keyword)
           # are available as a member variable:
           for col in self.columns:
               # Some methods of base.Transformer may be useful, like `valid`
               # which checks whether a cell value is something useful.
               if self.valid(row[col]):
                   result = row[col]
                   # […] Do something of your own with row[col] […]
                   # You are finally required to yield a string:
                   yield str(result)

Once your transformer class is implemented, you should make it available
to the ``ontoweaver`` module which will process the mapping:

.. code:: python

   ontoweaver.transformer.register(my_transformer)

You can have a look at the transformers provided by OntoWeaver to get
inspiration for your own implementation:
`ontoweaver/src/ontoweaver/transformer.py <https://github.com/oncodash/ontoweaver/blob/main/src/ontoweaver/transformer.py>`__

Keywords Synonyms
~~~~~~~~~~~~~~~~~

Because several communities gathered around semantic knowledge graphs,
several terms can be used (more or less) interchangeably.

OntoWeaver thus allows you to use your favorite vocabulary to write down
the mapping configurations.

Here is the list of available synonyms:

- ``subject`` = ``row`` = ``entry`` = ``line`` = ``source``
- ``column`` = ``columns`` = ``fields``
- ``to_object`` = ``to_target`` = ``to_node``
- ``from_subject`` = ``from_source``
- ``via_relation`` = ``via_edge`` = ``via_predicate``
- ``to_property`` = ``to_properties``
- ``for_object`` = ``for_objects``

How To
------

How to Add Properties to Nodes and Edges
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you do not need to create a new node, but simply attach some data to
an existing node, use the ``to_property`` predicate, for example:

.. code:: yaml

   row:
      map:
         to_subject: phenotype
   transformers:
       - map:
           column: patient
           to_object: case
           via_relation: case_to_phenotype
       - map:
           column: age
           to_property: patient_age
           for_object: case

This will add a “patient_age” property to nodes of type “case”.

Note that you can add the same property value to several property fields
of several node types:

.. code:: yaml

       - map:
           column: age
           to_properties:
               - patient_age
               - age_patient
           for_object:
               - case
               - phenotype

How to Extract Additional Edges
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Edges can be extracted from the mapping configuration, by defining a
``from_subject`` and ``to_object`` in the mapping configuration, where
the ``from_subject`` is the node type from which the edge will start,
and the ``to_object`` is the node type to which the edge will end.

For example, consider the following mapping configuration for the sample
dataset below:

::

   id  patient         sample
   0   patient1    sample1
   1   patient2    sample2
   2   patient3    sample3
   3   patient4    sample4

.. code:: yaml

   row:
       map:
           column: id
           to_subject: variant
   transformers:
       - map:
             column: patient
             to_object: patient
             via_relation: patient_has_variant
       - map:
             column: sample
             to_object: sample
             via_relation: variant_in_sample

If the user would like to extract an additional edge from the node type
``patient`` to the node type ``sample``, they would need to add the
following section to the transformers in the mapping configuration:

.. code:: yaml

       - map:
           column: patient
           from_subject: sample
           to_object: patient
           via_relation: sample_to_patient

How to add the same metadata properties to all nodes and edges
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Metadata can be added to nodes and edges by defining a ``metadata``
section in the mapping configuration. You can specify all the property
keys and values that you wish to add to your nodes and edges in a
``metadata`` section. For example:

.. code:: yaml

   metadata:
           - name: oncokb
           - url: https://oncokb.org/
           - license: CC BY-NC 4.0
           - version: 0.1

The metadata defined in the ``metadata`` section will be added to all
nodes and edges created during the mapping process.

How to add the column of origin as a property to all nodes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In addition to the user-defined metadata, a property field
``add_source_column_names_as`` is also available. It allows to indicate
the column name in which the data was found, as a property to each
*node*. Note that this is not added to *edges*, because they are not
mapped from a column *per se*.

For example, if the label of a node is extracted from the “indication”
column, and you indicate ``add_source_column_name_as: source_column``,
the node will have a property: ``source_column: indication``.

This can be added to the metadata section as follows:

.. code:: yaml

   metadata:
           - name: oncokb
           - url: https://oncokb.org/
           - license: CC BY-NC 4.0
           - version: 0.1
           - add_source_column_names_as: sources

Now each of the nodes contains a property ``sources`` that contains the
names of the source columns from which it was extracted. Be sure to
include all the added node properties in the schema configuration file,
to ensure that the properties are correctly added to the nodes.

How to create user-defined adapters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You may manually define your own adapter class, inheriting from the
OntoWeaver’s class that manages tabular mappings.

For example:

.. code:: python

   class MYADAPTER(ontoweaver.tabular.PandasAdapter):

       def __init__(self,
           df: pd.DataFrame,
           config: dict,
           type_affix: Optional[ontoweaver.tabular.TypeAffixes] = ontoweaver.tabular.TypeAffixes.prefix,
           type_affix_sep: Optional[str] = "//",
       ):
           # Default mapping as a simple config.
           from . import types
           parser = ontoweaver.tabular.YamlParser(config, types)
           mapping = parser()

           super().__init__(
               df,
               *mapping,
           )

When manually defining adapter classes, be sure to define the affix type
and separator you wish to use in the mapping. Unless otherwise defined,
the affix type defaults to ``suffix``, and the separator defaults to
``:``. In the example above, the affix type is defined as ``prefix`` and
the separator is defined as ``//``. If you wish to define affix as
``none``, you should use
``type_affix: Optional[ontoweaver.tabular.TypeAffixes] = ontoweaver.tabular.TypeAffixes.none``,
and if you wish to define affix type as ``suffix``, use
``type_affix: Optional[ontoweaver.tabular.TypeAffixes] = ontoweaver.tabular.TypeAffixes.suffix``.

How to access dynamic Node and Edge Types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

OntoWeaver relies a lot on meta-programming, as it actually creates
Python types while parsing the mapping configuration. By default, those
classes are dynamically created into the ``ontoweaver.types`` module.

You may manually define your own types, derivating from
``ontoweaver.base.Node`` or ``ontoweaver.base.Edge``.

The ``ontoweaver.types`` module automatically gathers the list of
available types in the ``ontoweaver.types.all`` submodule. This allows
accessing the list of node and edge types:

.. code:: python

   node_types  = types.all.nodes()
   edge_types  = types.all.edges()

Parallel Processing
-------------------

OntoWeaver provides a way to parallelize the extraction of nodes and
edges from the provided database, with the aim of reducing the runtime
of the extraction process. By default, the parallel processing is
disabled, and the data frame is processed in a sequential manner. To
enable parallel processing, the user can pass the maximum number of
workers to the ``extract_table`` function.

For example, to enable parallel processing with 16 workers, the user can
call the function as follows:

.. code:: python

   adapter = ontoweaver.tabular.extract_table(table, mapping, parallel_mapping = 16)

To enable parallel processing with a good default working on any
machine, you can use the `approach suggested by the concurrent
module <https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.ThreadPoolExecutor>`__.

.. code:: python

   import os
   adapter = ontoweaver.tabular.extract_table(table, mapping, parallel_mapping = min(32, (os.process_cpu_count() or 1) + 4))

Information Fusion
------------------

When integrating several sources of information to create your own SKG,
you will inevitably face a case where two sources provide different
information for the same object. If you process each source with a
separate mapping applied to separate input tables, then each will
provide the same node, albeit with different properties.

This is an issue, as BioCypher does not provide a way to fuse both nodes
in a single one, while keeping all the properties. As of version 0.5, it
will use the last seen node, and discard the first one(s), effectively
loosing information (albeit with a warning). With a raw Biocypher
adapter, the only way to solve this problem is to implement a single
adapter, which reconciliate the data before producing nodes, which makes
the task difficult and the adapter code even harder to understand.

Reconciliation
~~~~~~~~~~~~~~

OntoWeaver provides a way to solve the reconciliation problem with its
*high-level information fusion* feature. The fusion features allow to
reconciliate the nodes and edges produced by various *independent*
adapters, by adding a final step on the aggregated list of nodes and
edges.

The generic workflow is to first produce nodes and edges —as usual— then
call the ``fusion.reconciliate`` function on the produced nodes and
edges:

.. code:: python

   # Call the mappings:
   adapter_A = ontoweaver.tabular.extract_table(input_table_A, mapping_A)
   adapter_B = ontoweaver.tabular.extract_table(input_table_B, mapping_B)

   # Aggregate the nodes and edges:
   nodes = adapter_A.nodes + adapter_B.nodes
   edges = adapter_A.edges + adapter_B.edges

   # Reconciliate:
   fused_nodes, fused_edges = ontoweaver.fusion.reconciliate(nodes, edges, separator=";")

   # Then you can pass those to biocypher.write_nodes and biocypher.write_edges...

High-level Interface
^^^^^^^^^^^^^^^^^^^^

OntoWeaver provides the ``fusion.reconciliate`` function, that
implements a sane default reconciliation of nodes. It merges nodes
having the same identifier and the same type, taking care of not losing
any property. When nodes have the same property field showing different
values, it aggregates the values in a list.

This means that if the two following nodes come from two different
sources:

.. code:: python

   # From source A:
   ("id_1", "type_A", {"prop_1": "x"}),
   ("id_1", "type_A", {"prop_2": "y"}),

   # From source B:
   ("id_1", "type_A", {"prop_1": "z"})

Then, the result of the reconciliation step above would be:

.. code:: python

   # Note how "x" and "z" are separated by separator=";".
   ("id_1", "type_A", {"prop_1": "x;z", "prop_2": "y"})

Mid-level Interfaces
^^^^^^^^^^^^^^^^^^^^

The simplest approach to fusion is to define how to:

1. decide that two nodes are identical,
2. fuse two identifiers,
3. fuse two type labels, and
4. fuse two properties dictionaries, and then
5. let OntoWeaver browse the nodes by pairs, until everything is fused.

For step 1, OntoWeaver provides the ``serialize`` module, which allows
to extract the part of a node or an edge) that should be used when
checking equality.

A node being composed of an identifier, a type label, and a properties
dictionary, the ``serialize`` module provides function objects
reflecting the useful combinations of those components:

- ``ID`` (only the identifier)
- ``IDLabel`` (the identifier and the type label)
- ``All`` (the identifier, the type label, and the properties)

The user can instantiate those function objects, and pass them to the
``congregate`` module, to find which nodes are duplicates of each other.
For example:

.. code:: python

   on_ID = serialize.ID() # Instantiation.
   congregater = congregate.Nodes(on_ID) # Instantiation.
   congregater(my_nodes) # Actual processing call.
   # congregarter now holds a dictionary of duplicated nodes.

For steps 2 to 4, OntoWeaver provides the ``merge`` module, which
provides ways to merge two nodes’ components into a single one. It is
separated into two submodules, depending on the type of the component:

- ``string`` for components that are strings (i.e. identifier and type
  label),
- ``dictry`` for components that are dictionaries (i.e. properties).

The ``string`` submodule provides:

- ``UseKey``: replace the identifier with the serialization used at the
  congregation step,
- ``UseFirst``/``UseLast``: replace the type label with the first/last
  one seen,
- ``EnsureIdentical``: if two nodes’ components are not equal, raise an
  error,
- ``OrderedSet``: aggregate all the components of all the seen nodes
  into a single, lexicographically ordered list (joined by a
  user-defined separator).

The ``dictry`` submodule provides:

- ``Append``: merge all seen dictionaries in a single one, and aggregate
  all the values of all the duplicated fields into a single
  lexicographically ordered list (joined by a user-defined separator).

For example, to fuse “congregated” nodes, one can do:

.. code:: python

       # How to merge two components:
       use_key    = merge.string.UseKey() # Instantiation.
       identicals = merge.string.EnsureIdentical()
       in_lists   = merge.dictry.Append(separator)

       # Assemble those function objects in an object that knows
       # how to apply them members by members:
       fuser = fuse.Members(base.Node,
               merge_ID    = use_key,    # How to merge two identifiers.
               merge_label = identicals, # How to merge two type labels.
               merge_prop  = in_lists,   # How to merge two properties dictionaries.
           )

       # Apply a "reduce" step (browsing pairs of nodes, until exhaustion):
       fusioner = Reduce(fuser) # Instantiation.
       fusioned_nodes = fusioner(congregater) # Call on the previously found duplicates.

Once this fusion step is done, is it possible that the edges that were
defined by the initial adapters refer to node IDs that do not exist
anymore. Fortunately, the fuser keeps track of which ID was replaced by
which one. And this can be used to remap the edges’ *target* and
*source* identifiers:

.. code:: python

   remaped_edges = remap_edges(edges, fuser.ID_mapping)

Finally, the same fusion step can be done on the resulting edges (some
of which are now duplicates, because they were remapped):

.. code:: python

       # Find duplicates:
       on_STL = serialize.edge.SourceTargetLabel()
       edges_congregater = congregate.Edges(on_STL)
       edges_congregater(edges)

       # How to fuse them:
       set_of_ID       = merge.string.OrderedSet(separator)
       identicals      = merge.string.EnsureIdentical()
       in_lists        = merge.dictry.Append(separator)
       use_last_source = merge.string.UseLast()
       use_last_target = merge.string.UseLast()
       edge_fuser = fuse.Members(base.GenericEdge,
               merge_ID     = set_of_ID,
               merge_label  = identicals,
               merge_prop   = in_lists,
               merge_source = use_last_source,
               merge_target = use_last_target
           )

       # Fuse them:
       edges_fusioner = Reduce(edge_fuser)
       fusioned_edges = edges_fusioner(edges_congregater)

Because all those steps are performed onto OntoWeaver’s internal
classes, they need to be converted back to Biocypher’s tuples:

.. code:: python

       return [n.as_tuple() for n in fusioned_nodes], [e.as_tuple() for e in fusioned_edges]

Low-level Interfaces
^^^^^^^^^^^^^^^^^^^^

Each of the steps mentioned in the previous section involves a functor
class that implements a step of the fusion process. Users may provide
their own implementation of those interfaces, and make them interact
with the others.

The first function interface is the ``congregate.Congregater``, whose
role is to consume a list of Biocypher tuples, find duplicated elements,
and store them in a dictionary mapping a key to a list of elements.

This allows to implementation of a de-duplication algorithm with a time
complexity in O(n·log n).

A ``Congregater`` is instantiated with a ``serialize.Serializer``,
indicating which part of an element is to be considered when checking
for equality.

The highest level fusion interface is ``fusion.Fusioner``, whose role is
to process a ``congregate.Congregater`` and return a set of fusioned
nodes.

OntoWeaver provides ``fusion.Reduce`` as an implementation of
``Fusioner``, which itself relies on an interface whose role is to fuse
two elements: ``fuse.Fuser``.

OntoWeaver provides a ``fuse.Members`` as an implementation, which
itself relies on ``merge.Merger``, which role is to fuse two elements’
*components*.

So, from the lower to the higher level, the following three interfaces
can be implemented:

1. ``merge.Merger`` —(used by)→ ``fuse.Members`` —(used by)→
   ``fusion.Reduce``
2. ``fuse.Fuser`` —(used by)→ ``fusion.Reduce``
3. ``fusion.Fusioner``

For instance, if you need a different way to *merge* elements
*components*, you should implement your own ``merge.Merger`` and use it
when instantiating ``fuse.Members``.

If you need a different way to *fuse* two *elements* (for instance for
deciding their type based on their properties), implement a
``fuse.Fuser`` and use it when instantiating a ``fusion.Reduce``.

If you need to decide how to fuse whole *sets* of duplicated nodes (for
instance if you need to know all duplicated nodes before deciding which
type to set), implement a ``fusion.Fusioner`` directly.

Data Validation
---------------

Apart from mapping and fusion features, OntoWeaver also offers a data
validation feature to help you ensure your input databases and the
outputs of your mapping fulfill a set of predefined expectations. The
data validation feature uses the functionalities provided by the
`Pandera
package <(https://pandera.readthedocs.io/en/stable/index.html)>`__, as
well as its YAML configuration to validate the data. These YAML
configurations enable you to write some basic definitions of types and
domains expected for each of the columns of your input data, as well as
type and domain expectations for the output of your mapping, with some
preset rules for outputs, ensuring that the output of any mapping will
not result in an empty value and will be a string.

Here’s an example of what a YAML configuration file for a simple
database would look like:

::

   | variant_id | patient |
   |------------|---------|
   |      0     |    A    |
   |      1     |    B    |
   |      2     |    C    |

Let’s first define a simple mapping configuration for the above data. In
the example below we are mapping the column ``patient`` to a ``patient``
node and the index of the row to a ``variant`` node. The two nodes are
connected via the ``patient_has_variant`` edge.

.. code:: yaml

   row:
      rowIndex:
         to_subject: variant
   transformers:
       - map:
           columns:
               - patient
           to_object: patient
           via_relation: patient_has_variant

Input Data Validation
~~~~~~~~~~~~~~~~~~~~~

Now, let’s define a YAML configuration file for input data validation.
The configuration is part of the ``yaml`` file used to configure the
mapping. We start off by defining a ``validate`` section in the YAML
file, followed by a section defining the ``columns``. For each column in
our database, we define a ``type`` (``dtype: int64`` for the
``variant_id`` column and ``dtype: str`` for the ``patient`` column),
and a set of ``checks`` that we want to perform on the data in the
column. In this case, we want to ensure that the ``variant_id`` column
is in range from 0 to 3, and that the ``patient`` column only contains
the values ``A``, ``B``, and ``C``.

.. code:: yaml

   row:
      rowIndex:
         to_subject: variant
   transformers:
       - map:
           columns:
               - patient
           to_object: patient
           via_relation: patient_has_variant
   validate:
     columns:
       variant_id:
         dtype: int64
         checks:
           in_range:
             min_value: 0
             max_value: 3
             include_min: true
             include_max: true
       patient:
         dtype: str
         checks:
           isin:
             value:
               - A
               - B
               - C

Now we can validate our input data using the command below, which will
return an error if the data does not meet the expectations.

.. code:: sh

   ontoweave my_data.csv:my_mapping.yaml --validate-only

If you want to know more about the rules you can use to validate your
data, you can check the `Pandera
documentation <https://pandera.readthedocs.io/en/stable/index.html>`__.

Output Data Validation
~~~~~~~~~~~~~~~~~~~~~~

The output data validation is similar to the input data validation, but
it is used to validate the output of the mapping. Similarly to the
previous example, we define a domain and type, this time of each of the
transformers we use on the input data.

In the mapping below we’ve defined the expected domains for the output
of the mapping. Unlike in the case of input data validation, the output
validation is already configured to expect a non-empty string output, so
we don’t need to define that explicitly. Hence, we begin the output
validation section with the ``validate_output`` keyword, and the only
section to be defined is ``checks``. In this case, we expect the output
of the ``map`` transformer to be one of the values ``A``, ``B``, or
``C``, and the output of the ``rowIndex`` transformer to be one of the
values ``0``, ``1``, ``2``, or ``3``.

.. code:: yaml

   row:
      rowIndex:
         to_subject: variant
         validate_output:
                 checks:
                     isin:
                         value:
                             - '0'
                             - '1'
                             - '2'
                             - '3'
   transformers:
       - map:
           columns:
               - patient
           to_object: patient
           via_relation: patient_has_variant
           validate_output:
                     checks:
                         isin:
                             value:
                                 - A
                                 - B
                                 - C

The whole YAML file, with both data mapping, input data validation, and
output data validation, would look like this:

.. code:: yaml

   row:
      rowIndex:
         to_subject: variant
         validate_output:
                 checks:
                     isin:
                         value:
                             - '0'
                             - '1'
                             - '2'
                             - '3'
   transformers:
       - map:
           columns:
               - patient
           to_object: patient
           via_relation: patient_has_variant
           validate_output:
                     checks:
                         isin:
                             value:
                                 - A
                                 - B
                                 - C
   validate:
     columns:
       variant_id:
         dtype: int64
         checks:
           in_range:
             min_value: 0
             max_value: 3
             include_min: true
             include_max: true
       patient:
         dtype: str
         checks:
           isin:
             value:
               - A
               - B
               - C

You can find a test based on this example in the
``tests/validate_input`` directory of the OntoWeaver repository. The
test there is configured to fail, due to the presence of a forbidden
``E`` character in the input data.

If you want to know more about the rules you can use to validate your
data, you can check the `Pandera
documentation <https://pandera.readthedocs.io/en/stable/index.html>`__.

|OntoWeaver logo| image:: docs/OntoWeaver_logo__big.svg
