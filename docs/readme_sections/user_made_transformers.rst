Simple Ad-hoc Transformers
~~~~~~~~~~~~~~~~~~~~~~~~~~

Transformers are the core feature of OntoWeaver.
They are essentially a function object that ingest an atomic piece of data
(e.g. a *row* of a table), transform it, and output a set of nodes and edges.

On top of the transformers provided by OntoWeaver, users can implement their
own. This is especially useful if what you need to do with the data requires
nested loops or if/then constructs, which would be less readable and
maintainable if they were to be implemented with a declarative language.
OntoWeaver takes good care of not providing transformers that would need a
complex YAML configuration, and favors user-defined Python implementation for
such cases.

To implement a transformer, you have several options, from the simplest
*ad-hoc* function-object that will work only on your data (see the next
sections), to the most generic functor that can work on any data (see below).


Simplest User-Defined Transformer
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In essence, a transformer is an object that can be called like a function.
At construction, it can declare the types of nodes and edges it uses,
and it is called as a generator of nodes and edges.

To use such an *ad-hoc* transformer, you would put its name in the mapping,
just like any regular one:

.. code:: yaml

    row:
        map: # A regular transformer.
            column: variant
            to_subject: variant
    tranformers:
        - adhoc: # Our user-defined transformer.
            to_object: patient
            via_relation: patient_has_variant
            # We don't need more options, as every other thing is hard-coded.


Its minimal implementation is straightforward:

.. code:: python

    class adhoc(ontoweaver.transformer.Transformer):

        def __init__(self, **kwargs):
            super().__init__(**kwargs)

            # Declares two type of nodes.
            self.declare_types.make_node_class("patient")
            self.declare_types.make_node_class("variant")

            # Declare one type of edge:
            self.declare_types.make_edge_class("patient_has_variant", "patient", "variant")

        def __call__(self, row, i):
            # Extract only one (patient)--[patient_has_variant]->(variant) edge.
            # The `create` function takes care of the underlying machinery.
            # Note how we don't use the `column` option but hard-code the
            # "patient" column.
            yield self.create(row["patient"], row)


To make a user-defined transformer available from the mapping file, don't forget
to register it.

When calling from the ``ontoweave`` command, pass the path to your module file
with the ``--register`` argument, for example:

.. code:: sh

    ontoweave data.csv:mapping.yaml --register my_transformer.py


If you use your own weaving script, use ``ontoweave.transformer.register``,
for example:

.. code:: python

    import my_transformer
    ontoweaver.transformer.register(my_transformer.adhoc)



Complete User-defined Transformer
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This section shows a slightly more complex ad-hoc transformer, handling explicit
options, properties and a more complex code. However, the architecture is
essentially the same.

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

            # Create branching logic and return correct elements. Elements are returned by using the ``yield`` statement,
            # which yields a tuple containing the node ID, edge type, target node type, and reverse edge type (if any).
            # At each step we can additionally set the ``final_type`` (See ``How to`` section for more details on ``final_type``) and
            # ``properties_of`` member variables, which will be used to extract properties for the current node.

            if relationship_type == "my_relationship_type":
                if entity == "my_entity_type":
                    self.final_type = # Possible to set final type if feature is needed.
                    self.properties_of = self.branching_properties.get("my_target_node_class", {})
                    # Here, we don't use `create` but we are explicit.
                    yield node_id, self.declare_types.get_edge_class("my_edge_class"), self.declare_types.get_node_class("my_target_node_class"), None

                else:  ...

            else: ...

An example of such a transformer-like function is provided in ``tests/custom_transformer/custom.py``.

Once your transformer class is implemented, you should make it available
to the ``ontoweaver`` module which will process the mapping:

.. code:: python

   ontoweaver.transformer.register(my_transformer)


Full-Featured Generic Transformers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you plan on implementing a generic transformer, you will need to understand
the slightly complex machinery that OntoWeaver uses for its generic transformers.

For sych cases, you might need transformers that perform operations using
``ValueMakers`` and ``LabelMakers``.


Value Makers
^^^^^^^^^^^^

