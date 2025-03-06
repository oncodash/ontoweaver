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

How to filter properties of elements of the same ontological type
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In some cases there might be a need to filter properties of the same
ontological type. For example, if you have a table of proteins defining
sources and targets of interactions:

====== ====== =============== ===============
SOURCE TARGET SOURCE_PROPERTY TARGET_PROPERTY
====== ====== =============== ===============
A      B      source_1        target_1
C      A      source_2        target_2
====== ====== =============== ===============

In a conventional way of mapping, you would map the ``SOURCE`` column to
the node type ``protein`` and the ``TARGET`` column to the node type
``protein``. The ``SOURCE_PROPERTY`` and ``TARGET_PROPERTY`` columns
would hence also need to be mapped to the type ``protein``, resulting in
all the nodes - ``A``, ``B``, and ``C`` having all the four properties
attached to them.

However, you might want to filter the properties of the ``protein``
nodes based on the source and target. In this case you can opt for the
usage of the ``final_type`` keyword in the mapping configuration. The
``final_type`` keyword allows you to define a final node type to which
the source and target nodes will be converted. For example:

.. code:: yaml

   row:
       map:
           column: SOURCE
           to_subject: source # Subtype of protein.
           final_type: protein # The final type of the node.

   transformers:
       - map:
           column: TARGET
           to_object: target # Subtype of protein.
           via_relation: protein_protein_interaction
           final_type: protein # The final type of the node.
           
       # Properties of for the node type 'source'
       - map:
           column: SOURCE_PROPERTY
           to_property: genesymbol # Give name of the property.
           for_object: source # Node type to which the property will be linked.
       # Properties of for the node type 'target'
       - map:
           column: TARGET_PROPERTY
           to_property: genesymbol
           for_object: target # Node type to which the property will be linked.

Notice how in this way, we avoid mapping the ``source`` properties to
the ``target`` node types, and instead map then to the source node type.
The vice-versa is also true, we avoid mapping the ``target`` properties
to the ``source`` node types, and instead map them to the target node
type.

This way, were it not for the ``final_type: protein`` clause, the
``source`` and ``target`` nodes would have been created with their own
respective segregated properties. Notice that there would be two types
of the node ``A`` created, one with the ``source_1`` property, and the
type of the node being ``source``, and the other with the ``target_1``
property, and the type of the node being ``target``.

However, with the ``final_type: protein`` clause, the ``source`` and
``target`` nodes are converted to their supertype ``protein``
on-the-fly, and the mapping results in the creation of three nodes:
``A``, ``B``, and ``C``, all holding the type ``protein``. Node ``A``
will have, following reconciliation (for more information see the
``Information Fusion`` section), the properties ``source_1`` and
``target_2``, node ``B`` will have the property ``target_1``, and node
``C`` will have the property ``source_2``.

An edge of type ``protein_protein_interaction``, will be created from
node ``A`` to node ``B``, as well as from node ``C`` to node ``A``.
