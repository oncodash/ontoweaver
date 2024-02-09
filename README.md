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
```
subject: <node_type>
<column_name>:
   to_object: <node_type>
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


## Usage

