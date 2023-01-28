# RuuviGate
Python package to push RuuviTag data to a cloud service.

## Acknowledgments
* [RuuviTag Sensor](https://github.com/ttu/ruuvitag-sensor) by _ttu_ used to poll RuuviTag data
* [Azure IoT SDKs for Python](https://github.com/Azure/azure-iot-sdk-python) used to publish the RuuviTag data

## Prerequisites
* [Poetry](https://python-poetry.org/)
* Python (>=3.8)
* Azure IoT Central application with a [RuuviGate](./resources/azure-iot-central/RuuviGate.json) device

## Build
```
poetry build
```

## Usage
Examples of configuration files:
- [ruuvitags.yml](./resources/ruuvitags.yml)
- [azure.yml](./resources/azure-iot-central/azure.yml)

### Produce sample data to stdout
```
python ruuvigate -r /path/to/ruuvitags.yml --mode stdout --interval 5 --loglevel INFO --simulate
```

### Produce sample data to Azure IoT Central
```
python ruuvigate -r /path/to/ruuvitags.yml -c /path/to/azure.yml --interval 5 --loglevel INFO --simulate
```

### Publish RuuviTag data to Azure IoT Central
```
python ruuvigate -r /path/to/ruuvitags.yml -c /path/to/azure.yml --interval 5 --loglevel INFO
```
