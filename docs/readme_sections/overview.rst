OntoWeaver is a tool for importing iterable data in Semantic Knowledge
Graphs (SKG) databases.

For instance, OntoWeaver allows writing a simple declarative mapping to express
how items from an iterable dataset (e.g. a CSV table or a JSON file) are to be
converted as typed nodes or edges in an SKG.

With OntoWeaver, you have to express a "mapping" in simple declarative language,
following the YAML syntax.

To map tabular data, this would look like:

.. code:: yaml

   row: # The meaning of an entry in the input table.
      map:
         column: <column name in your CSV>
         to_subject: <ontology node type to use for representing a row>

   transformers:  # How to map cells to nodes and edges.
       - map:  # Map a column to a node.
           column: <column name>
           to_object: <ontology node type to use for representing a column>
           via_relation: <edge type for linking subject and object nodes>
       - map:  # Map a column to a property.
           column: <another name>
           to_property: <property name>
           for_object: <type holding the property>

   metadata:  # Optional properties added to every node and edge.
       - source: "My OntoWeaver adapter"
       - version: "v1.2.3"


You then run a command to transform your data in an SKG:

.. code:: sh

   ontoweave my_data.csv:my_mapping.yaml


.. note::

   OntoWeaver provides a simple layer of abstraction on top of
   `BioCypher <https://biocypher.org>`__, which remains responsible for
   doing the ontology alignment, supporting several graph database
   backends, and allowing reproducible & configurable builds.
   You may want to read its documentation too.

