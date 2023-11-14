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
from scipy import stats
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




# Calc 7q10 threshold for high warnings levels
def get_warning_low_level(comid, data):
    def __calc_method__(ts):
        # Result dictionary
        rv = {'empirical' : {},
              'norm'      : {'fun': stats.norm,     'para' : {'loc': np.nanmean(ts), 'scale': np.nanstd(ts)}},
              'pearson3'  : {'fun': stats.pearson3, 'para' : {'loc': np.nanmean(ts), 'scale': np.nanstd(ts), 'skew': 1}},
              'dweibull'  : {'fun': stats.dweibull, 'para' : {'loc': np.nanmean(ts), 'scale': np.nanstd(ts), 'c'   : 1}},
              'chi2'      : {'fun' : stats.chi2,    'para' : {'loc': np.nanmean(ts), 'scale' : np.nanstd(ts), 'df' : 2}},
              'gumbel_r'  : {'fun' : stats.gumbel_r,'para' : {'loc': np.nanmean(ts) - 0.45005 * np.nanstd(ts), 'scale' : 0.7797 * np.nanstd(ts)}}}
        # Extract empirical distribution data
        freq, cl = np.histogram(ts, bins='sturges')
        freq = np.cumsum(freq) / np.sum(freq)
        cl_marc = (cl[1:] + cl[:-1]) / 2
        # Save values
        rv['empirical'].update({'freq': freq,'cl_marc': cl_marc})
        # Function for stadistical test
        ba_xi2 = lambda o, e : np.square(np.subtract(o,e)).mean() ** (1/2)
        # Add to probability distribution the cdf and the xi test
        for p_dist in rv:
            if p_dist == 'empirical':
                continue
            # Build cummulative distribution function (CDF)
            rv[p_dist].update({'cdf' : rv[p_dist]['fun'].cdf(x = cl_marc, **rv[p_dist]['para'])})
            # Obtain the xi test result
            rv[p_dist].update({f'{p_dist}_x2test' : ba_xi2(o = rv[p_dist]['cdf'], e = freq)})
        # Select best probability function
        p_dist_comp = pd.DataFrame(data={'Distribution' : [p_dist for p_dist in rv if p_dist != 'empirical'],
                                         'xi2_test'     : [rv[p_dist][f'{p_dist}_x2test'] for p_dist in rv if p_dist != 'empirical']})
        p_dist_comp.sort_values(by='xi2_test', inplace = True)
        p_dist_comp.reset_index(drop = True, inplace = True)
        best_p_dist = p_dist_comp['Distribution'].values[0]
        return rv[best_p_dist]['fun'](**rv[best_p_dist]['para'])
    # Previous datatime manager
    data_cp = data.copy()
    data_cp = data_cp.rolling(window=7).mean()
    data_cp = data_cp.groupby(data_cp.index.year).min().values.flatten()
    # Calc comparation value
    rv = {}
    for key in {'7q10' : 1}:
        res = __calc_method__(data_cp)
        # TODO: Fix in case of small rivers get 7q10 negative
        val = res.ppf([0.01]) if res.ppf([0.01]) > 0 else 0    # Modified 7q5
        rv.update({key : val})
    # Build result dataframe
    d = {'rivid': [comid]}
    d.update(rv)
    # Parse to dataframe
    corrected_low_warnings_df = pd.DataFrame(data=d)
    corrected_low_warnings_df.set_index('rivid', inplace=True)
    return corrected_low_warnings_df

# Excedence warning low
def get_occurrence_low_warning(ensem, warnings):
    # Build esnsemble comparation time serie
    ts = ensem.quantile(0.75, axis = 1).copy()
    ts = ts.groupby(ts.index.year.astype(str) +'/'+ ts.index.month.astype(str) +'/'+ ts.index.day.astype(str)).min()
    # Count warnings alerts
    rv = {}
    for warning in warnings.columns:
        rv[warning] = len(ts[ts < warnings[warning].values[0]])
    # Assing warnings
    if rv['7q10'] >= 5 and rv['7q10'] < 7 :
        return 'S1'
    elif rv['7q10'] >= 7 and rv['7q10'] < 10 :
        return 'S2'
    elif rv['7q10'] >= 10 :
        return 'S3'
    else:
        return 'S0'
    

###############################################################################################################
#                                                Main Function                                                #
###############################################################################################################

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
        station_comid = drainage.comid[i]
        simulated_data = get_format_data("select * from r_{0} where datetime < '2022-06-01' and datetime > '1979-01-02';".format(station_comid), conn)
        ensemble_forecast = get_format_data("select * from f_{0};".format(station_comid), conn)
        warnings_low_level = get_warning_low_level(comid = station_comid, data  = simulated_data)
        warning_drought = get_occurrence_low_warning(ensem=ensemble_forecast, warnings=warnings_low_level)
        # Warning
        drainage.loc[i, ['drought']] = warning_drought
        print(f"{station_comid} - {warning_drought}")
    except:
        print(f"Error en tramo: {station_comid}")
    

# Insert to database
drainage.to_sql('drainage_network', con=conn, if_exists='replace', index=False)

# Close connection
conn.close()


