# Import libraries and dependencies
import os
import datetime
import urllib.request
import gzip
import shutil
from dotenv import load_dotenv
import geopandas as gpd
import pandas as pd
from hsclient import HydroShare


# Change the work directory
user = os.getlogin()
user_dir = os.path.expanduser('~{}'.format(user))
os.chdir(user_dir)
os.chdir("tethys_apps_ecuador/geoglows_database_ecuador")

# Import enviromental variables
load_dotenv()
NWSAFFGS_USER = os.getenv('NWSAFFGS_USER')
NWSAFFGS_PASS = os.getenv('NWSAFFGS_PASS')
HS_USER = os.getenv('HS_USER')
HS_PASS = os.getenv('HS_PASS')
HS_IDRS = os.getenv('HS_ID02')


NWSAFFGS_USER="ecu"
NWSAFFGS_PASS="20-ffGS.ecU-23"

HS_USER="pronostico.inamhi"
HS_PASS="Pronostico2023*"
HS_IDRS="352379cf82444fd099eca8bfc662789b"

run_hour = "12"
print(run_hour)


# Read the shapefile
shapefile_path = 'shp/nwsaffgs_ecuador_basins_v2.shp'
gdf_shapefile = gpd.read_file(shapefile_path)


# Define the function to retrieve data from the server
def get_file(product, filename, run, colname):
    # Change the work directory
    os.chdir(user_dir)
    os.chdir("data/nwsaffgs")
    #
    # Generate the actual date
    actual_date = datetime.datetime.now() + datetime.timedelta(hours=-5)
    actual_year = actual_date.strftime("%Y")
    actual_month = actual_date.strftime("%m")
    actual_day = actual_date.strftime("%d")
    actual_hour = run
    print(actual_date)
    #
    # URL for the comprimed file (*.gz)
    url = "https://nwsaffgs-ubuntu.hrcwater.org/NWSAFFGS_CONSOLE/EXPORTS/REGIONAL/{0}/{1}/{2}/{4}_TXT/{0}{1}{2}-{3}00_ffgs_prod_{5}_regional.txt.gz"
    url = url.format(actual_year, actual_month, actual_day, actual_hour, product, filename)
    #
    # Download the *.gz file
    gz_filename = "data.gz"
    password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    password_mgr.add_password(None, url, NWSAFFGS_USER, NWSAFFGS_PASS)
    handler = urllib.request.HTTPBasicAuthHandler(password_mgr)
    opener = urllib.request.build_opener(handler)
    urllib.request.install_opener(opener)
    with urllib.request.urlopen(url) as response, open(gz_filename, 'wb') as out_file:
        shutil.copyfileobj(response, out_file)
    #
    # Tar the *.gz file
    output_filename = "data.txt"  # Nombre del archivo descomprimido
    with gzip.open(gz_filename, 'rb') as gz_file, open(output_filename, 'wb') as out_file:
        shutil.copyfileobj(gz_file, out_file)
    print("Download successfully completed!")
    #
    # Read the file and join
    data_nwsaffgs = pd.read_table("data.txt", sep="\t")
    data_nwsaffgs.columns = ["BASIN", colname]
    return(data_nwsaffgs)



# Humedad Promedio del Suelo (ASM)
asm = get_file(product = "ASM", filename = "est_asm_sacsma_06hr", run = run_hour, colname="asm")

# Precipitacion crítica para crecida (FFG)
ffg = get_file(product = "FFG", filename = "est_ffg_smffg_06hr", run = run_hour, colname="ffg")

# Pronostico de precipitacion WRF proximas 6 horas
fmap06 = get_file(product = "FMAP2", filename = "fcst_map_forecast2_06hr", run = run_hour, colname="fmap06")

# Pronostico de precipitacion WRF proximas 24 horas
fmap24 = get_file(product = "FMAP2", filename = "fcst_map_forecast2_24hr", run = run_hour, colname="fmap24")

# Pronostico de riesgo de crecidas repentinas proximas 12 horas
ffr12 = get_file(product = "FFR2", filename = "fcst_ffr_outlook2_12hr", run = run_hour, colname="ffr12")

# Pronostico de riesgo de crecidas repentinas proximas 24 horas
ffr24 = get_file(product = "FFR2", filename = "fcst_ffr_outlook2_24hr", run = run_hour, colname="ffr24")


# Merge data
nwsaffds_data = pd.merge(asm, ffg, on="BASIN", how="outer")
nwsaffds_data = pd.merge(nwsaffds_data, fmap06, on="BASIN", how="outer")
nwsaffds_data = pd.merge(nwsaffds_data, fmap24, on="BASIN", how="outer")
nwsaffds_data = pd.merge(nwsaffds_data, ffr12, on="BASIN", how="outer")
nwsaffds_data = pd.merge(nwsaffds_data, ffr24, on="BASIN", how="outer")

# Combine data with shapefile
gdf_merged = gdf_shapefile.merge(nwsaffds_data, left_on='BASIN', right_on='BASIN', how='left')


# Save the new shapefile
output_shapefile_path = 'nwsaffds.shp'
gdf_merged.to_file(output_shapefile_path)
print("Merged data!")

# Upload to geoserver (hydroshare)
hs = HydroShare(username=HS_USER, password=HS_PASS)
res = hs.resource(HS_IDRS)
file_list = ['nwsaffds.cpg', 'nwsaffds.dbf', 'nwsaffds.prj', 'nwsaffds.shp', 'nwsaffds.shx']
res.file_upload(*file_list)
print("Data uploaded to hydroshare!")
