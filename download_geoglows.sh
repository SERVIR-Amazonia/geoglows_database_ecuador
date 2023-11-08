#!/bin/bash 
cd ~/tethys_apps_ecuador/geoglows_database_ecuador
source .env set
$PYTHON_PATH r_forecast_analysis.py
$PYTHON_PATH r_corrected_forecast_analysis.py
$PYTHON_PATH r_drougth_analysis.py 