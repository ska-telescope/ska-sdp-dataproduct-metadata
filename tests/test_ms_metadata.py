"""Test Generating Metadata File for MeasurementSets."""
import os

from casacore import tables
from pytest_bdd.steps import given

# pylint: disable=missing-function-docstring


# arbitrarily chosen ms file for testing purposes:
INPUT_FILE = "data/AA05LOW.ms"
maintable = tables.table(INPUT_FILE, readonly=True, ack=False)


@given("An example input file of the correct dimension")
def test_file():
    if not os.path.isdir(INPUT_FILE):
        raise FileExistsError


maintabdict = {
    "t_resolution": maintable.getcell("INTERVAL", 0),
}

assert maintabdict.get("t_resolution") == 0.9
