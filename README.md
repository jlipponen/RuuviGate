# RuuviGate
Python3 application to push RuuviTag data to cloud. Only Azure IoT Central is currently supported.

## Acknowledgments
* [RuuviTag Sensor](https://github.com/ttu/ruuvitag-sensor) by _ttu_ used to poll RuuviTag data
* [Azure IoT SDKs for Python](https://github.com/Azure/azure-iot-sdk-python) used to publish the RuuviTag data

Elaborate list of used Python packages in _poetry.lock_

## Usage examples
Example usage of the RuuviGate application

### Prerequisites
* [Poetry](https://python-poetry.org/)
* Python (>=3.7)
* Azure IoT Central application with a device instance using the the DTDL templates in _azure-iot-central_ folder 

#### Azure configuration file (YAML)
```
IOTHUB_DEVICE_DPS_ID_SCOPE: [your-device-id-scope]
IOTHUB_DEVICE_DPS_DEVICE_ID: [your-device-id]
IOTHUB_DEVICE_DPS_DEVICE_KEY: [your-device-id-key]
IOTHUB_DEVICE_DPS_ENDPOINT: "global.azure-devices-provisioning.net"
IOTHUB_DEVICE_DPS_MODEL_ID: [your-device's-data-model-id]
IOTHUB_DEVICE_DPS_HOSTNAME: [your-provisioned-device-hostname] (optional, will be created during provisioning)
```

These values can be fetched from your Azure IoT Central application

#### RuuviTag MAC configuration file (YAML)
```
RU:UV:IM:AC:ADD:R1 (optional)
RU:UV:IM:AC:ADD:R2 (optional)
RU:UV:IM:AC:ADD:R3 (optional)
RU:UV:IM:AC:ADD:R4 (optional)
RU:UV:IM:AC:ADD:R5 (optional)
```
Notice that your device's (Azure IoT Central) datamodel should support the amount of Ruuvi's you specify. If none is specified, add them through the Azure IoT Central application.

### Virtualvenv installation and activation
```
poetry install
poetry shell
```

### Produce sample data to stdout
```
python ruuvigate -r /path/to/ruuvitags.yaml --mode stdout --interval 5 --loglevel INFO --simulate
```

### Produce sample data to Azure IoT Central
```
python ruuvigate -r /path/to/ruuvitags.yaml -a /path/to/azconf.yaml --interval 5 --loglevel INFO --simulate
```

### Publish RuuviTag data to Azure IoT Central
```
python ruuvigate -r /path/to/ruuvitags.yaml -a /path/to/azconf.yaml --interval 5 --loglevel INFO
```

## Azure IoT Central
Azure IoT Central by Microsoft has been the first cloud service to store and visualize RuuviGate published data:
https://azure.microsoft.com/en-us/services/iot-central/#overview

It stores 30 days worth of history with minimal costs. Rules can be created and for example an SMS alerts can triggered from an IoT Central application.

![Alt text](azure-iot-central/dashboard.png?raw=true "Azure IoT Central Dashboard")

It is also possible to specify device methods and run those from Azure IoT Central application.

![Alt text](azure-iot-central/device-methods.png?raw=true "Azure IoT Central Dashboard")
