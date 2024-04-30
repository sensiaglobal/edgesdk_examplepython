#
#
# HCC2 sample application using Modbus Client Engine (based on Pymodbus library)
#

# -----------------------------------------------------------------------------
#
# Main entry 
#
# ------------------------------------------------------------------------------
import math
import os
import json
from hcc2sdk.classes.variablemodel import quality_enum


def app(logger, db, event):
    
    try:
        with open(os.path.join('appconfig/', 'config.json')) as json_file:
            appcfg = json.load(json_file)
    except Exception as e:
        logger.error('Cannot read Application configuration file. Program ABORTED. Error: %s', str(e))
        return

    logger.name = "PYAPP"                   # give your logging context a name to appear in Unity
    logger.info("App: " + appcfg['app']['name'] + ", Version: " + appcfg['app']['version']) 

    while (True):
        #
        # wait for event to ensure the data source loop has finished its scan
        #
        event.wait()
        event.clear()
        #
        # do some calcs 
        #
        v1 = db.get_value("cpu_temp")
        v2 = db.get_value("cpu_usage")
        v3 = db.get_value("mem_percentage_used")
        v4 = db.get_value("local_time_second")
        

        if v1.quality == quality_enum.OK and v2.quality == quality_enum.OK and v3.quality == quality_enum.OK and v4.quality == quality_enum.OK:
            result = v1.value - 273.15
            db.set_value("result", result, quality_enum.OK)
        
