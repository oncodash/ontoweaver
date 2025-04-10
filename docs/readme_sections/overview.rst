OntoWeaver is a tool for importing table data in Semantic Knowledge
Graphs (SKG) databases.

OntoWeaver allows writing a simple declarative mapping to express how
columns from a `Pandas <https://pandas.pydata.org/>`__ table are to be
converted as typed nodes or edges in an SKG.

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


.. |OntoWeaver logo| image:: docs/OntoWeaver_logo__big.svg
