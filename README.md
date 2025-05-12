# OntoWeaver

OntoWeaver is a tool for transforming tabular data in
Semantic Knowledge Graphs (SKG) databases.

OntoWeaver allows writing a simple declarative mapping to express how columns from
a table should be converted as typed nodes, edges, or properties in an SKG.

![](docs/OntoWeaver_simple-summary.svg)

SKG databases allow for an easy integration of very heterogeneous data, and
OntoWeaver brings a reproducible approach to building them.

With OntoWeaver, you can very easily implement a script that will allow you
to automatically reconfigure a new SKG from the input data, each time you need it.

OntoWeaver has been tested on large scale biomedical use cases, and we can
guarantee that it is simple to operate by anyone having a basic knowledge
of programming.


## Basics

OntoWeaver provides a simple layer of abstraction on top of [Biocypher](https://biocypher.org),
which remains responsible for doing the ontology alignment,
supporting several graph database backends,
and allowing reproducible & configurable builds.

With a pure Biocypher approach, you would have to write a whole adapter by hand,
with OntoWeaver, you just have to express a mapping in YAML, looking like:
```yaml
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
```

OntoWeaver can read anything that [Pandas](https://pandas.pydata.org/) can load,
which means a lot of tabular formats.


### Installation

The project is written in Python and uses [Poetry](https://python-poetry.org).
You can install the necessary dependencies in a virtual environment like this:

```
git clone https://github.com/oncodash/ontoweaver.git
cd ontoweaver
poetry install
```

Poetry will create a virtual environment according to your configuration (either
centrally or in the project folder). You can activate it by running `poetry
shell` inside the project directory.

Theoretically, the graph can be imported in
any [graph] database supported by BioCypher
(Neo4j, ArangoDB, CSV, RDF, PostgreSQL, SQLite, NetworkX, …
see [BioCypher's documentation](https://biocypher.org/output/index.html)).


### Usage Documentation

Detailed documentation with tutorials and a more detailed installation guide is available
[on the OntoWeaver website](https://ontoweaver.readthedocs.io/en/latest/).


### Tests

Tests are located in the `tests/` subdirectory and may be a good starting point
to see OntoWeaver in practice. You may start with `tests/test_simplest.py` which
shows the simplest example of mapping tabular data through BioCypher.

To run tests, use `pytest`:
```
poetry run pytest
```


### Contributing

In case of any questions or improvements feel free to open an issue or a pull request!

