# SKA SDP Data Product Metadata

## Introduction

SDP Data Product Metadata is a Python package to record SKA-specific metadata alongside
the data products. It creates metadata files containing:
- Execution block ID
- The context of the execution block provided by the Observation Execution Tool (OET)
- The configuration of the processing block used to generate the data products
- A list of data product files with description, status, size and a cyclic redundancy check (CRC) for error detection
- Associated IVOA ObsCore attributes used for querying astronomical observations

## Typical Usage

To create a minimal MetaData file:

```python
from ska_sdp_dataproduct_metadata import MetaData
m = MetaData()
m.set_execution_block_id("test-block-id")

# write to disk (automatically validates the metadata)
try:
    m.write("/some/path/here/ska-data-product.yaml")
except jsonschema.exceptions.ValidationError as ve:
    print(ve)
```

Or to create a metadata object with typical obscore attributes:

```python
from ska_sdp_dataproduct_metadata import MetaData, ObsCore
m = MetaData()
m.set_execution_block_id("test-block-id")

# add obscore attributes
data = m.get_data()
data.obscore.dataproduct_type = ObsCore.DataProductType.MS
data.obscore.access_format = ObsCore.AccessFormat.TAR_GZ
data.obscore.calib_level = ObsCore.CalibrationLevel.LEVEL_4
data.obscore.obs_collection = ObsCore.ObservationCollection.SIMULATION
data.obscore.facility_name = ObsCore.SKA
data.obscore.instrument_name = ObsCore.SKA_LOW

# manually validate against the schema
validation_errors = m.validate()
```

## Standard CI machinery

The repository is set up to use [CI templates](https://gitlab.com/ska-telescope/templates-repository)
and [makefiles](https://gitlab.com/ska-telescope/sdi/ska-cicd-makefile) maintained by the System Team.

For any questions, please look at the repositories' documentation or ask for support on Slack
in the #team-system-support channel.

To keep the makefile modules up to date locally, follow the instructions at:
https://gitlab.com/ska-telescope/sdi/ska-cicd-makefile#keeping-up-to-date

## Creating a new release

When new release is ready:

  - checkout the main branch
  - Update the version number in .release, pyproject.toml, and docs/src/conf.py with
    - `make bump-patch-release`
    - `make bump-minor-release`, or
    - `make bump-major-release`
  - Manually replace main with the new version number in CHANGELOG.md
  - create the git tag with `make create-git-tag` using your working ticket number
  - push the changes using `make push-git-tag`