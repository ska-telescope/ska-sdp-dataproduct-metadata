"""Generating Metadata File."""
# pylint: disable=too-many-arguments
# pylint: disable=too-many-instance-attributes

import logging

import ska_ser_logging
import yaml

# Initialise logging
ska_ser_logging.configure_logging()
LOG = logging.getLogger("ska_sdp_scripting")
LOG.setLevel(logging.DEBUG)

METADATA_TEMPLATE = "resources/metadata_defaults.yaml"


class MetaData:
    """."""

    def __init__(
        self,
        input_file=None,
        interface=None,
        eb_id=None,
        pb_id=None,
        processing_script=None,
        observer=None,
        intent=None,
        notes=None,
        cmdline=None,
        commit=None,
        image=None,
        version=None,
        path_list=None,
        output_path=None,
    ):
        """

        @param interface:
        @param execution_block:
        @param processing_block:
        @param processing_script:
        @param observer:
        @param intent:
        @param notes:
        @param cmdline:
        @param commit:
        @param image:
        @param version:
        @param path_list:
        """
        # Read the metadata default template
        if input_file is None:
            self._data = self.read(METADATA_TEMPLATE)
        else:
            self._data = self.read(input_file)

        self._interface = interface
        self._eb_id = eb_id
        self._pb_id = pb_id
        self._processing_script = processing_script
        self._observer = observer
        self._intent = intent
        self._notes = notes
        self._cmdline = cmdline
        self._commit = commit
        self._image = image
        self._version = version
        self._path_list = path_list
        self._output_path = output_path

    def create(self):
        """Create metadata file."""

        # Update interface and eb values
        # Interface needs to be added, this is just a placeholder
        if self._interface:
            LOG.debug("Interface -  %s", self._interface)
            self._data["interface"] = self._interface

        if self._eb_id is None:
            raise ValueError("Execution Block ID is None!")

        self._data["execution_block"] = self._eb_id

        # Identifies the observation
        self.set_context()
        self.set_config()
        self.set_files()
        self.write(data=self._data)

        return self._data

    def update_status(self, filename, path, status):
        """Update the current file status."""

        data = self.read(filename)

        for file in data["files"]:
            if file["path"] == path:
                file["status"] = status

        self.write(filename=filename, data=data)

    def read(self, file):
        """."""
        with open(file, "r", encoding="utf8") as input_file:
            data = yaml.safe_load(input_file)
        print(data)
        return data

    def write(self, filename=None, data=None):
        """Write the metadata to a yaml file.
        @param output_path: output path for the metadata file
        @param data: metadata that needs to be written to file

        """

        if filename is None:
            output_path = self._output_path
        else:
            output_path = filename

        # Write YAML file
        with open(output_path, "w", encoding="utf8") as out_file:
            yaml.safe_dump(data, out_file, default_flow_style=False)

    def set_context(self):
        """Set context for free-form data provided by OET.
        Note. This is currently left empty until we know where to get
        the data from

        @param observer:
        @param intent:
        @param notes:
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

    def set_files(self):
        """Set path to files and add current file status.

        @param path_lists: List of path and description
        """

        files_list = []
        if self._path_list:
            print(self._path_list)
            for path_list in self._path_list:
                path_list["status"] = "working"
                files_list.append(path_list)
            self._data["files"] = files_list
        else:
            LOG.debug("Path list is empty!")
