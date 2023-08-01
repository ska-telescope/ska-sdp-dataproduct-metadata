#!/usr/bin/env python3

"""Script to run OSKAR interferometer simulation with a parameter file specified in the command line."""
"""Nadia Steyn"""

import argparse
import configparser  # for reading in the .ini file.
import os
import sys
from pprint import pprint

import matplotlib.pyplot as plt
import oskar
from astropy.time import Time, TimeDelta
from casacore import tables

from ska_sdp_dataproduct_metadata import MetaData


def _subtable(tbl: tables.table, name: str, readonly=True):
    """Extract subtable from MeasurementSet"""
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
    """Convert from seconds to days, and take leap seconds into account"""
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
    """Calculate file size in kb"""
    total = 0
    with os.scandir(path) as folder:
        for entry in folder:
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                total += get_dir_size(entry.path)
    return total / 1024


def convert_bytes(num):
    """
    this function will convert bytes to MB.... GB... etc
    """
    for x in ["bytes", "KB", "MB", "GB", "TB"]:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0


def get_filename(file_path):
    """Get filename without extension"""
    file_path = file_path.rstrip("/")
    filename = os.path.splitext(os.path.basename(file_path))[0]

    return filename


print("\noskarpy version:", oskar.__version__)
print("python version:", sys.version, "\n")

"""
The user inputs the directory to the .ini config file in the command line
"""
parser = argparse.ArgumentParser()
parser.add_argument(
    "parameter_file", help="name of configuration file to use, .ini or .txt"
)

# Extract the list of all OSKAR parameters:
settings = oskar.SettingsTree("oskar_sim_interferometer")
OSKAR_DICT = settings.to_dict(include_defaults=True)
parameter_names = OSKAR_DICT.keys()
parameters = [
    parser.add_argument("--" + parameter_name)
    for parameter_name in parameter_names
]

args = parser.parse_args()

# Read in the given .ini file
config_file = args.parameter_file
config = configparser.ConfigParser()
config.read(config_file)

# Make required updates to settings tree:
config.set("simulator", "keep_log_file", "true")  # save the log file
for key in args.__dict__:
    if args.__dict__[key] is not None and key != "parameter_file":
        print("Update:", key, args.__dict__[key])
        key_names = key.split("/")
        config.set(key_names[0], "/".join(key_names[1:]), args.__dict__[key])


"""
Write an updated .ini file
"""
parameter_file = "gen/updated_" + str(os.path.basename(config_file))
with open(parameter_file, "w") as updated_parameter_file:
    config.write(
        updated_parameter_file, space_around_delimiters=False
    )  # Write updated .ini file
    updated_parameter_file.close()
command = "oskar_sim_interferometer " + parameter_file


"""
Run OSKAR directly in the Singularity
"""
os.system(command)


"""
Get size of output files
"""
config.read(parameter_file)  # read updated parameter file
try:
    vis_path = config["interferometer"]["oskar_vis_filename"]
    print("size of", vis_path, ":")
    vis_size = os.stat(vis_path).st_size
    print(convert_bytes(vis_size))
except KeyError:
    print("\nNo .vis data saved.")

ms_path = config["interferometer"]["ms_filename"]
ms_size = 0
for path, dirs, files in os.walk(ms_path):
    for f in files:
        fp = os.path.join(path, f)
        ms_size += os.path.getsize(fp)
print("size of", ms_path, ":")
print(convert_bytes(ms_size))


"""
Save an image of the Ionospheric screen
"""
try:
    screen_path = config["telescope"]["external_tec_screen/input_fits_file"]
    print("\nsize of screen,", screen_path, ":")
    screen_size = os.stat(screen_path).st_size
    print(convert_bytes(screen_size))

    from astropy.io import fits
    from astropy.wcs import WCS

    hdu = fits.open(screen_path)
    wcs = WCS(hdu[0].header, naxis=2)
    CDELT1 = hdu[0].header["CDELT1"]
    CDELT2 = hdu[0].header["CDELT2"]
    DIM = hdu[0].header["NAXIS1"]
    FOV = CDELT1 * DIM
    # Print specs:
    print("screen shape:", hdu[0].data.shape)
    print("pixel size:", CDELT1, "m x", CDELT2, "m")
    print("screen width:", FOV, "m")
    try:
        print(
            "screen height:",
            config["telescope"]["external_tec_screen/screen_height_km"],
            "km",
        )
    except KeyError:
        print("screen height: 300 km")  # default screen height

    fig = plt.figure()
    ax = fig.add_subplot(projection=wcs)
    if hdu[0].data.ndim == 4:
        im = plt.imshow(hdu[0].data[0][0])
    elif hdu[0].data.ndim == 3:
        im = plt.imshow(hdu[0].data[0])
    plt.colorbar(im)
    hdu.close()
    plt.savefig("ionospheric_screen.png")
    print("Saved image of ionospheric screen: ionospheric_screen.png")

except KeyError:
    print("No ionospheric screen given.")


"""
Image the simulated visibilities using oskar.Imager
"""
try:  # if oskar_vis_filename is given
    try:  # use the specified precision
        dbl_prec = config["simulator"]["double_precision"]
        if dbl_prec == "true":
            precision = "double"
        else:
            precision = "single"
    except KeyError:
        precision = "double"
    imager = oskar.Imager(precision)
    imager.set(
        fov_deg=4, image_size=512
    )  # Make an image 4 degrees/512 pixels across
    imager.set(input_file=vis_path, output_root=vis_path + "sky_model")
    data = imager.run(
        return_images=1
    )  # A FITS file named %_I.fits will be written
    image = data["images"][0]

    fig = plt.figure()
    infile = "%s_I.fits" % imager.output_root
    from astropy.io import fits
    from astropy.wcs import WCS

    hdu = fits.open(infile)
    wcs = WCS(hdu[0].header, naxis=2)
    ax = fig.add_subplot(projection=wcs)
    im = plt.imshow(
        image, cmap="jet"
    )  # Pass image to Python and render using matplotlib
    plt.colorbar(im)
    plt.savefig("%s.png" % imager.output_root)
    print("\nSaved image of sky model: %s.png" % imager.output_root)
    print("precision:", precision)

except NameError:
    print("No .vis data saved, therefore no sky model image generated.")

plt.close("all")

print("\nOSKAR interferometer run complete.\n")

print("Writing metadata...\n")

maintable = tables.table(ms_path, readonly=True, ack=False)

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
    "access_estsize": int(get_dir_size(ms_path)),
    "access_format": "application/unknown",  # application/x-tar-gzip?
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
data.files.append(
    {
        "description": "raw visibilities",
        "path": "vis.ms",
        "status": "working",
    }
)
data.interface = "http://schema.skao.int/ska-data-product-meta/0.1"


def try_except(dictionary: dict, value_to_retrieve: str):
    """If a value doesn't exist, the script shouldn't crash"""
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

metadata_filename = get_filename(ms_path)
m.write(f"gen/{metadata_filename}_metadata.yaml")

print(f"Saved {metadata_filename}_metadata.yaml")
