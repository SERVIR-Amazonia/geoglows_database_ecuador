import os
import geopandas as gpd
from dotenv import load_dotenv
from .imerg import get_imerg
from .plot import get_pacum_plot


# Change the work directory
user = os.getlogin()
user_dir = os.path.expanduser('~{}'.format(user))
os.chdir(user_dir)
os.chdir("tethys_apps_ecuador/geoglows_database_ecuador")

# Read PAUTE basin SHP
paute = gpd.read_file("shp/paute.shp")
print("Reading Paute Basin")

# Change the work directory
user = os.getlogin()
user_dir = os.path.expanduser('~{}'.format(user))
os.chdir(user_dir)
os.chdir("data/paute")

get_imerg()
get_pacum_plot("pacum_paute.tif", gdf=paute)