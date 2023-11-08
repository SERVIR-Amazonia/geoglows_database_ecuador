#!/bin/bash 
cd ~/tethys_apps_ecuador/geoglows_database_ecuador
source .env set
$PYTHON_PATH r_gpm.py
$PYTHON_PATH r_nwsaffgs.py
$PYTHON_PATH r_report.py