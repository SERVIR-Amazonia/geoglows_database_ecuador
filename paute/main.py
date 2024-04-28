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
prov = gpd.read_file("shp/ecuador.shp")
ec = prov.unary_union
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

plot.pacum_ec(raster="imerg.tif", ec_gdf=ec, prov_gdf=prov, paute_gdf=paute)
plot.pacum_paute(raster="imerg.tif", gdf=paute)
