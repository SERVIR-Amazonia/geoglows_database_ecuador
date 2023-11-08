#!/bin/bash 
cd ~/tethys_apps_ecuador/geoglows_database_ecuador
if [ ! -f .env ]
then
  export $(cat .env | xargs)
fi
echo $PYTHON_PATH
$PYTHON_PATH r_gpm.py
$PYTHON_PATH r_nwsaffgs.py
$PYTHON_PATH r_report.py