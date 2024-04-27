import os
import plot
import imerg
import geopandas as gpd


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

# Download data
imerg.get(outpath="../paute_final/imerg.tif")

# Change the work directory
os.chdir("../paute_final")

plot.pacum_ec(raster="imerg.tif", gdf=ec)
plot.pacum_paute(raster="imerg.tif", gdf=paute)


#plot.pacum("pacum_paute.tif", gdf=paute, fig_path="../../tethys_apps_ecuador/geoglows_database_ecuador/paute/paute-pacum.png")


#shutil.copy(pa)