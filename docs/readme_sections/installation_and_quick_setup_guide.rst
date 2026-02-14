Installation and quick setup guide
----------------------------------

Python Module
~~~~~~~~~~~~~

The project is written in Python and has been tested with the
`UV <https://docs.astral.sh/uv/>`__ environment manager.
You can install the necessary dependencies in a virtual environment like this:

::

   git clone https://github.com/oncodash/ontoweaver.git
   cd ontoweaver
   uv build

UV will create a virtual environment according to your configuration
(either centrally or in the project folder).
You can then run any script or command using ``uv run``.
For isntance, to run the ontoweave command: ``uv run ontoweave``.


Output Database
~~~~~~~~~~~~~~~

OntoWeaver can export the created knowledge graph in any format
supported by BioCypher (Neo4j, ArangoDB, CSV, RDF, PostgreSQL, SQLite,
NetworkX, … see `BioCypher’s
documentation <https://biocypher.org/output/index.html>`__).


Graph visualization with Neo4j
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Neo4j is a popular graph database management system that offers a
flexible and efficient way to store, query, and manipulate complex,
interconnected data. Cypher is the query language used to interact with
Neo4j databases. In order to visualize graphs extracted from databases
using OntoWeaver and BioCypher, you can download the `Neo4j Graph
Database Self-Managed <https://neo4j.com/deployment-center/>`__ for your
operating system. It has been extensively tested with the Community
edition.

To create a global variable to Neo4j, add the path to ``neo4j-admin`` to
your ``PATH`` and ``PYTHONPATH``. In order to use the Neo4j browser, you
will need to install the correct Java version, depending on the Neo4j
version you are using, and add the path to ``JAVA_HOME``. OntoWeaver and
BioCypher support versions 4 and 5 of Neo4j.

To run Neo4j (version 5+), use the command ``neo4j-admin server start``
after importing your results via the neo4j import sequence provided in
the ``./biocypher-out/`` directory. Use ``neo4j-admin server stop`` to
disconnect the local server.

By default, Neo4j Community Edition (CE) and Neo4j Enterprise Edition
(EE) report a small amount of usage data. If necessary, reporting can be
turned off with the configuration setting ``dbms.usage_report.enabled=false``.


Tests
~~~~~

Tests are located in the ``tests/`` subdirectory and may be a good
starting point to see OntoWeaver in practice. You may start with
``tests/test_simplest.py`` which shows the simplest example of mapping
tabular data through BioCypher.

To run tests, use ``pytest``:

::

   uv run pytest

