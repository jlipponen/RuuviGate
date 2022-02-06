import sys
import os
import argparse
import yaml
import logging
from enum import Enum

from ruuvitag_sensor.ruuvi import RuuviTagSensor

from azure_client import AzureClient


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


def provision_iotc_device(args, azure_config):
    logging.info("Provisioning new Azure IoT Central device..")
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

def parse_ruuvi_macs(args):
    with open(args.ruuvi_macs, "r") as stream:
        try:
            ruuvi_macs = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            sys.exit(os.EX_OSFILE)

    return ruuvi_macs

def get_azure_client(args):
    with open(args.azure_confs, "r") as stream:
            try:
                azure_config = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)
                sys.exit(os.EX_OSFILE)

    # Check that all needed Azure configurations exist
    for param in AzureParams:
        if param.value != AzureParams.DeviceHostName.value and param.value not in azure_config:
            logging.error(
                "Azure configuration error! Missing Azure configuration: " + param.value)
            sys.exit(os.EX_USAGE)

    # Provision a new device if needed
    if AzureParams.DeviceHostName.value not in azure_config:
        azure_config = provision_iotc_device(args, azure_config)

    # Connect to Azure IoT Central
    azureClient = AzureClient()
    try:
        azureClient.connect(azure_config[AzureParams.DeviceKey.value],
                            azure_config[AzureParams.DeviceID.value],
                            azure_config[AzureParams.DeviceHostName.value])
    except ConnectionError:
        sys.exit(os.EX_UNAVAILABLE)

    return azureClient

def main(args, client, ruuvi_macs):
    try:
        while True:
            datas = RuuviTagSensor.get_data_for_sensors(
                ruuvi_macs.keys(), args.interval)
            if datas:
                for mac, data in datas.items():
                    if mac in ruuvi_macs:
                        client.buffer_data(
                            {TelemNames.Temperature.value+str(ruuvi_macs[mac]): data["temperature"],
                             TelemNames.Humidity.value+str(ruuvi_macs[mac]): data["humidity"],
                             TelemNames.Pressure.value+str(ruuvi_macs[mac]): data["pressure"],
                             TelemNames.Battery.value+str(ruuvi_macs[mac]): data["battery"],
                             TelemNames.Sequence.value+str(ruuvi_macs[mac]): data["measurement_sequence_number"]}
                        )
                    else:
                        logging.warning(
                            "Received data from an unknown RuuviTag: " + mac)
                client.send_data()
            else:
                logging.warning(
                    "Could not read any RuuviTag data. Please make sure that the specified RuuviTags are within range.")
    except KeyboardInterrupt:
        logging.info("Exiting")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--mode', dest='mode', choices=['azure'], default='azure')
    parser.add_argument('-r', '--ruuvimacs', dest='ruuvi_macs',
                        help='RuuviTag MAC address specification file path', required=True)
    parser.add_argument('-a', '--azureconfs', dest='azure_confs',
                        help='Azure configurations', required=True)
    parser.add_argument('-i', '--interval', dest='interval',
                        help='Interval (seconds) on which RuuviTag data is fetched and send to Azure', default=60, type=int)
    parser.add_argument('-l', '--loglevel', dest='log_level',
                        help='Python logger log level', default="WARN")

    args = parser.parse_args()

    logging.basicConfig(level=args.log_level)
    ruuvi_macs = parse_ruuvi_macs(args)

    if args.mode == "azure":
        client = get_azure_client(args)

    main(args, client, ruuvi_macs)
