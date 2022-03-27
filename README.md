# RuuviGate
Python3 application to push RuuviTag data to cloud. Only Azure IoT Central is currently supported.

Following cofiguration files are used by the application.

## Azure configuration file (YAML), mandatory
```
IOTHUB_DEVICE_DPS_ID_SCOPE: [your-device-id-scope]
IOTHUB_DEVICE_DPS_DEVICE_ID: [your-device-id]
IOTHUB_DEVICE_DPS_DEVICE_KEY: [your-device-id-key]
IOTHUB_DEVICE_DPS_ENDPOINT: "global.azure-devices-provisioning.net"
IOTHUB_DEVICE_DPS_MODEL_ID: [your-device's-data-model-id]
IOTHUB_DEVICE_DPS_HOSTNAME: [your-provisioned-device-hostname] (optional, will be created during provisioning)
```

These values can be fetched from your Azure IoT Central application

## RuuviTag MAC configuration file (YAML), optional
```
RU:UV:IM:AC:ADD:R1
RU:UV:IM:AC:ADD:R2
RU:UV:IM:AC:ADD:R3
RU:UV:IM:AC:ADD:R4
RU:UV:IM:AC:ADD:R5
```
Notice that your device's (Azure IoT Central) datamodel should support the amount of Ruuvi's you specify. If none is specified, add them through the Azure IoT Central application.
