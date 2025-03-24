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

How to map properties on several nodes of the same type
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In some cases there might be a need to filter properties of the same ontological type. 
For example, if you have a table of proteins defining sources and targets of interactions, and  you want to have the uniProt IDs as a property of these nodes:

====== ====== ================= =================
SOURCE TARGET UNIPROT_ID_SOURCE UNIPROT_ID_TARGET
====== ====== ================= =================
A      B      uniprot_id_A      uniprot_id_B
C      A      uniprot_id_C      uniprot_id_A
====== ====== ================= =================

In a conventional way of mapping, you would map the ``SOURCE`` column to the node type ``protein`` and the ``TARGET`` column to the node type ``protein``. 

By default, OntoWeaver attach properties to all nodes of the *type*. The ``UNIPROT_ID_SOURCE`` and ``UNIPROT_ID_TARGET`` columns would hence be mapped to the type ``protein``.

However, you might want to map the properties of the ``protein`` nodes
either on the *source* or the *target*, but not both. In this case you can
use the ``final_type`` keyword in the mapping configuration. The
``final_type`` keyword allows you to define a *final* node type to which
the node will be converted, at the very end of the mapping process.

In a nutshell: you map the *source* node to a temporary
``protein_source`` and map properties to it. You map the *target* node to a temporary
``protein_target`` and map properties to it. You also set the
``final_type: protein`` , so that, after having mapped all properties,
OntoWeaver will change the node type from the temporary
``protein_source`` and ``protein_target`` to the final ``protein``. Thus, you can attach
different properties to different nodes of the same type.

For example:

.. code:: yaml

   row:
       map:
           column: SOURCE
           to_subject: protein_source # Temporary type.
           final_type: protein # The final type of the node.

   transformers:
       - map:
           column: TARGET
           to_object: protein_target # Temporary type.
           via_relation: protein_protein_interaction
           final_type: protein # The final type of the node.
           
       # Properties of for the node type 'source'
       - map:
           column: UNIPROT_ID_SOURCE
           to_property: uniprot_id # Give name of the property.
           for_object: protein_source # Temporary node type to which the property will be linked.
       # Properties of for the node type 'target'
       - map:
           column: UNIPROT_ID_TARGET
           to_property: uniprot_id
           for_object: protein_target # Temporary node type to which the property will be linked.

Notice how in this way, we avoid mapping the ``source`` properties to
the ``target`` node types, and instead map then to the ``source`` node type.
We also avoid mapping the ``target`` properties to the ``source`` node
types, and instead map them to the ``target`` node type.

 The mapping thus results in the creation of three nodes: ``A``,
``B``, and ``C``, all having the type ``protein``, and the property ``uniprot_id``.

Note that node ``A`` have now been instantiated twice, with different
properties attached to each instance. However, the expected result would
be to have a single instance, with all the properties combined. To solve
this kind of issue, OntoWeaver provides a “reconciliation” feature, that
can be called after the mapping, onto the list of nodes. For more
information see the ``Information Fusion`` section.

An edge of type ``protein_protein_interaction``, will be created from
node ``A`` to node ``B``, as well as from node ``C`` to node ``A``.
