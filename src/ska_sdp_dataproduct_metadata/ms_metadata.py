"""Generating MeasurementSet Metadata File."""

import argparse
import os
from pprint import pprint

from astropy.time import Time, TimeDelta
from casacore import tables

from ska_sdp_dataproduct_metadata import MetaData

# pylint: disable=missing-function-docstring


def _subtable(tbl: tables.table, name: str, readonly=True):
    try:
        table_err = False
        return (
            tables.table(tbl.getkeyword(name), readonly=readonly, ack=False),
            table_err,
        )
    except RuntimeError as err:
        table_err = True
        if f"Table keyword {name} does not exist" in str(err):
            print(f"Invalid sub-table: '{name}'")
        else:
            raise err
        return None, table_err


def stokes_polarisations(corr_types: list):
    """return polarisations, separated by '/'"""
    stokes_types = {
        5: "RR",
        6: "RL",
        7: "LR",
        8: "LL",
        9: "XX",
        10: "XY",
        11: "YX",
        12: "YY",
    }
    keys = [
        stokes_types[value] for value in corr_types if value in stokes_types
    ]
    return "/".join(keys)


def time_to_mjd(mjd_in_secs):
    return (
        Time(0.0, format="mjd", scale="tai")
        + TimeDelta(mjd_in_secs, format="sec", scale="tai")
    ).mjd


def check_diameter(diameters):
    """Check if all dish diameter values are the same"""
    if len(diameters) == 0:
        return ""
    if all(d == diameters[0] for d in diameters):
        return float(diameters[0])
    return "various"


def get_dir_size(path="."):
    # pylint: disable=W0622
    total = 0
    with os.scandir(path) as iter:
        for entry in iter:
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                total += get_dir_size(entry.path)
    return total / 1024


parser = argparse.ArgumentParser()
parser.add_argument("ms_file", help="path of the ms file to use, <path>.ms")
args = parser.parse_args()

# arbitrarily chosen ms file for testing purposes:
AA05LOW = (
    "/Users/00110564/ska/ska-sdp-realtime-receive-modules/data/AA05LOW.ms"
)

# Extract the file name and extension
full_path = args.ms_file
full_path = full_path.rstrip("/")
file_name_with_extension = os.path.split(full_path)[-1]

maintable = tables.table(args.ms_file, readonly=True, ack=False)

reference_list = [
    "ANTENNA",
    "OBSERVATION",
    "SPECTRAL_WINDOW",
    "POLARIZATION",
    "POINTING",
]

subtables = []
for subtab in maintable.getsubtables():
    file_name = os.path.basename(subtab)
    subtables.append(file_name)
print("Sub-tables:")
for s in subtables:
    print(s, sep="\n")


maintabdict = {
    "t_resolution": maintable.getcell("INTERVAL", 0),
}

anttable, table_error = _subtable(maintable, "ANTENNA")
dish_diameters = []
for row in range(anttable.nrows()):
    d = anttable.getcell("DISH_DIAMETER", row)
    dish_diameters.append(d)
antdict = {
    "instrument_ant_diameter": check_diameter(dish_diameters),
    "ant_number": int(anttable.nrows()),
}

obstable, table_error = _subtable(maintable, "OBSERVATION")
if not table_error:
    obsdict = {
        "facility_name": str(obstable.getcell("OBSERVER", 0)),
        "obs_publisher_did": str(obstable.getcell("PROJECT", 0)),  # duplicate?
        "instrument_name": str(obstable.getcell("TELESCOPE_NAME", 0)),
        "t_min": float(time_to_mjd(obstable.getcell("TIME_RANGE", 0)[0])),
        "t_max": float(time_to_mjd(obstable.getcell("TIME_RANGE", 0)[-1])),
        "t_exptime": float(obstable.getcell("TIME_RANGE", 0)[-1])
        - float(obstable.getcell("TIME_RANGE", 0)[0]),
    }
else:
    print("WARNING: Missing sub-table: OBSERVATION")
    obsdict = {}

swtable, table_error = _subtable(maintable, "SPECTRAL_WINDOW")
if not table_error:
    for row in range(swtable.nrows()):
        swdict = {
            "f_min": float(swtable.getcell("CHAN_FREQ", row)[0] / 1e6),
            "f_max": float(swtable.getcell("CHAN_FREQ", row)[-1] / 1e6),
            "em_xel": int(swtable.getcell("NUM_CHAN", row)),
        }
    if swtable.nrows() > 1:
        print("WARNING: table ", swtable, "has", swtable.nrows(), "rows")
