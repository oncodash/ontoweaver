How To
------

How to Add Properties to Nodes and Edges
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you do not need to create a new node, but simply attach some data to
an existing node, use the ``to_property`` predicate, for example:

.. code:: yaml

   row:
      rowIndex:
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

.. note::
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

.. note::
   Note that the properties declared in the BioCypher ``schema_config.yaml`` must match the properties declared in the mapping configuration file.
   Furthermore, when declaring the properties in the schema configuration file, take care that the property must always be a
   string (``str``) type - in order to avoid errors when importing the data into the Neo4j graph database.

How to Extract Additional Edges
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Edges can be extracted from the mapping configuration, by defining a
``from_subject`` and ``to_object`` in the mapping configuration, where
the ``from_subject`` is the node type from which the edge will start,
and the ``to_object`` is the node type to which the edge will end.

For example, for the sample dataset below:

+----+----------+---------+
| id | patient  | sample  |
+====+==========+=========+
| 0  | patient1 | sample1 |
+----+----------+---------+
| 1  | patient2 | sample2 |
+----+----------+---------+
| 2  | patient3 | sample3 |
+----+----------+---------+
| 3  | patient4 | sample4 |
+----+----------+---------+

Consider the following mapping configuration:

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
*node*.

.. note::
   Note that this is not added to *edges*, because they are not
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

By default, OntoWeaver will attach properties to all nodes of the same *type*. The ``UNIPROT_ID_SOURCE`` and ``UNIPROT_ID_TARGET`` columns would hence be mapped as properties to the type ``protein``.

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

.. note::
   Notice how in this way, we avoid mapping the ``source`` properties to
   the ``target`` node types, and instead map then to the ``source`` node type.
   We also avoid mapping the ``target`` properties to the ``source`` node
   types, and instead map them to the ``target`` node type.

The mapping thus results in the creation of three nodes: ``A``,
``B``, and ``C``, all having the type ``protein``, and the property ``uniprot_id``.

.. note::
   Note that node ``A`` have now been instantiated twice, with different
   properties attached to each instance. However, the expected result would
   be to have a single instance, with all the properties combined. To solve
   this kind of issue, OntoWeaver provides a “reconciliation” feature, that
   can be called after the mapping, onto the list of nodes. For more
   information see the ``Information Fusion`` section.

An edge of type ``protein_protein_interaction``, will be created from
node ``A`` to node ``B``, as well as from node ``C`` to node ``A``.

How to Extract Reverse Relations For Declared Edges
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Reverse relations can be extracted for each edge in a declarative manner.
Let's assume you have a mapping file mapping each row index to the node type `disease`, and each cell value from the
`patient` column to the node type `patient`. The two nodes are connected via a relation `disease_affects_patient`, but you
would also wish to indicate a reverse edge of type `patient_has_disease`.

This can be done by using the `reverse_relation` keyword, which extracts the reverse edge of the type you declared. You
may consult the ``Keyword Synonyms`` section for more synonyms.

.. code:: yaml

   row:
      rowIndex:
         to_subject: disease
   transformers:
       - map:
           column: patient
           to_object: patient
           via_relation: disease_affects_patient
           reverse_relation: patient_has_disease

How to Compose Multiple Transformers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Custom transformers (See the ``User-defined Transformers`` and ``User-defined Transformer-Like Functions`` sections) can
be configured to compose multiple transformers together. This is useful when you want to apply a series of transformations
to your data.

For example, let's look again at the example provided in the ``User-defined Transformer-Like Functions`` section.

Below we declare a custom transformer `MyTransformer`, which branches based on the values of the `type` and `entity_type_target` columns.

What if, instead of simply returning the extracted ``node_id``, ``edge_type``, ``target_node_type``, and ``reverse_relation``, we wanted to apply
a concatenation transformer (See ``cat``) to the ``node_id`` before yielding it?

In this case we can instantiate a concatenation transformer inside our custom transformer, and apply it to the ``node_id`` with the
desired columns which values are to be concatenated, and later yield the results of this concatenation.

The example below follows the exact logic of the ``MyTransformer`` class we created in the ``User-defined Transformer-Like Functions`` section,
but instantiates a concatenation transformer in the ``__init__`` method. This ``cat`` transformer is then called in the ``__call__``
method to concatenate the values of the desired columns before yielding the results.

