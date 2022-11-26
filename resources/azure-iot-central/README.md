# Azure IoT Central
Azure IoT Central by Microsoft has been the first cloud service to store and visualize RuuviGate published data:
https://azure.microsoft.com/en-us/services/iot-central/#overview

It stores 30 days worth of history with minimal costs. Rules can be created and for example an SMS alerts can triggered from an IoT Central application.

![Alt text](./dashboard.png?raw=true "Azure IoT Central Dashboard")

It is also possible to specify device methods and run those from Azure IoT Central application.

![Alt text](./device-methods.png?raw=true "Azure IoT Central Dashboard")

## Configuration
After creating an Azure IoT Central application and instantiating a [RuuviGate](.RuuviGate.json) device, write the device configuration to the [azure.yml](./azure.yml) file. You can fetch the needed data from your device instance (under _connect_ option) and the used template.
