Introduction
============

The SDP Data Product Metadata is a python package that generates Measurement Set (MS) metadata. This package
helps to ensure the data products are written with the appropriate metadata.


Contents of Metadata file
-------------------------

Below shows the contents of the metadata and brief description about them:

- ``interface``:  Giving the schema. Currently there is no schema for this (just a placeholder). It will be added to the `Telescope Model <https://gitlab.com/ska-telescope/ska-telmodel>'_.
- ``execution_block``: Identifies the observation
- ``context``:  This contains free-form data provided by OET. The data is meant to be passed verbatim through from OET/TMC as part of AssignResources (SDP) or Configure (other sub-systems). Currently this is just a placeholder.
- ``config``: This is the configuration used for executing the processing script
- ``files``: This contains a list of MS files which have been generated.

    - ``path``: Path where the MS is located
    - ``description``: Useful details about the file
    - ``status``: Indicate current file status

        - ``working``: Processes still running, files might be missing or incomplete
        - ``done``: Processes finished, files should be complete
        - ``failure``: Not finished successfully, files might be incomplete or corrupt

More details can be found in `ADR-55 <https://confluence.skatelescope.org/display/SWSI/ADR-55+Definition+of+metadata+for+data+management+at+AA0.5>`_
