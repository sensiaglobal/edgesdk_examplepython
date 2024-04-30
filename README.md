# HCC2 Application Example using SDK in python

This is a fully runnable sample code for an python application to be deployed in HCC2 using the HCC2 SDK.

This application can be copied to another folder to start a new application. Use this command:

```
cp -r ~/<code_directory>/edgesdkexample/ ~/<code_directory>/<myapplication>/
```

### Modbus Registers

This application is already configured to scan 4 Modbus Input Register and 1 Holding Register.
The holding register is writable so results can be written back to this register.

Register definition (see: appconfig/vars.json)

+ IR 00 (30001): cpu_temp (mapped to HCC2 cpu_temp internal tag)
+ IR 02 (30003): cpu_usage (mapped to HCC2 cpu_usage internal tag)
+ IR 04 (30005): mem_percentage_used (mapped to HCC2 mem_percentage_used internal tag)
+ IR 06 (30007): local_time_second (maped to HCC2 clock seconds)

+ HR 00 (40001): result - here goes the calculation made by this app.

### Sample Calculation

result = cpu_temp - 273.15

### Notes

You need to install the HCC2SDK package to let this app to run.
The latest version (to-this-date) is already downloaded in thew packages/ folder.

In the case you receive or download a new version of the SDK package, do the following:

1. An updated SDK package can be found in https://github.com/sensiaglobal/qratehcc2sdk/edgesdk_python_api repository.

2. To install the package:
```
pip install packages/hcc2sdk-X.X.X-py3-none-any.whl --force-reinstall
```
(X.X.X is the package version number)

3. To check if it is already installed:
```
pip list | grep hcc2sdk
```