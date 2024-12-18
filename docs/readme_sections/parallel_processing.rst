Parallel Processing
-------------------

OntoWeaver provides a way to parallelize the extraction of nodes and
edges from the provided database, with the aim of reducing the runtime
of the extraction process. By default, the parallel processing is
disabled, and the data frame is processed in a sequential manner. To
enable parallel processing, the user can pass the maximum number of
workers to the ``extract_all`` function.

For example, to enable parallel processing with 16 workers, the user can
call the function as follows:

.. code:: python

   adapter = ontoweaver.tabular.extract_all(table, mapping, parallel_mapping = 16)

To enable parallel processing with a good default working on any
machine, you can use the `approach suggested by the concurrent
module <https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.ThreadPoolExecutor>`__.

.. code:: python

   import os
   adapter = ontoweaver.tabular.extract_all(table, mapping, parallel_mapping = min(32, (os.process_cpu_count() or 1) + 4))
