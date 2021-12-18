import sys
import os
import argparse
import yaml
import logging
from enum import Enum

from ruuvitag_sensor.ruuvi import RuuviTagSensor

from .azure_client import AzureClient


class AzureParams(Enum):
    DeviceKey = "IOTHUB_DEVICE_DPS_DEVICE_KEY"
    DeviceID = "IOTHUB_DEVICE_DPS_DEVICE_ID"
    DeviceIDScope = "IOTHUB_DEVICE_DPS_ID_SCOPE"
    DeviceHostName = "IOTHUB_DEVICE_DPS_HOSTNAME"
    ProvisioningHost = "IOTHUB_DEVICE_DPS_ENDPOINT"
    ModelID = "IOTHUB_DEVICE_DPS_MODEL_ID"


class TelemNames(Enum):
    Temperature = "Temperature"
    Humidity = "Humidity"
    Pressure = "Pressure"
    Battery = "Battery"
    Sequence = "Sequence"
    MAC = "MAC"


def provision(args, azure_config):
    logging.info("Provisioning new IoT Central device..")
    device_host = AzureClient.provision_device(azure_config[AzureParams.ProvisioningHost.value],
                                               azure_config[AzureParams.DeviceIDScope.value],
                                               azure_config[AzureParams.DeviceID.value],
                                               azure_config[AzureParams.DeviceKey.value],
                                               azure_config[AzureParams.ModelID.value])
    logging.info("Got device hostname: " + device_host +
                 "\nStoring it to the given Azure configuration file..")

    with open(args.azure_confs, "a") as stream:
        try:
            stream.write("\n"+AzureParams.DeviceHostName.value +
                         ":"+" \""+device_host+"\"")
        except yaml.YAMLError as exc:
            print(exc)
            sys.exit(os.EX_OSFILE)

    # Add it to the parsed Azure configuration as well
    azure_config[AzureParams.DeviceHostName.value] = device_host
    return azure_config


def parse_configurations(args):
    with open(args.azure_confs, "r") as stream:
        try:
            azure_config = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            sys.exit(os.EX_OSFILE)

    # Check that all needed Azure configurations exist
    for param in AzureParams:
        if param.value == AzureParams.DeviceHostName.value and args.provision:
            if param.value in azure_config:
                logging.error(
                    "Azure configuration error! Device host already specified. Sure you need to provision the device? "
                    "If so, delete the existing entry.")
                sys.exit(os.EX_USAGE)
            continue
        if param.value not in azure_config:
            logging.error(
                "Azure configuration error! Missing Azure configuration: " + param.value)
            sys.exit(os.EX_USAGE)

    with open(args.ruuvi_macs, "r") as stream:
        try:
            ruuvi_macs = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            sys.exit(os.EX_OSFILE)

    return azure_config, ruuvi_macs


def main(args, azure_config, ruuvi_macs):
    azureClient = AzureClient()
    try:
        azureClient.connect(azure_config[AzureParams.DeviceKey.value],
                            azure_config[AzureParams.DeviceID.value],
                            azure_config[AzureParams.DeviceHostName.value])
    except ConnectionError:
        sys.exit(os.EX_UNAVAILABLE)

    try:
        while True:
            datas = RuuviTagSensor.get_data_for_sensors(
                ruuvi_macs.keys(), args.interval)
            if datas:
                for mac, data in datas.items():
                    if mac in ruuvi_macs:
                        azureClient.buffer_data(
                            {TelemNames.Temperature.value+str(ruuvi_macs[mac]): data["temperature"],
                             TelemNames.Humidity.value+str(ruuvi_macs[mac]): data["humidity"],
                             TelemNames.Pressure.value+str(ruuvi_macs[mac]): data["pressure"],
                             TelemNames.Battery.value+str(ruuvi_macs[mac]): data["battery"],
                             TelemNames.Sequence.value+str(ruuvi_macs[mac]): data["measurement_sequence_number"]}
                        )
                    else:
                        logging.warn(
                            "Received data from an unknown RuuviTag: " + mac)
                azureClient.send_data()
            else:
                logging.warn(
                    "Could not read any RuuviTag data. Please make sure that the specified RuuviTags are within range.")
    except KeyboardInterrupt:
        logging.info("Exiting")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--ruuvimacs', dest='ruuvi_macs',
                        help='RuuviTag MAC address specification file path', required=True)
    parser.add_argument('-a', '--azureconfs', dest='azure_confs',
                        help='Azure configurations', required=True)
    parser.add_argument('-i', '--interval', dest='interval',
                        help='Interval (seconds) on which RuuviTag data is fetched and send to Azure', default=60, type=int)
    parser.add_argument('-l', '--loglevel', dest='log_level',
                        help='Python logger log level', default="WARN")
    parser.add_argument('--provision', action='store_true',
                        help='Provision current device to Azure IoT Central')
    parser.set_defaults(provision=False)
    args = parser.parse_args()
    logging.basicConfig(level=args.log_level)

    azure_config, ruuvi_macs = parse_configurations(args)

    if args.provision:
        azure_config = provision(args, azure_config)

    main(args, azure_config, ruuvi_macs)
