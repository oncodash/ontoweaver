Mapping API
-----------

OntoWeaver essentially creates a Biocypher adapter from the description
of a mapping from a table to ontology types. As such, its core input is
a dictionary, that takes the form of a YAML file. This configuration
file indicates:

- to which (node) type to map each line of the table,
- to which (node) type to map columns of the table,
- with which (edge) types to map relationships between nodes.


Simplest possible full example
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To build up a SKG from scratch, you will need at least five files:

1. some data, for instance in a table: ``data.csv``,
2. An ontology file, containing the taxonomy of types you want
   to use: ``ontology.ttl``.
3. a BioCypher configuration indicating what ontologies to use, and what
   database to export to: ``config.yaml``,
4. a schema configuration, indicating the graph structure that
   you want: ``schema.yaml``,
5. a mapping, indicating what column of the table to map on which type of the
   ontology: ``mapping.yaml``.

.. image:: OntoWeaver_simple-example.svg
   :alt: Un diagramme montrant les différents fichiers nécessaires pour
         configurer un run d'OntoWeaver.

Let' say we want to extract a graph of 4 nodes and 3 edges from a table
with 3 rows and 2 columns, those files would look like the following.


.. code-block:: csv
   :caption: The ``data.csv`` file:
   
   Stuff,Gizmo
   S1,GA
   S1,GO
   S2,GA


.. code-block:: ttl
   :caption: The ``ontology.ttl`` file.
   
   @prefix : <https://my.domain.tld/ontology#> .
   @prefix owl: <http://www.w3.org/2002/07/owl#> .
   @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
   @prefix biocypher: <https://biocypher.org/biocypher#> .
   
   biocypher:BioCypherRoot a rdfs:Class ;
        rdfs:label "BioCypherRoot" .
   
   owl:Thing a rdfs:Class ;
       rdfs:label "Thing" ; # Note how labels are uppercased.
       rdfs:subClassOf biocypher:BioCypherRoot .
   
   :Node a rdfs:Class ;
       rdfs:label "Mynode" ;
       rdfs:subClassOf owl:Thing .
   
   :Edge a owl:ObjectProperty ;
       rdfs:label "Myedge" ;
       rdfs:subPropertyOf biocypher:BioCypherRoot .


.. code-block:: yaml
   :caption: The ``config.yaml`` file.
   
   biocypher:
       dbms: owl # For example, here, we output in an OWL file.
   
   head_ontology:
       url: my_ontology.ttl
       root_node: BioCypherRoot
   
   owl: # Options for the chosen OWL DBMS.
       rdf_format: turtle
       edge_model: ObjectProperty


.. code-block:: yaml
   :caption: The ``mapping.yaml`` file.
   
   row:
       map:
           column: Stuff     # Columns are uppercased.
           to_subject: thing # But types are converted to lowercase.
   transformers:
       - map:
           column: Gizmo
           # You can map to any label,
           # as the schema will have the
           # last word on the actual type.
           to_object: my_mapped_node
           # But convention dictates to just
           # use the type, as seen by BioCypher,
           # because this is simpler to understand.
           via_relation: myedge


.. code-block:: yaml
   :caption: The ``schema.yaml`` file.

   # Note how BioCypher interprets
   # uppercased labels as lowercased
   # in this schenma file.
   thing:
       represented_as: node
       label_in_input: thing
   
   mynode:
       represented_as: node
       # The label in input can be anything
       # that comes from the mapping...
       label_in_input: my_mapped_node
   
   myedge:
       represented_as: edge
       # ... or just the same than the type.
       label_in_input: myedge


Now, you have to run OntoWeaver, using all those files::
   
   location=$(ontoweave -C config.yaml -s schema.yaml data.csv:mapping.yaml)

And now, ``echo $(dirname $location)`` will show you  in which directory is the populated OWL file.

