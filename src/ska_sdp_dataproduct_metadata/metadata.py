"""Generating Metadata File."""

import logging
import os

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


class MetaData:
    """
    Class for generating the metadata file
    """

    def __init__(self, path=None):

        # determine template filename
        metadata_template_path = os.path.join(
            os.path.dirname(__file__), "template", METADATA_TEMPLATE
        )

        # if no path specified, use metadata template
        path = path or metadata_template_path

        # read data from yaml
        self._data = benedict(path, format="yaml")

        self._config = None
        self._pb_id = None
        self._pb = None
        self._eb_id = None
        self._root = "/"
        self._prefix = ""

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
            self._pb = txn.get_processing_block(self._pb_id)

            if self._pb is None:
                raise ValueError("Processing Block is None!")

            self._eb_id = self._pb.eb_id
            LOG.info("Execution Block ID %s", self._eb_id)

            if self._eb_id:
                execution_block = txn.get_execution_block(self._eb_id)
                self._data.execution_block = self._eb_id

            # Get script from processing block
            script = txn.get_script(
                self._pb.script["kind"],
                self._pb.script["name"],
                self._pb.script["version"],
            )
            if script is None:
                raise ValueError("Script is None!")

        # Update context
        if self._eb_id:
            self._data.context = execution_block["context"]

        # Update config
        self.set_config(script)

        # Construct the path to write metadata
        self._root = mount_path or "/"
        self._prefix = f"/product/{self._eb_id}/ska-sdp/{self._pb_id}"

    def runtime_abspath(self, path):
        """
        The absolute path of `path` relative to the standard prefix. This value
        is valid at runtime; i.e., it maps to the filesystem in use.

        :param path: A path relative to the standard prefix.
        """
        return os.path.normpath(f"{self._root}/{self._prefix}/{path}")

    def set_id(self, metadata_id):
        """
        Set the id for this metadata file
        """
        self._eb_id = metadata_id
        self._data.execution_block = metadata_id

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
        config_data.processing_script = pb_script["name"]
        config_data.image = script["image"].split(":", 1)[0]
        config_data.version = pb_script["version"]

    def new_file(self, path=None, description=None, crc=None):
        """
        Creates a new file into the metadata and add current file status.

        :param path: file name of the data product
        :param description: Description of the file
        :param crc: Checksum of the file. NB: CRC is supplied, not calculated
        :returns: instance of the File class

        """

        path = os.path.normpath(path)
        for file in self._data.files:
            if path in file.path:
                raise ValueError("File with same path already exists!")

        add_to_file = [
            {
                "crc": crc,
                "description": description,
                "path": path,
                "status": "working",
            }
        ]
        self._data.files.extend(add_to_file)
        self.write()

        # Instance of the class to represent the file
        file = File(self, path)
        return file

    def read(self, file):
        """
        Read input metadata file and load in yaml

        :param file: input metadata file
        :returns: Returns the yaml loaded metadata file

        """
        self._data = benedict(file, format="yaml")
        return self._data

    def write(self, path=None):
        """Write the metadata to a yaml file."""

        # determine path
        metadata_file_path = path or self.runtime_abspath(METADATA_FILENAME)

        # Check if directories exist, if not create
        parent_dir = os.path.dirname(metadata_file_path)
        if not os.path.exists(parent_dir):
            os.makedirs(parent_dir)

        # Write YAML file
        with open(metadata_file_path, "w", encoding="utf8") as out_file:
            out_file.write(self._data.to_yaml())


class File:
    """Class to represent the file in the metadata."""

    def __init__(self, metadata, path):
        self._path = path
        self._metadata = metadata
        self._metadata_file_path = metadata.runtime_abspath(METADATA_FILENAME)

    @property
    def full_path(self):
        """Get the full path object."""
        return self._metadata.runtime_abspath(self._path)

    @property
    def metadata_file_path(self):
        """Get the metadata file path object."""
        return self._metadata_file_path

    def update_status(self, status):
        """
        Update the current file status.

        :param: status: status to be updated to

        """

        # read metadata yaml
        metadata = MetaData(self._metadata_file_path)
        data = metadata.get_data()

        # Update File
        for file in data.files:
            if self._path in file.path:
                file.status = status

        # Write YAML file
        metadata.write(self._metadata_file_path)
