"""Generating Metadata File."""

import json
import logging
import os

import jsonschema
import ska_sdp_config
import ska_ser_logging
from benedict import benedict

from .config import new_config_client

# Initialise logging
ska_ser_logging.configure_logging()
LOG = logging.getLogger("ska_sdp_dataproduct_metadata")
LOG.setLevel(logging.INFO)

METADATA_TEMPLATE = "metadata_defaults.yaml"
METADATA_FILENAME = os.environ.get(
    "METADATA_FILENAME", "ska-data-product.yaml"
)
METADATA_SCHEMA = "metadata.json"


# pylint:disable=too-many-instance-attributes
class MetaData:
    """
    Class for generating the metadata file

    :param path: location of the metadata file to read
    """

    # create a single validator for all instances of the MetaData class
    with open(
        os.path.join(os.path.dirname(__file__), "schema", METADATA_SCHEMA),
        "r",
        encoding="utf-8",
    ) as metadata_schema:
        validator = jsonschema.validators.Draft202012Validator(
            json.load(metadata_schema)
        )

    class ValidationError(Exception):
        """
        An exception indicating an error during validation of metadata
        against the schema.
        """

        def __init__(self, message, errors):
            super().__init__(message)
            self.errors = errors

    def __init__(self, path=None):
        # determine default template filename
        metadata_template_path = os.path.join(
            os.path.dirname(__file__), "template", METADATA_TEMPLATE
        )

        # if no path specified (called first time),
        # use metadata template to create one
        # this is not necessarily the output path
        path = path or metadata_template_path

        # read data from yaml
        self._data = self.read(path)
        self._config = None
        self._pb_id = None
        self._pb = None
        self._eb_id = None
        self._root = "/"
        self._prefix = ""
        # Output path of metadata file
        # Set to None if not provided
        self._output_path = None

    @property
    def output_path(self):
        """
        Output metadata path
        """
        return self._output_path

    @output_path.setter
    def output_path(self, custom_path):
        """
        Set custom path for output metadata
        """
        self._output_path = custom_path

    def runtime_abspath(self, path):
        """
        The absolute path of `path` relative to the standard prefix. This value
        is valid at runtime; i.e., it maps to the filesystem in use.

        :param path: A path relative to the standard prefix.
        """
        return os.path.normpath(f"{self._root}/{self._prefix}/{path}")

    def load_processing_block(self, pb_id=None, mount_path=None):
        """
        Configure a MetaData object based on the data in a processing block

        :param pb_id: processing block ID
        :type mount_path: path where the data product volume is mounted.
        """

        # Get connection to config DB
        LOG.info("Opening connection to config DB")
        self._config = new_config_client()

        # Processing block ID
        if pb_id is None:
            self._pb_id = os.getenv("SDP_PB_ID")
        else:
            self._pb_id = pb_id
        LOG.info("Processing Block ID %s", self._pb_id)

        # Get processing Block and eb_id from config DB
        self._pb = None
        self._eb_id = None
        for txn in self._config.txn():
            self._pb = txn.processing_block.get(self._pb_id)

            if self._pb is None:
                raise ValueError("Processing Block is None!")

            self._eb_id = self._pb.eb_id
            LOG.info("Execution Block ID %s", self._eb_id)

            if self._eb_id:
                execution_block = txn.execution_block.get(self._eb_id)
                self._data.execution_block = self._eb_id

            # Get script from processing block
            script_key = ska_sdp_config.entity.Script.Key(
                kind=self._pb.script.kind,
                name=self._pb.script.name,
                version=self._pb.script.version,
            )
            script = txn.script.get(script_key)
            if script is None:
                raise ValueError("Script is None!")

        # Update context
        if self._eb_id:
            self._data.context = execution_block.context

        # Update config
        self.set_config(script)

        # Construct the path to write metadata
        self._root = mount_path or "/"
        self._prefix = f"/product/{self._eb_id}/ska-sdp/{self._pb_id}"

    def set_execution_block_id(self, execution_block_id):
        """
        Set the execution_block_id for this MetaData object
        NB: If this MetaData object describes a dataproduct that was not
        generated from an execution_block, then it is possible to use any
        SKA Unique Identifier (https://gitlab.com/ska-telescope/ska-ser-skuid)

        :param execution_block_id: an execution_block_id
        """
        self._eb_id = execution_block_id
        self._data.execution_block = execution_block_id

    def get_data(self):
        """
        Return the data dictionary within the MetaData object
        """
        return self._data

    def set_config(self, script):
        """
        Set configuration of generating software.

        :param script: Processing script details

        """
        # Get script from processing block
        pb_script = self._pb.script

        config_data = self._data.config
        config_data.processing_block = self._pb_id
        config_data.processing_script = pb_script.name
        config_data.image = script.image.split(":", 1)[0]
        config_data.version = pb_script.version

    def new_file(self, dp_path=None, description=None, crc=None):
        """
        Creates a new file into the metadata and add current file status.

        :param dp_path: path of the data product
                Not to be confused with path of the metadata file
        :param description: Description of the file
        :param crc: CRC (Cyclic Redundancy Check) checksum for the file.
            NB: CRC is supplied, not calculated

        :returns: instance of the File class
        """

        dp_path = os.path.normpath(dp_path)
        for file in self._data.files:
            if dp_path in file.path:
                raise ValueError("File with same path already exists!")

        add_to_file = [
            {
                "crc": crc,
                "description": description,
                "path": dp_path,
                "status": "working",
            }
        ]
        self._data.files.extend(add_to_file)
        # Write to output metadata
        self.write()

        # Instance of the class to represent the file
        file = File(self, dp_path)
        return file

    def read(self, file):
        """
        Read input metadata file and load in yaml.

        :param file: input metadata file
        :returns: Returns the yaml loaded metadata file

        """
        return benedict(file, format="yaml")

    def write(self):
        """
        Write the metadata to a yaml file.
        """

        # validate the data before writing
        validation_errors = self.validate()
        if validation_errors:
            raise MetaData.ValidationError(
                "Error(s) occurred during validation.", validation_errors
            )
        # Allow writing to a custom path
        output_path = self.output_path or self.runtime_abspath(
            METADATA_FILENAME
        )

        # Check if directories exist, if not create
        parent_dir = os.path.dirname(output_path)
        if not os.path.exists(parent_dir):
            os.makedirs(parent_dir)

        # Write YAML file
        with open(output_path, "w", encoding="utf8") as out_file:
            out_file.write(self._data.to_yaml())

    def validate(self) -> list:
        """
        Validate the current contents of the metadata against the schema.

        :returns: A list of errors.
        """

        errors = []

        # validate the metadata against the schema
        validator_errors = MetaData.validator.iter_errors(self._data)

        # Loop over the errors
        for validator_error in validator_errors:
            errors.append(validator_error)

        return errors


class File:
    """Class to represent the file in the metadata."""

    def __init__(self, metadata, path):
        self._path = path
        self._metadata = metadata

    @property
    def full_path(self):
        """Get the full path object."""
        return self._metadata.runtime_abspath(self._path)

    def update_status(self, status):
        """
        Update the current file status.

        :param: status: status to be updated to
        """
        # read metadata yaml
        data = self._metadata.get_data()

        # Update File
        for file in data.files:
            if self._path in file.path:
                file.status = status

        # Write YAML file
        self._metadata.write()
