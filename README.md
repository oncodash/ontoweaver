# OntoWeaver

OntoWeaver is a tool for transforming iterable data (like tables)
in Semantic Knowledge Graphs (SKG) databases.

OntoWeaver allows writing a simple declarative mapping to express how columns from
a table should be converted as typed nodes, edges or properties in an SKG.

![Diagram showing that OntoWeaver needs ontologies, tabular data and graph schema to produce a Semantic Knowledge Graph.](https://raw.githubusercontent.com/oncodash/ontoweaver/refs/heads/main/docs/OntoWeaver__simple-summary.svg)


SKG databases allows for an easy integration of very heterogeneous data, and
OntoWeaver brings a reproducible approach to building them.

With OntoWeaver, you can very easily implement a script that will allow you
to automatically reconfigure a new SKG from the input data, each time you need it.

OntoWeaver has been tested on large scale biomedical use cases
(think: millions of nodes), and we can guarantee that it is simple to operate
by anyone having a basic knowledge of programming.


## Basics

### Mapping data

OntoWeaver provides a simple layer of abstraction on top of [BioCypher](https://biocypher.org),
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
which means a lot of tabular formats. It can also parse graphs from OWL files.


### Usage

To configure your SKG, you need input data, a mapping (see above), but also
a BioCyhper configuration: a [schema.yaml](https://biocypher.org/BioCypher/learn/tutorials/tutorial001_basics/#schema-configuration) and a [ibiocypher_config.yaml](https://biocypher.org/BioCypher/reference/biocypher-config/).

In most cases, you will just need to call the `ontoweave` command to build-up
the SKG you prepared:

```sh
ontoweave my_data.csv:my_mapping.yaml --import-script-run
```

The `ontoweave` command is very configurable, see `ontoweave --help` for more
details.

Detailed documentation with tutorials and a more detailed installation guide is available
[on the OntoWeaver website](https://ontoweaver.readthedocs.io/en/latest/).


### Installation

The project is written in Python and is tested with the
[UV](https://docs.astral.sh/uv/) environment manager.
You can install the necessary dependencies in a virtual environment like this:

```
git clone https://github.com/oncodash/ontoweaver.git
cd ontoweaver
uv build
```

UV will create a virtual environment according to your configuration (either
centrally or in the project folder).
You can then run any script with `uv run` and it should just work.

Theoretically, OntoWeaver can export a knowledge graph in any of the formats
supported by BioCypher (Neo4j, ArangoDB, CSV, RDF, PostgreSQL, SQLite, NetworkX, …
see [BioCypher's documentation](https://biocypher.org/output/index.html)).


## Development

### Tests

Tests are located in the `tests/` subdirectory and may be a good starting point
to see OntoWeaver in practice. You may start with `tests/test_simplest.py` which
shows the simplest example of mapping tabular data through BioCypher.

To run tests, use `pytest`:
```
uv run pytest
```


### Contributing

In case of any questions or improvements feel free to open an issue or a pull request!

