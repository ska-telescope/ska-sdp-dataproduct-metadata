SDP Data Product Metadata
=========================

SDP Data Product Metadata is a Python package to record SKA-specific metadata alongside
the data products. It creates metadata files containing:

    - Execution block ID
    - The context of the execution block provided by the Observation Execution Tool (OET)
    - The configuration of the processing block used to generate the data products
    - A list of data product files with description, status, size and a cyclic redundancy check (CRC) for error detection
    - Associated IVOA ObsCore attributes used for querying astronomical observations

.. toctree::
  :maxdepth: 1

  contents-of-metadata
  api


Indices and tables
------------------

- :ref:`genindex`
