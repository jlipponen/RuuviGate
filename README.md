# RuuviGate
Python package to push RuuviTag data to a cloud service.

## Acknowledgments
* [RuuviTag Sensor](https://github.com/ttu/ruuvitag-sensor) by _ttu_ used to poll RuuviTag data
* [Azure IoT SDKs for Python](https://github.com/Azure/azure-iot-sdk-python) used to publish the RuuviTag data

## Prerequisites
* Python (>=3.8)
* Azure IoT Central application with a [RuuviGate](./resources/azure-iot-central/RuuviGate.json) device
* Poetry (>=1.5.1)

## Installing
Install local version
```
> poetry build
> pip install ./dist/ruuvigate-<version>-py3-none-any.whl
```
Install from GitHub releases
```
> pip install https://github.com/jlipponen/RuuviGate/releases/download/<version>/ruuvigate-<version>-py3-none-any.whl
```

## Usage
Examples of configuration files:
- [ruuvitags.yml](./resources/ruuvitags.yml)
- [azure.yml](./resources/azure-iot-central/azure.yml)

### Produce sample data to stdout
```
> python3 -m ruuvigate -r /path/to/ruuvitags.yml --mode stdout --interval 5 --loglevel INFO --simulate
```

### Produce sample data to Azure IoT Central
```
> python3 -m ruuvigate -r /path/to/ruuvitags.yml -c /path/to/azure.yml --interval 5 --loglevel INFO --simulate
```

### Publish RuuviTag data to Azure IoT Central
```
> python3 -m ruuvigate -r /path/to/ruuvitags.yml -c /path/to/azure.yml --interval 5 --loglevel INFO
```

## Development

### Install dependencies
```
> poetry install
```

### Run unit tests
```
> poetry run pytest
```

## Typing
Check typing
```
> poetry run mypy .
```

### Formatting
Check formatting
```
> poetry run yapf --diff --recursive .
```
Apply formatting
```
> poetry run yapf -i --recursive .
```
