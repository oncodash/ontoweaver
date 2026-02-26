
I'm having trouble using `nested` transformers with Parquet files
-----------------------------------------------------------------

It seems that the backend used by Pandas to load Parquets files changes the way
a nested data structure is represented.

Double-check how the nested data structure is loaded in the DataFrame, and
configure the transformer accordingly.

For instance, we noticed that *fastparquet* loads a nested dictionary, while
*pyarrow* loads a single dictionary with keys aggregated by a dot.

Thus, if this does not work:

.. code-block:: yaml

    nested:
        keys:
            - level_1
            - level_2

then maybe try:

.. code-block:: yaml

    nested:
        keys: level_1.level_2