.. code:: python


    from ontoweaver import transformer, validate
    from ontoweaver import types as owtypes

    class MyTransformer(transformer.Transformer):
        """Custom end-user transformer."""

        def __init__(self, properties_of, value_maker = None, label_maker = None, branching_properties = None, columns=None, output_validator: validate.OutputValidator = None, multi_type_dict = None, raise_errors = True, **kwargs):

            super().__init__(properties_of, value_maker, label_maker, branching_properties, columns, output_validator,
                             multi_type_dict, raise_errors=raise_errors, **kwargs)

            # First declare all node and edge classes needed for your mapping. The declaration is done by using the
            # `declare_types` member variable, which is an instance of the ``ontoweaver.base.Declare`` class. Node classes are
            # declared by using the `` self.declare_types.make_node_class`` function. We first declare the name of the
            # possible source and target node classes (``my_source_node_class``, ``my_target_node_class``, ``another_node_class"``).
            # Then we extract the properties of those node classes from the `branching_properties` member variable, which is a dictionary
            # containing all the properties defined in the mapping file for each node and edge class (``self.branching_properties.get("my_source_node_class", {})``).

            self.declare_types.make_node_class("my_source_node_class", self.branching_properties.get("my_source_node_class", {}))
            self.declare_types.make_node_class("my_target_node_class", self.branching_properties.get("my_target_node_class", {}))
            self.declare_types.make_node_class("another_node_class", self.branching_properties.get("another_node_class", {}))

            # Edge classes are declared by using the `` self.declare_types.make_edge_class`` function. Again, we declare the
            # name of the edge class (``my_edge_class``) and the source and target node classes it connects. These are
            # retrieved by using the ``getattr`` function on the ``types`` module, which contains all the declared types in the ontology, as
            # well as the node classes we just declared above (``getattr(owtypes, "my_source_node_class")``) .
            # Finally, we extract the properties of the edge class from the ``branching_properties`` member variable
            # (``self.branching_properties.get("my_edge_class", {})``)

            self.declare_types.make_edge_class("my_edge_class", getattr(owtypes, "my_source_node_class"), getattr(owtypes, "my_target_node_class"), self.branching_properties.get("my_edge_class", {}))

            # We instantiate a cat transformer to concatenate the columns ``column1`` and ``column2``. We pass the properties of the
            # target node class ``my_target_node_class``. We also define a multi_type_dict to indicate the possible types of the target node class.
            # We instantiate a ``multi_type_dict`` which holds the information about possible branching needed for the
            # types created by the transformer. Since the branching logic is already handled by our custom made transformer, we only need to
            # define a single entry in the ``multi_type_dict``. In this case we define a single entry for the key ``None``
            # (indicating no branching is needed), along with the corresponding ``to_object``, ``via_relation``, ``final_type``, and ``reverse_relation``
            # values. Finally, we use a ``SimpleLabelMaker`` to create labels for the concatenated nodes.

            self.cat = transformer.cat(columns=["target", "entity_type_target"],
                                        properties_of=self.branching_properties.get("my_target_node_class", {}),
                                        multi_type_dict={"None" : {"to_object": getattr(owtypes, "my_target_node_class"),
                                                                   "via_relation" : getattr(owtypes, "my_edge_class"),
                                                                   "final_type": None,
                                                                   "reverse_relation": None}},
                                        label_maker=make_labels.SimpleLabelMaker())


        def __call__(self, row, i):

            # Initialize final type and properties_of member variables to ``None`` for each row processed. This is beacuase
            # the final type and properties may change depending on the values extracted from the current row.

            self.final_type = None
            self.properties_of = None

            # Extract branching information from the current row, as well as node ID. We branch based on the values of the
            # ``type`` and ``entity_type_target`` columns.

            node_id = row["target"]
            relationship_type = row["type"]
            entity = row["entity_type_target"]

            # Create branching logic and return correct elements. Elements are returned by using the ``yield`` statement,
            # which yields a tuple containing the node ID, edge type, target node type, and reverse edge type (if any).
            # At each step we can additionally set the ``final_type`` (See ``How to`` section for more details on ``final_type``) and
            # ``properties_of`` member variables, which will be used to extract properties for the current node.

            if relationship_type == "my_relationship_type":
                if entity == "my_entity_type":
                    self.properties_of = self.branching_properties.get("my_target_node_class", {})
                    # We call the ``cat`` transformer to concatenate the desired columns before yielding the results.
                    for node_id, edge_type, target_type, reverse_relation in self.cat(row, i):
                        yield node_id, edge_type, target_type, reverse_relation

                else:  ...

            else: ...


