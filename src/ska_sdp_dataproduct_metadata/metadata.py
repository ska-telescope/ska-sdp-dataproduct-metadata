"""Generating Metadata File."""
# pylint: disable=too-many-arguments
# pylint: disable=too-many-instance-attributes

import logging
import os

import ska_ser_logging
import yaml

from .config import new_config_client

# Initialise logging
ska_ser_logging.configure_logging()
LOG = logging.getLogger("ska_sdp_dataproduct_metadata")
LOG.setLevel(logging.INFO)

METADATA_TEMPLATE = "resources/metadata_defaults.yaml"


class MetaData:
    """
    Class for generating the metadata file

    """

    def __init__(self, pb_id=None):

        # Get connection to config DB
        LOG.info("Opening connection to config DB")
        self._config = new_config_client()

        # Processing block ID
        if pb_id is None:
            self._pb_id = os.getenv("SDP_PB_ID")
        else:
            self._pb_id = pb_id
        LOG.debug("Processing Block ID %s", self._pb_id)

        # Read the input metadata template
        if input_file is None:
            # Using the default template
            self._data = self.read(METADATA_TEMPLATE)
        else:
            self._data = self.read(input_file)

        # self._interface = interface
        # self._eb_id = eb_id
        # self._pb_id = pb_id
        # self._processing_script = processing_script
        # self._observer = observer
        # self._intent = intent
        # self._notes = notes
        # self._cmdline = cmdline
        # self._commit = commit
        # self._image = image
        # self._version = version
        # self._output_path = output_path

        # Update interface and eb values
        # Interface needs to be added from ska_telmodel
        if self._interface:
            LOG.debug("Interface -  %s", self._interface)
            self._data["interface"] = self._interface

        if self._eb_id is None:
            raise ValueError("Execution Block ID is None!")

        self._data["execution_block"] = self._eb_id

        # Updated all the relevant section of the metadata
        self.set_context()
        self.set_config()
        self.write()

    def update_file_status(self, ms_name, status):
        """
        Update the current file status.

        :param: ms_name: Measurement set file name
        :param: status: status to be updated to

        """

        for file in self._data["files"]:
            if ms_name in file["path"]:
                file["status"] = status

        self.write()

    def set_context(self):
        """
        Set context for free-form data provided by OET.
        Note. This is currently left empty until we know where to get
        the data from

        :param observer: observer name
        :param intent: intent of the use
        :param notes: additional notes

        """
        context_data = self._data["context"]
        context_data["observer"] = self._observer
        context_data["intent"] = self._intent
        context_data["notes"] = self._notes

    def set_config(self):
        """Set configuration of generating software."""

        config_data = self._data["config"]

        if self._pb_id is None:
            raise ValueError("Processing Block ID is None!")
        config_data["processing_block"] = self._pb_id

        if self._processing_script is None:
            raise ValueError("Processing Script is None!")
        config_data["processing_script"] = self._processing_script

        config_data["image"] = self._image
        config_data["version"] = self._version
        config_data["cmdline"] = self._cmdline
        config_data["commit"] = self._commit

    def add_path_to_files(self, path_lists=None):
        """
        Set path to files and add current file status.

        :param path_lists: List of path and description

        """

        files_list = []
        if path_lists:
            for path_list in path_lists:
                ms_name = path_list["path"]
                file_path = (
                    f"/product/{self._eb_id}/ska-sdp/{self._pb_id}/{ms_name}"
                )
                path_list["path"] = file_path
                path_list["status"] = "working"
                files_list.append(path_list)
            self._data["files"] = files_list
        else:
            raise ValueError("Path list is empty!")

        self.write()

    def read(self, file):
        """
        Read input metatada file and load in yaml

        :param file: input metadata file
        :returns: Returns the yaml loaded metadata file

        """
        with open(file, "r", encoding="utf8") as input_file:
            data = yaml.safe_load(input_file)
        return data

    def write(self):
        """Write the metadata to a yaml file."""

        # Write YAML file
        with open(self._output_path, "w", encoding="utf8") as out_file:
            yaml.safe_dump(self._data, out_file, default_flow_style=False)