The output file should look like a populated OWL file:
.. code-block:: ttl
   :caption: The ``ontology.ttl`` file.
   
   # This part is the same as the input ontology:
   @prefix : <https://my.domain.tld/ontology#> .
   @prefix biocypher: <https://biocypher.org/biocypher#> .
   @prefix owl: <http://www.w3.org/2002/07/owl#> .
   @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

   owl:Thing a rdfs:Class ;
       rdfs:label "Thing" ;
       rdfs:subClassOf biocypher:BioCypherRoot .

   biocypher:BioCypherRoot a rdfs:Class ;
       rdfs:label "BioCypherRoot" .

   :Node a rdfs:Class ;
       rdfs:label "Mynode" ;
       rdfs:subClassOf owl:Thing .

   :Edge a owl:ObjectProperty ;
       rdfs:label "Myedge" ;
       rdfs:subPropertyOf biocypher:BioCypherRoot .

   # This part contains the actual graph data:
   :S1 a owl:NamedIndividual,
           owl:Thing ;
       rdfs:label "S1" ;
       biocypher:id "S1" ;
       biocypher:preferred_id "id" ;
       :myedge :GA,
           :GO .

   :S2 a owl:NamedIndividual,
           owl:Thing ;
       rdfs:label "S2" ;
       biocypher:id "S2" ;
       biocypher:preferred_id "id" ;
       :myedge :GO .

   :GA a owl:NamedIndividual,
           biocypher:Mynode ;
       rdfs:label "GA" ;
       biocypher:id "GA" ;
       biocypher:preferred_id "id" .

   :GO a owl:NamedIndividual,
           biocypher:Mynode ;
       rdfs:label "GO" ;
       biocypher:id "GO" ;
       biocypher:preferred_id "id" .


Common Mapping
~~~~~~~~~~~~~~

The following explanations assume that you are familiar with `Biocypher’s
configuration <https://biocypher.org/tutorial-ontology.html>`__, notably
how it handles ontology alignment with schema configuration.

The minimal configuration would be to map lines and one column, linked
with a single-edge type.

For example, if you have the following CSV table of phenotypes/patients:

::

   phenotype,patient
   0,A
   1,B

and if you target the Biolink ontology, using a schema configuration
(i.e. subset of types), defined in your ``schema_config.yaml`` file, as
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
cell values within a single column. For example, having the table below:

+------+--------------+
| LINE | WORDS        |
+======+==============+
|   0  | sensitive    |
+------+--------------+
|   1  | sensitivity  |
+------+--------------+
|   2  | productive   |
+------+--------------+
|   3  | productivity |
+------+--------------+

You might want to map the column ``WORDS`` based on the word type detected:

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

Type branching based on value from another column
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In some cases the type of the node or edge you would like to assign to a value extracted from the current column depends on the
value extracted from another column. For example, lets look at the following table:

+-----------+--------------+----------+-------+
| furniture | localisation | will_sit?| name  |
+===========+==============+==========+=======+
| chair     | kitchen      | n        | Peter |
+-----------+--------------+----------+-------+
| sofa      | bathroom     | y        | Paul  |
+-----------+--------------+----------+-------+
| fridge    | kitchen      | n        | Mary  |
+-----------+--------------+----------+-------+

In this example we have a table with furniture, their localisation, whether they will be sat on or not, and the name of the person who owns them.

The mapping file for this table could look like this:

.. code:: yaml

    row:
       map:
          id_from_column: furniture
          match_type_from_column: localisation
          match:
            - kitchen:
                to_subject: kitchen_furniture
            - ^(?!kitchen$).*:
                to_subject: rest_of_house_furniture
    transformers:
        - map:
            id_from_column: name
            match_type_from_column: will_sit?
            match:
                - y:
                    to_object: person
                    via_relation: will_sit
                - n:
                    to_object: person
                    via_relation: will_not_sit