``ValueMakers`` are classes that define how to extract values from the cells of desired columns in oder to create node IDs,
edge IDs, or property values. They all represent subclasses of the ``ontoweaver.make_value.ValueMaker`` interface.
Several ``ValueMakers`` are provided by default in OntoWeaver, and come packaged as a nested class in each ``Transforemr`` class.

The example below shows the implementation of a simple ``ValueMaker`` that splits the content of a cell based on a separator.
This is the ``ValueMaker`` used by the ``split`` provided in OntoWeaver.

.. code:: python

    class ValueMaker(make_value.ValueMaker):

        def __init__(self, raise_errors: bool = True, separator: str = None):
            self.separator = separator
            super().__init__(raise_errors)

        def __call__(self, columns, row, i):

            for key in columns:
                items = str(row[key]).split(self.separator)
                for item in items:
                    yield item

Another, more complex, example is the ``ValueMaker`` used by the ``replace`` transformer. This ``ValueMaker`` replaces
forbidden characters in cell values based on a user-defined substitutes.

.. code:: python

    class ValueMaker(make_value.ValueMaker):

        def __init__(self, raise_errors: bool = True, forbidden = None, substitute = None):

            self.forbidden = forbidden
            self.substitute = substitute
            super().__init__(raise_errors)

        def __call__(self, columns, row, i):
            for key in columns:
                logger.debug(
                    f"Setting forbidden characters: {self.forbidden} for `replace` transformer, with substitute character: `{self.substitute}`.")
                formatted = re.sub(self.forbidden, self.substitute, row[key])
                strip_formatted = formatted.strip(self.substitute)
                logger.debug(f"Formatted value: {strip_formatted}")
                yield strip_formatted

In case you need to create your own ``ValueMaker``, you can refer to the examples above, as well as the existing
``ValueMakers`` provided by OntoWeaver, for inspiration.


Label Makers
^^^^^^^^^^^^

Label Makers are classes that define how to extract labels (node and edge types) for your mappings, based on certain criteria.
This criteria is dependant on a member variable of the ``Transformer`` class called the ``multi_type_dictionary``.

This dictionary is a mapping of possible branching values for the node and edge types for a given transformer, extracted from the ``YAML`` file.

All label makers represent subclasses of the ``ontoweaver.make_label.LabelMaker`` interface.

Below we will explain the two main ``LabelMakers`` provided by OntoWeaver: the ``SimpleLabelMaker`` and the ``MultiTypeLabelMaker``.
Other ``LabelMakers`` can be found in the ``ontoweaver.make_label`` module.


SimpleLabelMaker
________________

The simplest ``LabelMaker`` provided by OntoWeaver is the ``SimpleLabelMaker``, which simply returns the type defined
in the mapping file, in case there is no branching. For example, in the following mapping:

.. code:: yaml

        transformers:
            - map:
                columns:
                    - patient
                to_object: patient
                via_relation: patient_has_variant


... the ``multi_type_dictionary`` will look like this:

.. code:: python

    multi_type_dictionary= { "None" : {
                                        'to_object': patient, # The node class. Is normally a class object from ontoweaver.types.
                                        'via_relation': patient_has_variant, # The edge class. Is normally a class object from ontoweaver.types.
                                        'final_type': None # The final type of the node. In this case, None, because not defined in mapping above.
                                        'reverse_relation': None # The reverse edge class. In this case, None, because not defined in mapping above.
                                        }
                            }

The "None" key indicates that there is no branching, and the values are directly extracted from the mapping file.

This ``multi_type_dictionary`` will be processed by the ``SimpleLabelMaker``:

.. code:: python

    class SimpleLabelMaker(LabelMaker):
    """
    The class is used when the transformer does not have any kind of type branching logic.
    """

    def __init__(self, raise_errors: bool = True):
        super().__init__(raise_errors)

    def __call__(self, validate, returned_value, multi_type_dict, branching_properties = None, row = None):

        res = str(returned_value)
        if validate(res):
            if multi_type_dict:
                if "None" in multi_type_dict.keys():
                    # No branching needed. The transformer is not a branching transformer.
                    return ReturnCreate(res, multi_type_dict["None"]["via_relation"], multi_type_dict["None"]["to_object"],
                                        None, multi_type_dict["None"]["final_type"], multi_type_dict["None"]["reverse_relation"])
            else:
                # No multi-type dictionary. The transformer returns only the extracted value of the cell. Used for properties.
                return ReturnCreate(res)
        else:
            # Validation failed, return empty object with None values.
            return ReturnCreate()

