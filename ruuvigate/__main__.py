import sys
import os
import argparse
import yaml
import logging
import asyncio
import re
from enum import Enum
from random import randint

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


class MethodNames(Enum):
    AddRuuvitag = "RuuviGate_250*AddRuuviTag"


async def add_ruuvitag(data):
    # https://stackoverflow.com/a/7629690
    if not re.match("[0-9a-f]{2}([-:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", data.lower()):
        return {"result": False, "data": "Not a valid MAC address"}
    print("Adding RuuviTag "+data)
    return {"result": True, "data": "RuuviTag " + data + " added"}


async def provision_iotc_device(args, azure_config):
    logging.info("Provisioning new Azure IoT Central device..")
    device_host = await AzureClient.provision_device(azure_config[AzureParams.ProvisioningHost.value],
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


async def get_azure_client(args):
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
        azure_config = await provision_iotc_device(args, azure_config)

    # Connect to Azure IoT Central
    azureClient = AzureClient()
    try:
        await azureClient.connect(azure_config[AzureParams.DeviceKey.value],
                                  azure_config[AzureParams.DeviceID.value],
                                  azure_config[AzureParams.DeviceHostName.value])
    except ConnectionError:
        sys.exit(os.EX_UNAVAILABLE)

    return azureClient


async def get_ruuvi_data(args, client, macs):
    if args.simulate:
        data = {}
        for mac in macs.keys():
            ran = randint(-1, 1)
            data[mac] = {
                "temperature": 15+3*ran,
                "humidity": 50+5*ran,
                "pressure": 950+20*ran,
                "battery": 3000+5*ran,
                "measurement_sequence_number": 1234+2*ran
            }
        await asyncio.sleep(args.interval)
        return data
    else:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, RuuviTagSensor.get_data_for_sensors, macs.keys(), args.interval)


async def main(args, client, ruuvi_macs):
    try:
        asyncio.create_task(client.execute_method_listener(
            MethodNames.AddRuuvitag.value, add_ruuvitag))
        while True:
            task = asyncio.create_task(
                get_ruuvi_data(args, client, ruuvi_macs))
            datas = await task
            if datas:
                if args.mode == 'stdout':
                    print(datas)
                else:
                    for mac, data in datas.items():
                        if mac in ruuvi_macs:
                            # Match data to DTDL telemetry attribute names
                            await client.buffer_data(
                                {TelemNames.Temperature.value+str(ruuvi_macs[mac]): data["temperature"],
                                 TelemNames.Humidity.value+str(ruuvi_macs[mac]): data["humidity"],
                                 TelemNames.Pressure.value+str(ruuvi_macs[mac]): data["pressure"],
                                 TelemNames.Battery.value+str(ruuvi_macs[mac]): data["battery"],
                                 TelemNames.Sequence.value+str(ruuvi_macs[mac]): data["measurement_sequence_number"]}
                            )
                        else:
                            logging.warning(
                                "Received data from an unknown RuuviTag: " + mac)
                    await client.send_data()
            else:
                logging.warning(
                    "Could not read any RuuviTag data. Please make sure that the specified RuuviTags are within range.")
    except KeyboardInterrupt:
        logging.info("Exiting")
    finally:
        if not args.simulate:
            await client.shutdown()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--mode', dest='mode',
                        choices=['azure', 'stdout'], default='azure',
                        help='Data output destination')
    parser.add_argument('-r', '--ruuvimacs', dest='ruuvi_macs',
                        help='RuuviTag MAC address specification file path', required=True)
    parser.add_argument('-a', '--azureconfs', dest='azure_confs',
                        help='Azure configurations', required=True)
    parser.add_argument('-i', '--interval', dest='interval',
                        help='Interval (seconds) on which RuuviTag data is fetched and send', default=60, type=int)
    parser.add_argument('-l', '--loglevel', dest='log_level',
                        help='Python logger log level',
                        choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'NOTSET'], default="WARNING")
    parser.add_argument('--simulate', action='store_true',
                        help='Use simulated RuuviTag measurements', default=False)

    args = parser.parse_args()

    logging.basicConfig(level=args.log_level)
    ruuvi_macs = parse_ruuvi_macs(args)

    if args.mode == "azure":
        client = asyncio.run(get_azure_client(args))
    else:
        client = None

    asyncio.run(main(args, client, ruuvi_macs))