With this mapping, we want to map the column ``furniture`` to the node types ``kitchen_furniture`` and
``rest_of_house_furniture`` based on their localisation. The localisation of each piece of furniture is extracted from
the column ``localisation``. The mapping uses the ``match`` clause to apply different type mappings based on the
localisation of the furniture, similarly as it was done in the previous example. This time, however, the ``match`` clause
needs to look at the values of another column — ``localisation``, to determine the type of the node to be created.
In this case, we use the keyword ``match_type_from_column`` to indicate that the type of the node to be created depends
on the value of the ``localisation`` column. The ``id_from_column`` keyword indicates that the identifier of the node to be
created should be taken from the column ``furniture``.

Next, we want to map the column ``name`` to the node type ``person``, and define the edge type based on whether the
furniture will be "sat on" or not. We extract the name of the person from the column ``name``, using the ``id_form_column``
keyword and the edge type will be defined based on the value extracted from the column ``will_sit?``.
The mapping uses the ``match`` clause to apply different type mappings based on the value of the column
``will_sit?``, defined via the ``match_type_from_column`` keyword. The ``match`` clause defines two regex rules:
``y`` which matches the value ``y`` and maps the node type ``person`` via the edge type ``will_sit``, and ``n`` which
matches the value ``n`` and maps the node type ``person`` via the edge type ``will_not_sit``.

This mapping would result in three nodes of type ``person``: ``Peter``, ``Paul``, and ``Mary``, and two nodes of type
``kitchen_furniture``: ``chair`` and ``fridge``, and one node of type ``rest_of_house_furniture``: ``sofa``. The
nodes of type ``person`` would be connected to the nodes of type ``kitchen_furniture`` via an edge of type
``will_not_sit``, and to the node of type ``rest_of_house_furniture`` via an edge of type ``will_sit``.


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

       # Each transformer class should have a ValueMaker nested - class, to define how the value is extracted from the cell.
       # The ValueMaker class should inherit from the ontoweaver.make_value.ValueMaker class.
        class ValueMaker(ontoweaver.make_value.ValueMaker):
            def __init__(self, raise_errors: bool = True):
                super().__init__(raise_errors)

            # The call interface is called when processing a row. Here you should define how the value is extracted from the cell.
            def __call__(self, columns, row, i):

                # We define that for each column name, we should extract the value from the corresponding cell in the row.
                for key in columns:
                    if key not in row:

                        # We raise an error if the column name is not found in the row.
                        self.error(f"Column '{key}' not found in data", section="map.call",
                                   exception=exceptions.TransformerDataError)

                    # Finally, we yield the value of the cell back to the transformer.
                    yield row[key]

       # The constructor is called when parsing the YAML mapping.
        def __init__(self, properties_of, value_maker = ValueMaker(), label_maker = None, branching_properties=None, columns=None, **kwargs):

           # All the arguments passed to the super class are available as member variables.
           super().__init__(properties_of, value_maker, label_maker, branching_properties, columns, **kwargs)

           # If you want user-defined parameters, you may get them from
           # the corresponding member variables (e.g. `self.my_param`).
           # However, if you want to have a default value if they are not declared
           # by the user in the mapping, you have to get them from kwargs:
           self.my_param = kwargs.get("my_param", None) # Defaults to None.

       # The call interface is called when processing a row.
       def __call__(self, row, i):

           # You should take care of your parameters:
           if not self.my_param:
               raise ValueError("You forgot the `my_param` keyword")

            # For each value extracted from the cell, we call the `create` method, which checks the value validity and
            # creates the node and corresponding edge.
            for value in self.value_maker(self.columns, row, i):

                # We yield the value back to the main function.
                yield self.create(value, row)

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
- ``to_object`` = ``to_target`` = ``to_node`` = ``to_type`` = ``to_label``
- ``from_subject`` = ``from_source``
- ``via_relation`` = ``via_edge`` = ``via_predicate``
- ``to_property`` = ``to_properties``
- ``for_object`` = ``for_objects``
- ``final_type`` = ``final_object`` = ``final_label`` = ``final_node`` = ``final_target`` = ``final_subject``
