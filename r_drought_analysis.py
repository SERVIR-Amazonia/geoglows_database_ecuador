# Import libraries and dependencies
import os
import psycopg2
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import geoglows
import numpy as np
import math
import datetime
import warnings
warnings.filterwarnings('ignore')

# Change the work directory
user = os.getlogin()
user_dir = os.path.expanduser('~{}'.format(user))
os.chdir(user_dir)
os.chdir("tethys_apps_ecuador/geoglows_database_ecuador")

# Import enviromental variables
load_dotenv()
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DB_NAME = os.getenv('DB_NAME')

# Generate the conection token
token = "postgresql+psycopg2://{0}:{1}@localhost:5432/{2}".format(DB_USER, DB_PASS, DB_NAME)



###############################################################################################################
#                                 Function to get and format the data from DB                                 #
###############################################################################################################
def get_format_data(sql_statement, conn):
    # Retrieve data from database
    data =  pd.read_sql(sql_statement, conn)
    # Datetime column as dataframe index
    data.index = data.datetime
    data = data.drop(columns=['datetime'])
    # Format the index values
    data.index = pd.to_datetime(data.index)
    data.index = data.index.to_series().dt.strftime("%Y-%m-%d %H:%M:%S")
    data.index = pd.to_datetime(data.index)
    # Return result
    return(data)

###############################################################################################################
#                                                  Getting Q10                                                #
###############################################################################################################
def get_quantile(data, quantile):
    df = simulated_data.quantile(quantile, axis=0).to_frame()
    df.rename(columns = {quantile: "q"}, inplace = True)
    return(df["q"][0])

###############################################################################################################
#                                         Getting ensemble statistic                                          #
###############################################################################################################
def ensemble_quantile(ensemble, quantile, label):
    df = ensemble.quantile(quantile, axis=1).to_frame()
    df.rename(columns = {quantile: label}, inplace = True)
    df =  df.groupby(df.index.strftime("%Y-%m-%d")).min()
    return(df)

###############################################################################################################
#                                   Getting return periods from data series                                   #
###############################################################################################################
def gumbel_1(std: float, xbar: float, rp: int or float) -> float:
  return -math.log(-math.log(1 - (1 / rp))) * std * .7797 + xbar - (.45 * std)

def get_return_periods(comid, data):
    data = 1/(data + 0.1)
    # Stats
    max_annual_flow = data.groupby(data.index.strftime("%Y")).max()
    mean_value = np.mean(max_annual_flow.iloc[:,0].values)
    std_value = np.std(max_annual_flow.iloc[:,0].values)
    # Return periods
    return_periods = [25, 10, 5, 2]
    return_periods_values = []
    # Compute the corrected return periods
    for rp in return_periods:
      return_periods_values.append(gumbel_1(std_value, mean_value, rp))
    # Parse to list
    d = {'rivid': [comid], 
         'return_period_25': [(1/return_periods_values[0]) - 0.1], 
         'return_period_10': [(1/return_periods_values[1]) - 0.1], 
         'return_period_5': [(1/return_periods_values[2]) - 0.1],
         'return_period_2': [(1/return_periods_values[3]) - 0.1]}
    # Parse to dataframe
    corrected_rperiods_df = pd.DataFrame(data=d)
    corrected_rperiods_df.set_index('rivid', inplace=True)
    return(corrected_rperiods_df)



# Setting the connetion to db
db = create_engine(token)

# Establish connection
conn = db.connect()

# Getting stations
drainage = pd.read_sql("select * from drainage_network;", conn)
drainage["drought"] = drainage["alert"]

# Number of stations
n = len(drainage)

# For loop 
for i in range(n):
    station_comid = drainage.comid[i]
    try:
        # Query to database 
        simulated_data = get_format_data("select * from r_{0};".format(station_comid), conn)
        ensemble_forecast = get_format_data("select * from f_{0};".format(station_comid), conn)
        # Forecast stats
        ensemble_median = ensemble_quantile(ensemble_forecast, 0.5, "Median")
        return_periods = get_return_periods(station_comid, simulated_data)
        # Quantiles
        q15 = return_periods["return_period_2"]#get_quantile(simulated_data, 0.03)
        q10 = return_periods["return_period_5"]#get_quantile(simulated_data, 0.02)
        q05 = return_periods["return_period_10"]#get_quantile(simulated_data, 0.01)
        # Indexes
        index_7q15 = sum((ensemble_median < q15).to_numpy())[0] >= 7
        index_7q10 = sum((ensemble_median < q10).to_numpy())[0] >= 7
        index_7q05 = sum((ensemble_median < q05).to_numpy())[0] >= 7
        # Alertas
        warning_drought = "S0"
        if(index_7q15):
            warning_drought = "S1"
        if(index_7q10):
            warning_drought = "S2"
        if(index_7q05):
            warning_drought = "S3"
        # Warning
        drainage.loc[i, ['drought']] = warning_drought
        print(f"{station_comid} - {warning_drought}")
    except:
        print(f"Error en tramo: {station_comid}")
    

# Insert to database
drainage.to_sql('drainage_network', con=conn, if_exists='replace', index=False)

# Close connection
conn.close()






