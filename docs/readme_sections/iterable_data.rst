Iterable input data
-------------------

OntoWeaver iterates over input data, and creates nodes and edges at each steps.

The simplest example of iterable data is a table, which OntoWeaver will consume
line by line, creating node(s) and edge(s) at each step.

However, technically, OntoWeaver can consume any iterable data, providing that
it has an "Adapter" class knowing how to do it.

For a basic usage through the `ontoweave` command, OntoWeaver will guess the
input data type from the input file extension. Thus, in theory, you will not
have to do anything special to consume a data file of a supported type;
even the mapping would work for any input data type.

The following sections show the available input data adapters.


Tabular data
~~~~~~~~~~~~

Tables being the most ubiquituous data structure, they is used as the main
example across OntoWeaver documentation, as you may have seen in the previous
sections.

The basic processing of a table is to iterate over each row,
and map from column names to element types.

Tables can be in any format that Pandas can read.
The automatic input data type detection can handle the following
formats/extensions:
csv, tsv, txt,  xls, xlsx, xlsm, xlsb, odf, ods, odt,  json, html, xml, hdf,
feather, parquet, pickle, orc, sas, spss, stata.


Web Ontology data
~~~~~~~~~~~~~~~~~

Existing Semantic Knowledge Graphs are often distributed in files containing
the taxonomy of types, some logical predicates for reasonning and the graph of
individual instances itself.
These files are called "ontologies", and come in various formats and dialects.
The *de facto* standard for ontologies is the Web Ontology Language (
`OWL <https://en.wikipedia.org/wiki/Web_Ontology_Language>`_,
a superset of
`RDF <https://en.wikipedia.org/wiki/Resource_Description_Framework>`_).

Just as BioCypher can read a taxonomy from an ontology file,
OntoWeaver can iterate over the graph of individuals in an ontology file,
and import them as pieces of data.

.. note::
   Biocypher incorrectly calls *a taxonomy defined in an ontology file*
   "an ontology", for the sake of simplicity.

More specifically, OntoWeaver can import RDF triples which predicate is
`owl:NamedIndividual`.

OntoWeaver can read ontology files written in the RDF dialects that
`RDFlib <https://rdflib.readthedocs.io>`_ can read:
owl, xml, n3, turtle, ttl, nt, trig, trix, json-ld.


OWL & automap
^^^^^^^^^^^^^^^^

The simplest way to read the input data from an ontology file is to use
the *automatic* OWL adapter.
This adapter can be used by passing the ``automap`` keyword in place of a mapping
file into the ``ontoweave`` command, or the ``weave`` function:

.. code:: sh

   ontoweave my_ontology.ttl:automap

This will automatically map the individuals defined into the input graph found
in the ontology file to the types found in the taxonomy of the *same* ontology
file.
Using this ``OWLAutoAdapter``, you thus don't need to define a mapping, it will
be automatically extracted from the input ontology file.

Of course, this adapter will expect that the classes defined in the input
ontology exist in the taxonomy configured by BioCypher.

.. note::
   BioCypher allows to assemble several taxonomies into a single one.
   This configured taxonomy should have the types that the graph loaded by
   OntoWeaver is using, or else a missing type error will occur.
   For instance, if you use a `root` type that's not the root of a
   (sub)taxonomy, a (possibly large) part of the (sub)taxonomy will be ignored
   by BioCypher, and thus invisible to OntoWeaver's extracted graph.

.. warning::
   This adapter cannot handle individuals inheriting from multiple classes,
   it will also ignore individuals without an `owl:class`.

