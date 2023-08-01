#!/usr/bin/env python3

"""
Script to run OSKAR interferometer simulation with a parameter file
specified in the command line.
"""
"""Nadia Steyn"""

import argparse
import configparser
import os
import sys

import matplotlib.pyplot as plt
import oskar


def convert_bytes(num):
    """
    this function will convert bytes to MB.... GB... etc
    """
    for x in ["bytes", "KB", "MB", "GB", "TB"]:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0


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
    file_without_extension, file_extension = os.path.splitext(vis_path)

    if file_extension.lower() == ".vis":
        full_path = vis_path
        path_without_ext = os.path.splitext(vis_path)[0]
    else:
        full_path = vis_path + ".vis"
        path_without_ext = vis_path

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
        fov_deg=5.5, image_size=8192
    )  # Make an image fov_deg degrees/ image_size pixels across

    imager.set(
        input_file=vis_path, output_root=path_without_ext + "_sky_model"
    )
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
