"""Test Generating Metadata File."""

import json
import logging
import os
import shutil

import pytest
import ska_sdp_config
import yaml

from ska_sdp_dataproduct_metadata import MetaData, new_config_client

LOG = logging.getLogger("metadata-test")
LOG.setLevel(logging.DEBUG)

CONFIG_DB_CLIENT = new_config_client()
SUBARRAY_ID = "01"
MOUNT_PATH = "tests/resources"
METADATA_FILENAME = "ska-data-product.yaml"
OUTPUT_METADATA = "tests/resources/expected_metadata.yaml"
OUTPUT_METADATA_WITHOUT_FILES = (
    "tests/resources/expected_metadata_without_files.yaml"
)
OUTPUT_METADATA_WITH_FILES = (
    "tests/resources/expected_metadata_with_files.yaml"
)
UPDATED_METADATA = "tests/resources/expected_updated_metadata.yaml"


def test_metadata_generation():
    """
    Test generating a metadata, adding files and updating status
    """

    # Wipe config db and directories
    clean_up(f"{MOUNT_PATH}/product")

    # Create eb and pb
    create_eb_pb()

    # Get processing block iD
    for txn in CONFIG_DB_CLIENT.txn():
        pb_list = txn.list_processing_blocks()
        pb_id = pb_list[0]

    # Processing Block
    for txn in CONFIG_DB_CLIENT.txn():
        processing_block = txn.get_processing_block(pb_id)
    eb_id = processing_block.eb_id

    # Creating a fake deployment
    deploy_name = "test"
    deploy_id = f"proc-{pb_id}-{deploy_name}"
    chart = {
        "chart": "artefact.skao.int/ska-sdp-script-vis-receive",
        "values": {},
    }
    deploy = ska_sdp_config.Deployment(deploy_id, "helm", chart)

    for txn in CONFIG_DB_CLIENT.txn():
        txn.create_deployment(deploy)

    data_product_path = f"{MOUNT_PATH}/product/{eb_id}/ska-sdp/{pb_id}"
    metadata = MetaData(pb_id, mount_path=MOUNT_PATH)
    generated_metadata = read_file(f"{data_product_path}/{METADATA_FILENAME}")
    assert generated_metadata == read_file(OUTPUT_METADATA_WITHOUT_FILES)

    # Check when files are added
    file = metadata.new_file(path="vis.ms", description="raw visibilities")
    metadata_with_files = read_file(f"{data_product_path}/{METADATA_FILENAME}")
    assert metadata_with_files == read_file(OUTPUT_METADATA_WITH_FILES)

    # Check with status has been updated
    file.update_status("done")
    updated_status_files_metadata = read_file(
        f"{data_product_path}/{METADATA_FILENAME}"
    )
    assert updated_status_files_metadata == read_file(UPDATED_METADATA)


def test_no_pb():
    """
    Check that ValueError is raised when there is no processing block"
    """

    # Wipe config db and directories
    clean_up(f"{MOUNT_PATH}/product")

    pb_id = "pb-tes-20200425-00000"

    with pytest.raises(ValueError, match=r"Processing Block is None!"):
        MetaData(pb_id, mount_path=MOUNT_PATH)


def test_no_script():
    """
    Check that ValueError is raised when there is no script"
    """

    # Wipe config db and directories
    clean_up(f"{MOUNT_PATH}/product")

    # Create eb and pb
    create_eb_pb()

    # Get processing block iD
    for txn in CONFIG_DB_CLIENT.txn():
        # Deleting script to test
        txn.delete_script("realtime", "vis-receive", "0.6.0")
        pb_list = txn.list_processing_blocks()
        pb_id = pb_list[0]

    with pytest.raises(ValueError, match=r"Script is None!"):
        MetaData(pb_id, mount_path=MOUNT_PATH)


