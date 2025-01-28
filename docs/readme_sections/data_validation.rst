Data Validation
---------------

Apart from mapping and fusion features, OntoWeaver also offers a data
validation feature to help you ensure your input databases and the
outputs of your mapping fulfill a set of predefined expectations. The
data validation feature uses the functionalities provided by the
`Pandera
package <(https://pandera.readthedocs.io/en/stable/index.html)>`__, as
well as its yaml configuration to validate the data. These yaml
configurations enable you to write some basic definitions of types and
domains expected for each of the columns of your input data, as well as
type and domain expectations for the output of your mapping, with some
preset rules for outputs, ensuring that the output of any mapping will
not result in an empty value and will be a string.

Here’s an example of what a yaml configuration file for a simple
database would look like:

::

   variant_id  patient
       0           A
       1           B
       2           C

Let’s first define a simple mapping configuration for the above data. In
the example below we are mapping the column ``patient`` to a ``patient``
node and the index of the row to a ``variant`` node. The two nodes are
connected via the ``patient_has_variant`` edge.

.. code:: yaml

   row:
      rowIndex:
         to_subject: variant
   transformers:
       - map:
           columns:
               - patient
           to_object: patient
           via_relation: patient_has_variant

Input Data Validation
~~~~~~~~~~~~~~~~~~~~~

Now, let’s define a yaml configuration file for input data validation.
The configuration is part of the ``yaml`` file used to configure the
mapping. We start off by defining a ``validate`` section in the yaml
file, followed by a section defining the ``columns``. For each column in
our database, we define a ``type`` (``dtype: int64`` for the
``variant_id`` column and ``dtype: str`` for the ``patient`` column),
and a set of ``checks`` that we want to perform on the data in the
column. In this case, we want to ensure that the ``variant_id`` column
is in range from 0 to 3, and that the ``patient`` column only contains
the values ``A``, ``B``, and ``C``.

.. code:: yaml

   row:
      rowIndex:
         to_subject: variant
   transformers:
       - map:
           columns:
               - patient
           to_object: patient
           via_relation: patient_has_variant
   validate:
     columns:
       variant_id:
         dtype: int64
         checks:
           in_range:
             min_value: 0
             max_value: 3
             include_min: true
             include_max: true
       patient:
         dtype: str
         checks:
           isin:
             value:
               - A
               - B
               - C

Now we can validate our input data using the command below, which will
return an error if the data does not meet the expectations.

.. code:: sh

   ontoweave my_data.csv:my_mapping.yaml --validate-only

If you want to know more about the rules you can use to validate your
data, you can check the `Pandera
documentation <https://pandera.readthedocs.io/en/stable/index.html>`__.

Output Data Validation
~~~~~~~~~~~~~~~~~~~~~~

The output data validation is similar to the input data validation, but
it is used to validate the output of the mapping. Similarly to the
previous example, we define a domain and type, this time of each of the
transformers we use on the input data.

In the mapping below we’ve defined the expected domains for the output
of the mapping. Unlike in the case of input data validation, the output
validation is already configured to expect a non-empty string output, so
we don’t need to define that explicitly. Hence, we begin the output
validation section with the ``validate_output`` keyword, and the only
section to be defined is ``checks``. In this case, we expect the output
of the ``map`` transformer to be one of the values ``A``, ``B``, or
``C``, and the output of the ``rowIndex`` transformer to be one of the
values ``0``, ``1``, ``2``, or ``3``.

.. code:: yaml

   row:
      rowIndex:
         to_subject: variant
         validate_output:
                 checks:
                     isin:
                         value:
                             - '0'
                             - '1'
                             - '2'
                             - '3'
   transformers:
       - map:
           columns:
               - patient
           to_object: patient
           via_relation: patient_has_variant
           validate_output:
                     checks:
                         isin:
                             value:
                                 - A
                                 - B
                                 - C

The whole yaml file, with both data mapping, input data validation, and
output data validation, would look like this:

.. code:: yaml

   row:
      rowIndex:
         to_subject: variant
         validate_output:
                 checks:
                     isin:
                         value:
                             - '0'
                             - '1'
                             - '2'
                             - '3'
   transformers:
       - map:
           columns:
               - patient
           to_object: patient
           via_relation: patient_has_variant
           validate_output:
                     checks:
                         isin:
                             value:
                                 - A
                                 - B
                                 - C
   validate:
     columns:
       variant_id:
         dtype: int64
         checks:
           in_range:
             min_value: 0
             max_value: 3
             include_min: true
             include_max: true
       patient:
         dtype: str
         checks:
           isin:
             value:
               - A
               - B
               - C

You can find a test based on this example in the
``tests/validate_input`` directory of the OntoWeaver repository. The
test there is configured to fail, due to the presence of a forbidden
``E`` character in the input data.

If you want to know more about the rules you can use to validate your
data, you can check the `Pandera
documentation <https://pandera.readthedocs.io/en/stable/index.html>`__.
