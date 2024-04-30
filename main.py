#
#
# HCC2 sample application using Modbus Client Engine (based on Pymodbus library)
#
import json
from optparse import OptionParser
import os
import logging
from threading import Event, Thread, Lock
import queue
from types import SimpleNamespace
from app import app
#
from hcc2sdk.classes.db import DB
from hcc2sdk.classes.server import Server
from hcc2sdk.lib.miscfuncs import text_to_log_level
from hcc2sdk.modbus_engine import modbus_engine
from hcc2sdk.config.config import Config
#
# Create an event to end the application when required
#     
event = Event()
event.clear() # make sure is not signaled
db_mutex = Lock()
control_queue = queue.Queue()
db = DB(control_queue, db_mutex) # main data DB for app
#
# Load config parameters from SDK library
#
config = Config()
#
# configure the service logging (including time format needed by HCC2 parsing pipeline)
#
logging.basicConfig( level=config.log.level,
    format=config.log.format,
    datefmt=config.log.date_format)
logger = logging.getLogger("PYSDK")
logger.setLevel (text_to_log_level(config.log.level))
if config.log.log_to_file == True:
    fh = logging.FileHandler(config.log.log_file, mode='w')
    fh.setLevel(logging.getLevelName(config.log.level))
    fmt = logging.Formatter(config.log.format)
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    logging.getLogger().propagate = False

# Needed to assert the correct log level words parsed in the HCC2
logging.addLevelName(logging.CRITICAL, "critical")
logging.addLevelName(logging.ERROR, "error")
logging.addLevelName(logging.WARNING, "warning")
logging.addLevelName(logging.INFO, "info")
logging.addLevelName(logging.DEBUG, "debug")

#
# Read command line parameters
# 
parser = OptionParser()
try:
    parser.add_option ("-s", "--host", dest="host", action="store", help=config.opts.host_help, default=config.app.server_default_host)
    parser.add_option ("-p", "--port", dest="port", action="store", help=config.opts.port_help, default=config.app.server_default_port)
    parser.add_option ("-u", "--unit", dest="unit", action="store", help=config.opts.unit_help, default=config.app.server_default_unit)
    parser.add_option ("-t", "--timeperiod", dest="time_period", action="store", help=config.opts.time_period_help, default=config.app.default_time_period)
    parser.add_option ("-c", "--controltimeperiod", dest="control_time_period", action="store", help=config.opts.control_time_period_help, default=config.app.default_control_time_period)
    parser.add_option ("-m", "--timeout", dest="timeout", action="store", help=config.opts.timeout_help, default=config.app.default_timeout)
    parser.add_option ("-r", "--retries", dest="retries", action="store", help=config.opts.retries_help, default=config.app.default_timeout)
    parser.add_option ("-v", "--version", dest="version", action="store_true", help=config.opts.version_help, default=False)
    (options, args) = parser.parse_args()
except Exception as e:
    logger.error("Invalid parameters. Try again. Error: " + str(e) + ". Program ABORTED.")
    exit()
#
# check parameters
# also Check if Environment variables were defined
# Note: Environment variables takes precedence over arguments.
#
if (options.version == True):
    logger.info("version: " + config.version)
    exit()

host = options.host
host = os.environ.get(config.env.modbus_host, host)
if (host == ""):
    logger.error("Found invalid host name, either on command line or env variable. Try again. Program ABORTED.")
    exit()
try:
    port = int(options.port)
    port = int(os.environ.get(config.env.modbus_port, port))
except Exception as e:
    logger.error("Found invalid modbus port Number, either on command line or env variable. Try again. Error: " + str(e) + ". Program ABORTED.")
    exit()
try:
    unit = int(options.unit)
    unit = int(os.environ.get(config.env.modbus_unit, unit))
except Exception as e:
    logger.error("Found invalid modbus unit Number, either on command line or env variable. Try again. Error: " + str(e) + ". Program ABORTED.")
    exit()
if (unit < 1 or unit > 254):
    logger.error("Found invalid modbus unit Number, either on command line or env variable. Try again. Received unit: " + str(unit) + ". Program ABORTED.")
    exit()
try:
    time_period = int(options.time_period)
    time_period = int(os.environ.get(config.env.time_period, time_period))
except Exception as e:
    logger.error("Found invalid scan time period, either on command line or env variable. Try again. Error: " + str(e) + ". Program ABORTED.")
    exit()
if (time_period < 100 or time_period > 99999):
    logger.error("Found invalid scan time period, either on command line or env variable. Try again. Received time period: " + str(time_period) + ". Program ABORTED.")
    exit()
try:
    control_time_period = int(options.control_time_period)
    control_time_period = int(os.environ.get(config.env.control_time_period, control_time_period))
except Exception as e:
    logger.error("Found invalid control time period, either on command line or env variable. Try again. Error: " + str(e) + ". Program ABORTED.")
    exit()
if (control_time_period < 100 or control_time_period > 99999 or control_time_period > time_period):
    logger.error("Found invalid control time period, either on command line or env variable. Try again. Received time period: " + str(time_period) + ". Program ABORTED.")
    exit()
try:
    timeout = float(options.timeout)
    timeout = float(os.environ.get(config.env.timeout, timeout))
except Exception as e:
    logger.error("Found invalid timeout, either on command line or env variable. Try again. Error: " + str(e) + ". Program ABORTED.")
    exit()
if (timeout < 0.0 or timeout > 9999.9):
    logger.error("Found invalid timeout, either on command line or env variable. Try again. Received timeout: " + str(timeout) + ". Program ABORTED.")
    exit()

try:
    retries = int(options.retries)
    retries = int(os.environ.get(config.env.retries, retries))
except Exception as e:
    logger.error("Found invalid retries count, either on command line or env variable. Try again. Error: " + str(e) + ". Program ABORTED.")
    exit()
if (retries < 0 or retries > 99):
    logger.error("Found invalid retries count, either on command line or env variable. Try again. Received timeout: " + str(retries) + ". Program ABORTED.")
    exit()
#
# put all server params in Server Object
#
server = Server(host, port, unit, time_period, control_time_period, timeout, retries)
#
# let's read the variables file!
#
var_file_path = config.variable_file
try:
    with open(var_file_path) as json_file:
        vars = json.load(json_file, object_hook=lambda d: SimpleNamespace(**d))
except Exception as e:
    print('Cannot read Variable configuration file. Program ABORTED. Error: %s', str(e))
    exit()
#
# Print version
#
logger.info('Engine version: ' + config.version)
#
# All seems to check out. Let's start the modbus client engine
#
# ----------------------------------------------------------------------- #
# run the Modbus client scanner engine
# ----------------------------------------------------------------------- #
try:  
    thread1 = Thread(target=modbus_engine, args=(logger, config, server, vars, db, event))
    thread1.start()
except Exception as e:
    logger.error("Exception trying to start modbus engine. Error: " + str(e) + ". Program ABORTED.")
    exit()
# ----------------------------------------------------------------------- #
# run the App thread
# ----------------------------------------------------------------------- #
try:  
    thread2 = Thread(target=app, args=(logger, db, event))
    thread2.start()
except Exception as e:
    logger.error("Exception trying to start app. Error: " + str(e) + ". Program ABORTED.")
    exit()
#
#
# Wait for threads to end
#
thread1.join()
thread2.join()
logger.info("APPLICATION ENDED.")

