# RuuviAzureGateway
Python3 application to publish RuuviTag data to Azure IoT Central

Following cofiguration files are needed to run the application:

## Azure configuration file (YAML)
IOTHUB_DEVICE_DPS_ID_SCOPE: "your-device-id-scope" \
IOTHUB_DEVICE_DPS_DEVICE_ID: "your-device-id" \
IOTHUB_DEVICE_DPS_DEVICE_KEY: "your-device-id-key" \
IOTHUB_DEVICE_DPS_ENDPOINT: "global.azure-devices-provisioning.net" \
IOTHUB_DEVICE_DPS_MODEL_ID: "your-device's-data-model-ide" \
IOTHUB_DEVICE_DPS_HOSTNAME: "your-provisioned-device-hostname" (optional, will be created during provisioning) \

## RuuviTag MAC configuration file (YAML)
RU:UV:IM:AC:ADD:R1: 1
RU:UV:IM:AC:ADD:R1: 2
RU:UV:IM:AC:ADD:R1: 3
RU:UV:IM:AC:ADD:R1: 4
RU:UV:IM:AC:ADD:R1: 5
.
.
.

Notice that your device's datamodel should support the amount of Ruuvi's you specify