import rioxarray  # noqa E402
from affine import Affine
import xarray
from shapely.geometry import box
import pyproj
from rasterio.plot import show
import matplotlib.pyplot as plt
from multiprocessing import Pool

import math

from geographiclib.geodesic import Geodesic


def latlon_to_metres(latitude, longitude, latitude_reference, longitude_reference):
    ret = Geodesic.WGS84.Inverse(
        latitude_reference, longitude_reference, latitude, longitude
    )
    distance = ret["s12"]
    bearing = ret["azi1"]
    return (distance, bearing)


def metres_to_latlon(latitude, longitude, eastings, northings):
    s12 = math.sqrt(eastings**2 + northings**2)
    azi1 = math.degrees(math.atan2(eastings, northings))
    ret = Geodesic.WGS84.Direct(latitude, longitude, azi1, s12)
    latitude_offset = ret["lat2"]
    longitude_offset = ret["lon2"]
    return (latitude_offset, longitude_offset)


def print_raster(raster):
    print(
        f"shape: {raster.rio.shape}\n"
        f"resolution: {raster.rio.resolution()}\n"
        f"bounds: {raster.rio.bounds()}\n"
        f"sum: {raster.sum().item()}\n"
        f"CRS: {raster.rio.crs}\n"
    )


def main():
    latitude_origin = 44.571
    longitude_origin = -125.149

    rds: xarray.DataArray = xarray.open_dataset("mosaic8mm.tiff", engine="rasterio")
    aff: Affine = rds.rio.transform()

    x = rds["x"].values
    y = rds["y"].values

    print_raster(rds)
    print(aff)

    with Pool(4) as p:
        results = p.starmap(
            latlon_to_metres,
            [
                (latitude, longitude, latitude_origin, longitude_origin)
                for latitude, longitude in zip(x, y)
            ],
        )
    lat = [latitude for latitude, _ in results]
    lon = [longitude for _, longitude in results]

    # Add lat lon to rds
    rds.coords["lat"] = (("y", "x"), lat)
    rds.coords["lon"] = (("y", "x"), lon)

    print_raster(rds)


if __name__ == "__main__":
    main()
