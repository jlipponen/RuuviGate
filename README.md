# RuuviGate
Python package to publish RuuviTag data to cloud services.

## Acknowledgments
* [RuuviTag Sensor](https://github.com/ttu/ruuvitag-sensor) by _ttu_ used to poll RuuviTag data
* [Azure IoT SDKs for Python](https://github.com/Azure/azure-iot-sdk-python) used to publish RuuviTag data to Azure

## Prerequisites
* Python (>=3.10)
* uv (>=0.9.0)
* Azure IoT Central application with a [RuuviGate](./resources/azure-iot-central/RuuviGate.json) device

## Installation
Install locally build version
```
> uv build
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

### Write sample data to stdout
```
> python3 -m ruuvigate -r /path/to/ruuvitags.yml --mode stdout --interval 5 --loglevel INFO --simulate
```

### Publish sample data to Azure IoT Central
```
> python3 -m ruuvigate -r /path/to/ruuvitags.yml -c /path/to/azure.yml --interval 5 --loglevel INFO --simulate
```

### Publish RuuviTag data to Azure IoT Central
```
> python3 -m ruuvigate -r /path/to/ruuvitags.yml -c /path/to/azure.yml --interval 5 --loglevel INFO
```

## Development
### Run locally in simulation mode
```
> uv run python -m ruuvigate -r ./resources/ruuvitags.yml --mode stdout --interval 5 --loglevel INFO --simulate
```

### Run unit tests
```
> uv run pytest
```

## Typing
Check typing
```
> uv run mypy .
```

### Formatting
Check formatting
```
> uv run yapf --diff --recursive .
```
Apply formatting
```
> uv run yapf -i --recursive .
```
