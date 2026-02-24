
In some specific cases, you may want to load several data files at once, and
merge them in a single table before mapping the data. For instance, "parquet"
files often come as a set of files.

To do so, you can use the "globbing" syntax that you may know from your command
line shell.

For instance, if you want to select all the files ending with the ``.parquet``
extension in the ``my_dir`` directory:

.. code:: sh

   ontoweave 'my_dir/*.parquet:my_mapping.yaml'

.. warning::

    You have to encompass the globbing file syntax with quotes, or else
    your shell is going to expand it for you in a list of files, which is not
    supported by `ontoweave`. However, OntoWeaver is going to expand the common
    syntax by itself. You can thus safely use the common globbing syntax.

