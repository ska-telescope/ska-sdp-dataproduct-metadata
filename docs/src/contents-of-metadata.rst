Contents of Metadata file
=========================

Below shows the contents of the metadata and brief description about them:

- ``interface``:  Giving the schema. Currently there is no schema for this (just a placeholder). It will be added to the `Telescope Model <https://gitlab.com/ska-telescope/ska-telmodel>`_.
- ``execution_block``: Identifies the observation
- ``context``:  This contains free-form data provided by OET. The data is meant to be passed verbatim through from OET/TMC as part of AssignResources (SDP) or Configure (other sub-systems). Currently this is just a placeholder.
- ``config``: This is the configuration used for executing the processing script
- ``files``: This contains a list of data products (typically MS or HDF files) which have been generated.

    - ``crc``: A cyclic redundancy check (CRC) generated from the contents of the file and used to detect errors in the data
    - ``description``: Useful details about the file
    - ``path``: Path where the data product file is located
    - ``size``: Size of the file (in KB)
    - ``status``: Indicate current file status

        - ``working``: Processes still running, files might be missing or incomplete
        - ``done``: Processes finished, files should be complete
        - ``failure``: Not finished successfully, files might be incomplete or corrupt

- ``obscore``: This contains attributes as specified by the IVOA recommendation for Observation Data Models. It defines core components that are necessary to perform data discovery when querying for astronomical observations. Details of the attributes can be found at `IVOA ObsCore <https://www.ivoa.net/documents/ObsCore/>`_.
 
More details can be found in `ADR-55 <https://confluence.skatelescope.org/display/SWSI/ADR-55+Definition+of+metadata+for+data+management+at+AA0.5>`_

Note - If the metadata filename needs to be updated, you can do that by publishing it on `METADATA_FILENAME` environment variable.