def test_with_duplicate_file_path():
    """
    Check if the file with same path has already been added to the list."
    """

    # Wipe config db and directories
    clean_up(f"{MOUNT_PATH}/product")

    # Create eb and pb
    create_eb_pb()

    # Get processing block iD
    for txn in CONFIG_DB_CLIENT.txn():
        pb_list = txn.list_processing_blocks()
        pb_id = pb_list[0]

    # Processing Block
    for txn in CONFIG_DB_CLIENT.txn():
        processing_block = txn.get_processing_block(pb_id)
    eb_id = processing_block.eb_id

    data_product_path = f"{MOUNT_PATH}/product/{eb_id}/ska-sdp/{pb_id}"
    metadata = MetaData(pb_id, mount_path=MOUNT_PATH)

    generated_metadata = read_file(f"{data_product_path}/{METADATA_FILENAME}")
    expected_metadata = read_file(OUTPUT_METADATA_WITHOUT_FILES)
    assert generated_metadata == expected_metadata

    # Check when files are added
    path = "vis.ms"
    metadata.new_file(path=path, description="raw visibilities")

    with pytest.raises(
        ValueError, match=r"File with same path already exists!"
    ):
        metadata.new_file(path=path, description="raw visibilities")


# -----------------------------------------------------------------------------
# Ancillary functions
# -----------------------------------------------------------------------------


def read_file(file):
    """Read and load files into yaml"""
    with open(file, "r", encoding="utf8") as input_file:
        data = yaml.safe_load(input_file)
    return data


def clean_up(path):
    """Remove all entries in the config DB and delete directories"""
    CONFIG_DB_CLIENT.backend.delete("/pb", must_exist=False, recursive=True)
    CONFIG_DB_CLIENT.backend.delete("/eb", must_exist=False, recursive=True)
    CONFIG_DB_CLIENT.backend.delete(
        "/script", must_exist=False, recursive=True
    )

    if os.path.exists(path):
        shutil.rmtree(path)
    else:
        LOG.info("The path does not exist")


def create_eb_pb():
    """Create execution block and processing block."""
    execution_block, processing_blocks = get_eb_pbs()
    for txn in CONFIG_DB_CLIENT.txn():
        eb_id = execution_block.get("eb_id")
        if eb_id is not None:
            txn.create_execution_block(eb_id, execution_block)
        for processing_block in processing_blocks:
            txn.create_processing_block(processing_block)

            # Create script
            pb_script = processing_block.script
            script_image = "artefact.skao.int/ska-sdp-script-"
            script = {
                "image": f"{script_image}{pb_script['name']}:"
                f"{pb_script['version']}"
            }
            txn.create_script(
                pb_script["kind"],
                pb_script["name"],
                pb_script["version"],
                script,
            )


def read_configuration_string():
    """Read configuration string from JSON file."""
    return read_json_data("configuration_string.json", decode=True)


def get_eb_pbs():
    """Get EB and PBs from configuration string."""
    config = read_configuration_string()

    pbs_from_config = config.pop("processing_blocks")
    eb_id = config.get("eb_id")

    eb_config = config.copy()
    eb_extra = {
        "subarray_id": SUBARRAY_ID,
        "pb_realtime": [],
        "pb_batch": [],
        "pb_receive_addresses": None,
        "current_scan_type": None,
        "scan_id": None,
        "status": "ACTIVE",
    }
    execution_block = {**eb_extra, **eb_config}

    pbs_config_list = []
    for pb_from_config in pbs_from_config:
        pb_id = pb_from_config.get("pb_id")
        kind = pb_from_config.get("script").get("kind")
        execution_block["pb_" + kind].append(pb_id)
        if "dependencies" in pb_from_config:
            dependencies = pb_from_config.get("dependencies")
        else:
            dependencies = []
        processing_block = ska_sdp_config.ProcessingBlock(
            pb_id,
            eb_id,
            pb_from_config.get("script"),
            parameters=pb_from_config.get("parameters"),
            dependencies=dependencies,
        )
        pbs_config_list.append(processing_block)

    return execution_block, pbs_config_list


def read_json_data(filename, decode=False):
    """Read JSON file from data directory.

    :param decode: decode the JSON dat into Python

    """
    path = os.path.join(os.path.dirname(__file__), "resources", filename)
    with open(path, "r", encoding="utf8") as file:
        data = file.read()
    if decode:
        data = json.loads(data)
    return data
