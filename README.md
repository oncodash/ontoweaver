# OntoWeaver

## Overview

OntoWeaver is a Python module for importing tables data in
Semantic Knowledge Graphs (SKG) databases.

OntoWeaver allows to write a simple declarative mapping to express how columns from
a [Pandas](https://pandas.pydata.org/) table are to be converted as typed nodes
or edges in a SKG.

It provides a simple layer of abstraction on top of [Biocypher](https://biocypher.org),
which remains responsible for doing the ontology alignment,
supporting several graph database backend,
and allowing reproducible & configurable builds.

With a pure Biocypher approach, you would have to write a whole adapter by hand,
with OntoWeaver, you just have to express a mapping in YAML, looking like:
```yaml
subject: <line_node_type>
columns:
    <column_name>:
        to_object: <col_node_type>
        via_relation: <edge_type>
```

## Installation

### Python Module

The project uses [Poetry](https://python-poetry.org). You can install like this:

```
git clone https://github.com/oncodash/ontoweaver.git
cd ontoweaver
poetry install
```

Poetry will create a virtual environment according to your configuration (either
centrally or in the project folder). You can activate it by running `poetry
shell` inside the project directory.


### Database

Theoretically, any graph database supported by Biocypher may be used.


### Tests

Tests are located in the `tests/` subdirectory and may be a good starting point
to see OntoWeaver in practice. You may start with `tests/test_simplest.py` which
shows the simplest example of mapping tabular data through BioCypher.

To run tests, use `pytest`:
```
poetry run pytest
```
or, alternatively:
```
poetry shell
pytest
```


## Usage

OntoWeaver actually automatically provides a working adapter for BioCypher,
without you having to do it.
To actually insert data in a SKG database, you will have to use Biocypher
export API:
```python
    import yaml
    import logging
    import pandas as pd
    import biocypher
    import ontoweaver

    # Load ontology
    bc = biocypher.BioCypher(
        biocypher_config_path = "tests/simplest/biocypher_config.yaml",
        schema_config_path = "tests/simplest/schema_config.yaml"
    )

    # Load data
    table = pd.read_csv("tests/simplest/data.csv")

    # Load mapping
    with open("tests/simplest/mapping.yaml") as fd:
        mapping = yaml.full_load(fd)

    # Run the adapter
    adapter = ontoweaver.tabular.extract_all(table, mapping)

    # Write nodes
    bc.write_nodes( adapter.nodes )

    # Write edges
    bc.write_edges( adapter.edges )

    # Write import script
    bc.write_import_call()

    # Now you have a script that you can run to actually insert data.
```
Additionally, you will have to define a strategy for the naming of mapped items when creating nodes, by defining an `affix` and `separator`
to be used during node creation. The `affix` used will represent the ontology type of the item in question. Unless otherwise defined, 
the `affix` defaults to `suffix` and `separator` defaults to `:`. This can be modified by changing the variables in the
`extract_all()` function. `Affix` can be either a `prefix`, `suffix` or `none` - in case you decide not to include the ontology type in 
the node naming strategy. Special care should be exercised in case there are several types of the same name in the database. There is a 
possibility that nodes of the same name will be merged together during mapping, so an `affix` should be present. Below are some examples of
node naming strategies. `NAME` refers to the name of the item in question in your database, and `TYPE` refers to the type of the item 
in the ontology.
```python
...

   # Affix defaults to "suffix", and separator defaults to ":"
   # Node represented as [NAME]:[TYPE]
   adapter = ontoweaver.tabular.extract_all(table, mapping)
   
   # Node represented as [TYPE]-[NAME]
   adapter = ontoweaver.tabular.extract_all(table, mapping, affix = "prefix", separator = "-")
   
   # Node represented as [NAME] 
   adapter = ontoweaver.tabular.extract_all(table, mapping, affix = "none")

...
```




## Mapping API

OntoWeaver essentially creates a Biocypher adapter from the description of a
mapping from a table to ontology types.
As such, its core input is a dictionary, that takes the form of a YAML file.
This configuration file indicates:

- to which (node) type are mapped each line of the table,
- to which (node) type are mapped columns of the table,
- with which (edge) type are mapped relationships between nodes.

The following explanations assume that you are familiar with
[Biocypher's configuration](https://biocypher.org/tutorial-ontology.html),
notably how it handles ontology alignment with
schema configuration.


### Common Mapping

The minimal configuration would be to map lines and one column, linked with
a single edge type.

For example, if you have the following CSV table of phenotypes/patients:
```
phenotype,patient
0,A
1,B
```
and if you target the Biolink ontology, with the following schema
(i.e. subset of types):
```yaml
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
```
you may write the following mapping:
```yaml
subject: phenotype
columns:
    patient: # Name of the column in the table.
        to_object: case # Node type to export to (most probably the same than in the ontology).
        via_relation: case_to_phenotype # Edge type to export to.
```

This configuration will end in creating a node for each phenotype, a node
for each patient, and an edge for each phenotype-patient pair:
```
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
```


### Relation between Columns Nodes

If you need to add an edge between a column node to another (and not between
the line node and a column node), you can use the `from_subject` predicate,
for example:
```yaml
subject: phenotype
columns:
    patient:
        to_object: case
        via_relation: case_to_phenotype
    disease:
        from_subject: case # The edge will start from this node type...
        to_object: disease # ... to this node type.
        via_relation: disease to entity association mixin
```

```
           ╭───────────────────╮
           │              ╔════╪════╦════════════════════╗
           │              ║pati│ent ║      disease       ║
           │              ╠════╪════╬════════════════════╣
           │              ║    │    ║disease to          ║
           │              ║    │    ║entity              ║
╭──────────┴──────────╮   ║╭───┴───╮║  ↓    ╭───────────╮║
│phenotypic feature: 0│   ║│case: A├╫───────┤ disease: X│║
╰─────────────────────╯   ║╰───────╯║       ╰┬──────────╯║
                          ╠═════════╬════════╪═══════════╣
╭─────────────────────╮   ║╭───────╮║       ╭┼╌╌╌╌╌╌╌╌╌╌╮║
│          1          │   ║│   B   ├╫────────╯    X     ┆║
╰──────────┬──────────╯   ║╰───┬───╯║       ╰╌╌╌╌╌╌╌╌╌╌╌╯║
           │              ╚════╪════╩════════════════════╝
           ╰───────────────────╯
```

### Properties

If you do not need to create a new node, but simply attach some data to an existing
node, use the `to_property` predicate, for example:
```yaml
subject: phenotype
columns:
    patient:
        to_object: case
        via_relation: case_to_phenotype
    age: # Name of the column.
        to_property:
            patient_age: # Name of the property.
                - case # Type(s) in which to add the property.
```
This will add an "age" property to nodes of type "case".

Note that you can add the same property to several types.


### Transformers

If you want to transform a data cell before exporting it as one or several
nodes, you will use *transformers*.

#### `split`

The *split* transformer separates a string on a separator, into several items,
and then insert a node for each element of the list.

For example, if you have a list of treatments separated by a semicolon,
you may write:
```yaml
subject: phenotype
columns:
    variant:
        to_object: variant
        via_relation: phenotype to variant
    treatments:
        into_transformer:
            split:
                separator: ";"
            from_object: variant
            to_object: drug
            via_relation: variant_to_drug
```

```
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
```

It is worth noting that the underlying code is very simple:
```python
class split(base.EdgeGenerator):
    def nodes(self):
       for i in self.id.split(self.separator):
           yield self.make_node(id = i)

    def edges(self):
       for i in self.id_target.split(self.separator):
           yield self.make_edge(id_target = i)
```


### Keywords Synonyms

Because several communities gathered around semantic knowledge graph,
several terms can be used (more or less) interchangeably.

OntoWeaver thus allows to use your favorite vocabulary to write down
the mapping configurations.

Here is the list of available synonyms:

- `subject` = `row` = `entry` = `line` = `source`
- `columns` = `fields`
- `to_object` = `to_target` = `to_node`
- `from_subject` = `from_source`
- `via_relation` = `via_edge` = `via_predicate`
- `to_property` = `to_properties`
- `into_transformer` = `into_generator` = `into_gen`, `into_trans`


### User-defined Classes

#### Dynamic Node and Edge Types

OntoWeaver relies a lot on meta-programming, as it actually creates
Python types while parsing the mapping configuration.
By default, those classes are dynamically created into the `ontoweaver.types`
module.

You may manually define your own types, derivating from `ontoweaver.base.Node`
or `ontoweaver.base.Edge`.

The `ontoweaver.types` module automatically gather the list of available types
in the `ontoweaver.types.all` submodule.
This allows accessing the list of node and edge types:
```python
node_types  = types.all.nodes()
edge_types  = types.all.edges()
```


#### User-defined Adapters

You may manually define your own adapter class, inheriting
from the OntoWeaver's class that manages tabular mappings.

For example:
```python
class MYADAPTER(ontoweaver.tabular.PandasAdapter):

    def __init__(self,
        df: pd.DataFrame,
        config: dict,
        node_types : Optional[Iterable[ontoweaver.Node]] = None,
        node_fields: Optional[list[str]] = None,
        edge_types : Optional[Iterable[ontoweaver.Edge]] = None,
        edge_fields: Optional[list[str]] = None,
    ):
        # Default mapping as a simple config.
        from . import types
        mapping = self.configure(config, types)

        # If "None" is passed (the default), then do not filter anything
        # and just extract all available types.
        if not node_types:
            node_types  = types.all.nodes()
            logging.debug(f"node_types: {node_types}")

        if not node_fields:
            node_fields = types.all.node_fields()
            logging.debug(f"node_fields: {node_fields}")

        if not edge_types:
            edge_types  = types.all.edges()
            logging.debug(f"edge_types: {edge_types}")

        if not edge_fields:
            edge_fields = types.all.edge_fields()
            logging.debug(f"edge_fields: {edge_fields}")

        # Declare types defined in the config.
        super().__init__(
            df,
            *mapping,
            node_types,
            node_fields,
            edge_types,
            edge_fields,
        )
```


#### Multiple Subjects

If you need to change the subject's (line) type depending on the value of
some field, you will have to declare your own adapter class, and overload
the `source_type` method.

For example:
```python
    def source_type(self, row):
        from . import types
        if row["alteration"].lower() == "amplification":
            return types.amplification
        elif row["alteration"].lower() == "loss":
            return types.loss
        else:
            logging.debug(f"Source type is `variant`")
            return types.variant
```

The same goes for defining the *ID* of the subject, for example:
```python
    def source_id(self, i, row):
        id = "{}".format(row["patient_id"])
        logging.debug("Source ID is `{}`".format(id))
        return "{}".format(id)
```


#### Multiple Relations

If you need to add an additional edge from the current node to another one,
you will need to overload the `end` method.

For example:
```python
    def end(self):
        from . import types
        for i,row in self.df.iterrows():
            sid = row["sample_id"]
            pid = row["patient_id"]
            logging.debug(f"Add a `sample_to_patient` edge between `{sid}` and `{pid}`")
            self.edges_append( self.make_edge(
                types.sample_to_patient, id=None,
                id_source=sid, id_target=pid
            ))
```