How to Declare Properties On-the-Fly
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Similarly as with the composition of transformers and their declaration on-the-fly within custom transformers, property
transformers can also be declared on-the-fly within custom transformers.

For example, let's use the same custom transformer `MyTransformer` from the previous sections
(See the ``User-defined Transformers`` and ``User-defined Transformer-Like Functions`` sections) .

Let's say you have two columns in your database called ``property_key`` and ``property_value``, and you want to map these
columns as properties to the target node type.

You can declare a property transformer on-the-fly within your custom transformer, in the ``properties_of`` member variable.

.. code:: python

    from ontoweaver import transformer, validate
    from ontoweaver import types as owtypes

    class MyTransformer(transformer.Transformer):
        """Custom end-user transformer."""

        def __init__(self, properties_of, value_maker = None, label_maker = None, branching_properties = None, columns=None, output_validator: validate.OutputValidator = None, multi_type_dict = None, raise_errors = True, **kwargs):

            super().__init__(properties_of, value_maker, label_maker, branching_properties, columns, output_validator,
                             multi_type_dict, raise_errors=raise_errors, **kwargs)

            # First declare all node and edge classes needed for your mapping. The declaration is done by using the
            # `declare_types` member variable, which is an instance of the ``ontoweaver.base.Declare`` class. Node classes are
            # declared by using the `` self.declare_types.make_node_class`` function. We first declare the name of the
            # possible source and target node classes (``my_source_node_class``, ``my_target_node_class``, ``another_node_class"``).
            # Then we extract the properties of those node classes from the `branching_properties` member variable, which is a dictionary
            # containing all the properties defined in the mapping file for each node and edge class (``self.branching_properties.get("my_source_node_class", {})``).

            self.declare_types.make_node_class("my_source_node_class", self.branching_properties.get("my_source_node_class", {}))
            self.declare_types.make_node_class("my_target_node_class", self.branching_properties.get("my_target_node_class", {}))
            self.declare_types.make_node_class("another_node_class", self.branching_properties.get("another_node_class", {}))

            # Edge classes are declared by using the `` self.declare_types.make_edge_class`` function. Again, we declare the
            # name of the edge class (``my_edge_class``) and the source and target node classes it connects. These are
            # retrieved by using the ``getattr`` function on the ``types`` module, which contains all the declared types in the ontology, as
            # well as the node classes we just declared above (``getattr(owtypes, "my_source_node_class")``) .
            # Finally, we extract the properties of the edge class from the ``branching_properties`` member variable
            # (``self.branching_properties.get("my_edge_class", {})``)

            self.declare_types.make_edge_class("my_edge_class", getattr(owtypes, "my_source_node_class"), getattr(owtypes, "my_target_node_class"), self.branching_properties.get("my_edge_class", {}))


        def __call__(self, row, i):

            # Initialize final type and properties_of member variables to ``None`` for each row processed. This is beacuase
            # the final type and properties may change depending on the values extracted from the current row.

            self.final_type = None
            self.properties_of = None

            # Extract branching information from the current row, as well as node ID. We branch based on the values of the
            # ``type`` and ``entity_type_target`` columns.

            node_id = row["target"]
            relationship_type = row["type"]
            entity = row["entity_type_target"]

            # Here we extract the value of the property key column.
            property_key = row["property_key"]

            # Create branching logic and return correct elements. Elements are returned by using the ``yield`` statement,
            # which yields a tuple containing the node ID, edge type, target node type, and reverse edge type (if any).
            # At each step we can additionally set the ``final_type`` (See ``How to`` section for more details on ``final_type``) and
            # ``properties_of`` member variables, which will be used to extract properties for the current node.

            if relationship_type == "my_relationship_type":
                if entity == "my_entity_type":
                    self.final_type = # Possible to set final type if feature is needed.
                    # We then declare a property transformer on-the-fly within the ``properties_of`` member variable.
                    # setting ``property_key`` as the property name, and the  ``property_value`` column as the property value
                    # to be extracted.
                    self.properties_of = {transformer.map(columns="property_value", properties_of=None, label_maker=make_labels.SimpleLabelMaker()): property_key}
                    yield node_id, getattr(owtypes, "my_edge_class"), getattr(owtypes, "my_target_node_class"), None

                else:  ...

            else: ...

In case of using this feature, remember to include all the dynamically created properties in the schema configuration file of BioCypher.