The ``SimpleLabelMaker`` simply extracts the values from the ``multi_type_dictionary`` without any branching logic. The
``ReturnCreate`` object holds the values needed to be returned by the transformer.


MultiTypeLabelMaker
____________________

The ``MultiTypeLabelMaker`` is used when there is branching logic defined in the mapping file.

For example, in the following mapping:

.. code:: yaml

    transformers:
        - map:
            column: patient
            match:
                - B:
                    to_object: patient
                    via_relation: patient_has_variant
                - A:
                    final_type: sickness
                    to_object: disease
                    via_relation: variant_to_disease
                - C:
                    to_object: oncogenicity
                    via_relation: variant_to_oncogenicity

... the ``multi_type_dictionary`` will look like this:

.. code:: python

    multi_type_dictionary= { "B" : {
                                        'to_object': patient, # The node class. Is normally a class object from ontoweaver.types.
                                        'via_relation': patient_has_variant, # The edge class. Is normally a class object from ontoweaver.types.
                                        'final_type': None # The final type of the node. In this case, None, because not defined in mapping above.
                                        'reverse_relation': None # The reverse edge class. In this case, None, because not defined in mapping above.
                                        },
                            "A" : {
                                        'to_object': disease,
                                        'via_relation': variant_to_disease,
                                        'final_type': sickness, # The final type of the node defined in the mapping above.
                                        'reverse_relation': None
                                        },
                            "C" : {
                                        'to_object': oncogenicity,
                                        'via_relation': variant_to_oncogenicity,
                                        'final_type': None,
                                        'reverse_relation': None
                                        }
                            }

Notice that the keys of the dictionary are the branching values defined in the mapping file (``A``, ``B``, ``C``).

The ``MultiTypeLabelMaker`` will process this ``multi_type_dictionary`` as follows:

.. code:: python

    class MultiTypeLabelMaker(LabelMaker):
    """
    The class is used when the transformer has type branching logic based on the value that will become the ID of the element.
    """
    def __init__(self,raise_errors: bool = True):
        super().__init__(raise_errors)

    def __call__(self, validate, returned_value, multi_type_dict = None, branching_properties = None, row = None):
        res = str(returned_value)
        if validate(res):
            if multi_type_dict:
                for key, types in multi_type_dict.items():
                    # Branching is performed on the regex patterns.
                    if re.search(key, res):
                        if branching_properties:
                            properties_of = branching_properties.get(types["to_object"].__name__, {})
                        else:
                            properties_of = {}
                        return ReturnCreate(res, types["via_relation"], types["to_object"], properties_of,
                                            types["final_type"], types["reverse_relation"])
                    else:
                        logger.warning(f"Branching key `{key}` does not match extracted value `{res}`.")
                        continue
            else:
                # No multi-type dictionary. The transformer returns only the extracted value of the cell. Used for properties.
                return ReturnCreate(res)
        else:
            # Validation failed, return empty object with None values.
            return ReturnCreate()

In your own user-defined transformers, you can rely on these ``LabelMakers`` to handle the extraction of types based on the mapping file,
or you can create your own ``LabelMaker`` if you need more complex branching logic.


Full-Featured Generic User-Defined Transformers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is easy to create your own transformer, if you want to operate
complex data transformations, but still have them referenced in the
mapping.

This may even be a good idea if you do some pre-processing on the input
table, as it keeps it obvious for anyone able to read the mapping (while
it may be difficult to read the pre-processing code itself).

A user-defined transformer takes the form of a Python class inheriting
from ``ontoweaver.transformer.Transformer``:

.. code:: python

   class my_transformer(ontoweaver.transformer.Transformer):

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