else:
    print("WARNING: Missing sub-table: SPECTRAL_WINDOW")
    swdict = {}


poltable, table_error = _subtable(maintable, "POLARIZATION")
if not table_error:
    poldict = {
        "pol_states": stokes_polarisations(
            list(poltable.getcell("CORR_TYPE", 0))
        ),
        "pol_xel": int(poltable.getcell("NUM_CORR", 0)),
    }
else:
    print("WARNING: Missing sub-table: POLARIZATION")
    poldict = {}

pointtable, table_error = _subtable(maintable, "POINTING")

if not table_error:
    if pointtable.nrows() == 0:
        print("WARNING: POINTING table has", pointtable.nrows(), "rows")
        pointdict = {}
    else:
        pointdict = {
            "s_ra": float(pointtable.getcell("TARGET", 0)[0][0]),
            "s_dec": float(pointtable.getcell("TARGET", 0)[0][1]),
            "target_name": pointtable.getcell("NAME", 0),
        }
else:
    print("WARNING: Missing sub-table: POINTING")
    pointdict = {}


# Combine dictionaries:
joined_dict = {
    "obscore": maintabdict | antdict | obsdict | swdict | poldict | pointdict
}

pprint(joined_dict)


m = MetaData()
data = m.get_data()  # gets the _data attribute
data.obscore = {
    "access_estsize": int(get_dir_size(full_path)),
    "access_format": "application/unknown",  # application/x-tar-gzip
    "access_url": "console.cloud.google.com/storage/browser/"
    + "ska1-simulation-data/",
    "calib_level": 0,
    "dataproduct_type": "visibility",
    "facility_name": "SKA-Observatory",
    "instrument_name": "Unknown",
    "o_ucd": "stat.fourier",
    "obs_collection": "Unknown",
    "obs_id": "pb-test-20200425-00000",
    "pol_states": None,
    "pol_xel": None,
    "s_dec": None,
    "s_ra": None,
    "t_exptime": None,
    "t_max": None,
    "t_min": None,
    "t_resolution": None,
    "target_name": None,
}

data.config.image = "artefact.skao.int/ska-sdp-script-vis-receive"
data.config.processing_block = "pb-test-20200425-00000"
data.config.processing_script = "vis-receive"
data.config.version = "0.6.0"
data.execution_block = "eb-test-20200325-00001"
data.files.append = ({
    "description": "raw visibilities",
    "path": "vis.ms",
    "status": "working",
})
data.interface = "http://schema.skao.int/ska-data-product-meta/0.1"


def try_except(dictionary: dict, value_to_retrieve: str):
    try:
        value = dictionary[value_to_retrieve]
    except KeyError:
        print(f"Warning: could not find value '{value_to_retrieve}'")
        value = None
    return value


data.obscore.dataproduct_type = "MS"
data.obscore.ant_number = try_except(antdict, "ant_number")
data.obscore.facility_name = try_except(obsdict, "facility_name")
data.obscore.instrument_ant_diameter = try_except(
    antdict, "instrument_ant_diameter"
)
data.obscore.instrument_name = try_except(obsdict, "instrument_name")
data.obscore.o_ucd = "stat.fourier"
data.obscore.obs_publisher_did = try_except(obsdict, "obs_publisher_did")
data.obscore.pol_states = try_except(poldict, "pol_states")
data.obscore.pol_xel = try_except(poldict, "pol_xel")
data.obscore.s_dec = try_except(pointdict, "s_dec")
data.obscore.s_ra = try_except(pointdict, "s_ra")
data.obscore.t_exptime = try_except(obsdict, "t_exptime")
data.obscore.t_max = try_except(obsdict, "t_max")
data.obscore.t_min = try_except(obsdict, "t_min")
data.obscore.t_resolution = try_except(maintabdict, "t_resolution")
data.obscore.target_name = try_except(pointdict, "target_name")

m.write(f"gen/{file_name_with_extension}_meta-data.yaml")

print(f"Saved {file_name_with_extension}_meta-data.yaml")
