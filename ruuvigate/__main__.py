import sys
import os
import argparse
import yaml
import logging
import asyncio
import re
import signal
import functools
from enum import Enum
from random import randint

from ruuvitag_sensor.ruuvi import RuuviTagSensor

from azure_client import AzureClient

lock = asyncio.Lock()


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


class RuuviTags:
    def __init__(self, path):
        self.macs_file_ = path

        if not os.path.exists(self.macs_file_):
            with open(self.macs_file_, "x"):
                pass

        self.macs_ = []

    def parse_macs(self):
        with open(self.macs_file_, "r") as f:
            self.macs_ = f.read().splitlines()

    def add_mac(self, mac):
        if self.macs_.count(mac) != 0:
            return False
        with open(self.macs_file_, "a") as stream:
            stream.write(mac+'\n')
        self.parse_macs()
        return True

    def remove_mac(self, mac):
        if self.macs_.count(mac) == 0:
            return False
        with open(self.macs_file_, "r+") as stream:
            new_f = stream.readlines()
            stream.seek(0)
            for line in new_f:
                if mac not in line:
                    stream.write(line)
            stream.truncate()
        self.parse_macs()
        return True

    def get_macs(self):
        return self.macs_


async def add_ruuvitag(data, ruuvitags):
    # https://stackoverflow.com/a/7629690
    if not re.match("[0-9a-f]{2}([-:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", data.lower()):
        logging.warning("Got illegal RuuviTag MAC "+data)
        return {"result": False, "data": "Not a valid MAC address"}
    logging.info("Adding RuuviTag "+data)
    async with lock:
        ruuvitags.add_mac(data)
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
        stream.write("\n"+AzureParams.DeviceHostName.value +
                     ":"+" \""+device_host+"\"")

    # Add it to the parsed Azure configuration as well
    azure_config[AzureParams.DeviceHostName.value] = device_host
    return azure_config


async def get_azure_client(args):
    with open(args.azure_confs, "r") as stream:
        try:
            azure_config = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            logging.error(exc)
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


async def get_ruuvi_data(args, ruuvitags):
    if args.simulate:
        data = {}
        for tag in ruuvitags:
            ran = randint(-1, 1)
            data[tag] = {
                "temperature": 15+3*ran,
                "humidity": 50+5*ran,
                "pressure": 950+20*ran,
                "battery": 3000+5*ran,
                "measurement_sequence_number": 1234+2*ran
            }
        await asyncio.sleep(args.interval)
    else:
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None, RuuviTagSensor.get_data_for_sensors, ruuvitags, args.interval)
    return data


async def send_ruuvi_data(client, ruuvitags, data):
    for mac, data in data.items():
        # Match data to DTDL telemetry attribute names
        await client.buffer_data(
            {TelemNames.Temperature.value+str(ruuvitags.index(mac)+1): data["temperature"],
                TelemNames.Humidity.value+str(ruuvitags.index(mac)+1): data["humidity"],
                TelemNames.Pressure.value+str(ruuvitags.index(mac)+1): data["pressure"],
                TelemNames.Battery.value+str(ruuvitags.index(mac)+1): data["battery"],
                TelemNames.Sequence.value+str(ruuvitags.index(mac)+1): data["measurement_sequence_number"]}
        )
    await client.send_data()


async def publish_ruuvi_data(args, client, ruuvitags):
    while True:
        try:
            async with lock:
                macs = ruuvitags.get_macs()
            if macs:
                data = await get_ruuvi_data(args, macs)
                if data:
                    if args.mode == 'stdout':
                        print(data)
                    else:
                        await send_ruuvi_data(client, macs, data)
                else:
                    logging.warning(
                        "Could not read any RuuviTag data. Please make sure that the specified RuuviTags are within range.")
            else:
                logging.info("No RuuviTags specified.")
                await asyncio.sleep(args.interval)
        except asyncio.CancelledError:
            break


def cancel_tasks(signal, *tasks):
    logging.info("Received signal {}. Cancelling tasks..".format(signal))
    for task in tasks:
        task.cancel()


async def dummy_task():
    await asyncio.sleep(1)


async def main(args, client, ruuvitags):
    if client:
        t1 = asyncio.create_task(client.execute_method_listener(
            MethodNames.AddRuuvitag.value, add_ruuvitag, ruuvitags))
    else:
        t1 = asyncio.create_task(dummy_task())
    t2 = asyncio.create_task(publish_ruuvi_data(args, client, ruuvitags))

    loop = asyncio.get_event_loop()

    # Signals to initiate a graceful shutdown
    for signame in {'SIGINT', 'SIGTERM', 'SIGHUP'}:
        loop.add_signal_handler(
            getattr(signal, signame),
            functools.partial(cancel_tasks, signame, t1, t2))

    await asyncio.gather(t1, t2)

if __name__ == '__main__':
    import sys
    assert sys.version_info >= (3, 7), "Python 3.7+ required"

    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--mode', dest='mode',
                        choices=['azure', 'stdout'], default='azure',
                        help='Data output destination')
    parser.add_argument('-r', '--ruuvitags', dest='ruuvitags',
                        help='RuuviTags (MACs) specification file path', required=True)
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
    tags = RuuviTags(args.ruuvitags)
    tags.parse_macs()

    if args.mode == "azure":
        client = asyncio.run(get_azure_client(args))
    else:
        client = None

    asyncio.run(main(args, client, tags))
    logging.info("RuuviGate was shutdown")
