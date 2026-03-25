
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


How is the `from_subject` clause handled?
-----------------------------------------

There is 3 ways in which a `from_subject` clause finds the node(s) to which add
a link:

1. The subject type is the same as the one declared in the subject/row section.
   This is the default, and you don't need to explicitely add a `from_subject`
   clause in transformers to handle this case. It is implicit.
2. The subject type is the same than one declared in the `transformers` section
   with a `to_object` clause. It will always link to this one, for every row.
3. The subject type is referenced in a match clause.
   In this case, it will only link to this type if the current row matches to
   this type.
4. One (or several) node(s) of the subject type have been created by a user-made
   transformer **that has been called before**. In this case, all those created
   nodes will be linked.

.. warning::

    In the 4th case, it is **mandatory** that the transformer creating the nodes
    to which you want to link is declared **before** the transformer that has
    the `from_subject` clause.

.. warning::

    In the 3d and 4th cases, if the subject type does not match, the creation
    of the link is silently ignored.


Example showing cases 2, 3 and 4:

.. code:: yaml

    row:
        map:
            id_from_column: source
            match_type_from_column: entity_type
            match:
              - protein:
                    to_subject: protein
              - complex:
                    to_subject: complex

    transformers:
        - map:
            column: role
            to_object: role
            via_relation: has_role
        - map:
            column: effect
            from_subject: role  # From the transformer just above.
            to_object: effect
            via_relation: has_effect
        - path_directed  # Outputs a `target_protein`. MUST BE BEFORE THE NEXT ONE.
        - map:
            column: target_genesymbol
            from_subject: target_protein  # Links toward path_directed's target_protein.
            to_object: target_gene
            via_relation: transcript_to_gene_relationship
        - map:
            column: complex_involved_in
            from_subject: complex  # Only create nodes if the current row outputs this subject.
            to_object: complex_involved_in
            via_relation: has_involvement

