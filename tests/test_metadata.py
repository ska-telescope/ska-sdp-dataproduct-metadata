"""Metadata Library tests."""

# import json
import logging

import yaml

from ska_sdp_dataproduct_metadata import MetaData

# import os
# from unittest.mock import patch
#
# import yaml


LOG = logging.getLogger("metadata-test")
LOG.setLevel(logging.DEBUG)


# meta = MetaData()
# meta.create(eb="sdfsdfsdfs")
#
# path_list = [{"path": "visbility.ms", "description": "visibilities"},
#              {"path": "another.ms", "desciption": "more visbilities"}]
OUTPUT_PATH = "resources/sdp-data-out.yaml"
PATH_LIST = [
    {"path": "visbility.ms", "description": "visibilities"},
    {"path": "another.ms", "desciption": "more visbilities"},
]
EB_ID = ""
PB_ID = ""
PROCESSING_SCRIPT = ""
INPUT_FILE = "tests/resources/test_metadata_default.yaml"
EXPECTED_METADATA = "tests/resources/expected_metadata.yaml"

# meta.update_status(filename=output_path, path="visbility.ms", status="done")


def test_create():
    """
    Test the creation of the Metadata file using
    default parameters
    """

    LOG.info("Create Metadata file")

    metadata = MetaData(
        input_file=INPUT_FILE,
        eb_id="testing",
        pb_id="pb_testing",
        processing_script="processing/testing",
        path_list=PATH_LIST,
        output_path=OUTPUT_PATH,
    )
    output_data = metadata.create()
    expected_metadata = read_file(EXPECTED_METADATA)
    assert output_data == expected_metadata


def read_file(file):
    """."""
    with open(file, "r", encoding="utf8") as input_file:
        data = yaml.safe_load(input_file)
    return data


# def test_update_status():
#
# def test_fail():
