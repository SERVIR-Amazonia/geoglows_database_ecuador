import os
import plot
import imerg
import geopandas as gpd

import shutil


# Change the work directory
user = os.getlogin()
user_dir = os.path.expanduser('~{}'.format(user))
os.chdir(user_dir)
os.chdir("tethys_apps_ecuador/geoglows_database_ecuador")

# Read PAUTE basin SHP
paute = gpd.read_file("shp/paute.shp")
ec = gpd.read_file("shp/ecuador.shp")
print("Reading SHP files")

# Change the work directory
user = os.getlogin()
user_dir = os.path.expanduser('~{}'.format(user))
os.chdir(user_dir)
os.chdir("data/paute")

imerg.get(
    outpath="../paute_final/imerg.tif")

#plot.pacum(
#    raster="imerg.tif", 
#    gdf=ec, 
#    title="Ecuador Continental", 
#    xylim=[-81.3, -74.9, -5.2, 1.6], 
#    fig_path="../../tethys_apps_ecuador/geoglows_database_ecuador/paute/ecuador.png")

#plot.pacum("pacum_paute.tif", gdf=paute, fig_path="../../tethys_apps_ecuador/geoglows_database_ecuador/paute/paute-pacum.png")

for f in os.listdir():
    os.remove(f)
#shutil.copy(pa)