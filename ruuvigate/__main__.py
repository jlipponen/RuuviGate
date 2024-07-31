import sys
import os
import argparse
import logging
import asyncio
import re
import signal
import functools
from random import randint
from typing import List

from ruuvitag_sensor.ruuvi import RuuviTagSensor  # type: ignore

from ruuvigate.clients.client import FACTORIES, Connectable, DataPublisher


class RuuviTags:
    lock = asyncio.Lock()

    def __init__(self, path):
        self._macs_file: str = path
        self._macs: List[str] = []

        if not os.path.exists(self._macs_file):
            open(self._macs_file, "x")
        else:
            self.__parse_ruuvitag_file()

    async def add_mac(self, mac: str) -> bool:
        async with self.lock:
            if self._macs.count(mac) != 0:
                return False
            if not self.is_legal_mac(mac):
                raise ValueError("Malformed MAC: {}".format(mac))
            self._macs.append(mac)
        await self.__write_macs_to_ruuvitag_file()
        return True

    async def remove_mac(self, mac: str) -> bool:
        async with self.lock:
            if self._macs.count(mac) == 0:
                return False
            self._macs.remove(mac)
        await self.__write_macs_to_ruuvitag_file()
        return True

    async def get_macs(self) -> List[str]:
        async with self.lock:
            return self._macs

    def __parse_ruuvitag_file(self) -> None:
        with open(self._macs_file, "r") as f:
            lines = f.read().splitlines()
        for line in lines:
            if not line:
                continue
            if not self.is_legal_mac(line):
                raise ValueError(
                    "Malformed line in RuuviTags file: {}".format(line))
            self._macs.append(line)

    async def __write_macs_to_ruuvitag_file(self) -> None:
        async with self.lock:
            with open(self._macs_file, "w") as stream:
                for mac in self._macs:
                    stream.write(mac + '\n')

    @staticmethod
    def is_legal_mac(mac: str) -> bool:
        # https://stackoverflow.com/a/7629690
        return re.match("[0-9a-f]{2}([-:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$",
                        mac.lower())


async def add_ruuvitag(mac, ruuvitags):
    if mac is None:
        return {"result": False, "data": "Cannot add empty MAC"}

    if not RuuviTags.is_legal_mac(mac):
        logging.warning("Got illegal RuuviTag MAC " + mac)
        return {"result": False, "data": "Not a valid MAC address"}
    logging.info("Adding RuuviTag " + mac)
    ret = await ruuvitags.add_mac(mac)
    if ret:
        return {"result": True, "data": "RuuviTag " + mac + " added"}
    else:
        return {"result": False, "data": "RuuviTag " + mac + " already exists"}


async def remove_ruuvitag(mac, ruuvitags):
    if mac is None:
        return {"result": False, "data": "Cannot add empty MAC"}

    if not RuuviTags.is_legal_mac(mac):
        logging.warning("Got illegal RuuviTag MAC " + mac)
        return {"result": False, "data": "Not a valid MAC address"}
    logging.info("Removing RuuviTag " + mac)
    ret = await ruuvitags.remove_mac(mac)
    if ret:
        return {"result": True, "data": "RuuviTag " + mac + " removed"}
    else:
        return {"result": False, "data": "RuuviTag " + mac + " doesn't exist"}


async def get_ruuvitags(data, ruuvitags):
    logging.info("Returning RuuviTags")
    macs = await ruuvitags.get_macs()
    return {"result": True, "data": macs}


async def get_ruuvi_data(args, ruuvitags: List[str]):
    if args.simulate:
        data = {}
        for tag in ruuvitags:
            ran = randint(-1, 1)
            data[tag] = {
                "temperature": 15 + 3.2 * ran,
                "humidity": 50 + 5.7 * ran,
                "pressure": 950 + 20.5 * ran,
                "battery": 3000 + 5 * ran,
                "measurement_sequence_number": 1234 + 2 * ran
            }
        await asyncio.sleep(args.interval)
    else:
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None,
                                          RuuviTagSensor.get_data_for_sensors,
                                          ruuvitags, args.interval)
    return data


async def send_ruuvi_data(publisher: DataPublisher, ruuvitags, data):
    for mac, data in data.items():
        await publisher.buffer_data({
            "Temperature" + str(ruuvitags.index(mac) + 1):
            data["temperature"],
            "Humidity" + str(ruuvitags.index(mac) + 1):
            data["humidity"],
            "Pressure" + str(ruuvitags.index(mac) + 1):
            data["pressure"],
            "Battery" + str(ruuvitags.index(mac) + 1):
            data["battery"],
            "Sequence" + str(ruuvitags.index(mac) + 1):
            data["measurement_sequence_number"]
        })
    await publisher.publish_data()


async def publish_ruuvi_data(args, publisher: DataPublisher,
                             ruuvitags: RuuviTags):
    while True:
        try:
            macs = await ruuvitags.get_macs()
            if macs:
                data = await get_ruuvi_data(args, macs)
                if data:
                    await send_ruuvi_data(publisher, macs, data)
                else:
                    logging.warning(
                        "Could not read any RuuviTag data. Please make sure that the specified RuuviTags are within range."
                    )
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


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-m',
        '--mode',
        dest='mode',
        type=str,
        default='azure',
        choices=['azure', 'stdout'],
        help='RuuviTag measurements output destination (default: %(default)s)')
    parser.add_argument('-r',
                        '--ruuvitags',
                        dest='ruuvitags',
                        required=True,
                        type=argparse.FileType('r'),
                        help='Path to RuuviTag specification file')
    parser.add_argument('-c',
                        '--config',
                        dest='config',
                        default=None,
                        help='Path to cloud client configuration file')
    parser.add_argument(
        '-i',
        '--interval',
        dest='interval',
        type=int,
        default=60,
        help=
        'Interval (seconds) in which RuuviTag data is polled and published (default: %(default)s)'
    )
    parser.add_argument(
        '-l',
        '--loglevel',
        dest='log_level',
        type=str,
        default="WARNING",
        choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'NOTSET'],
        help='Python logger log level (default: %(default)s)')
    parser.add_argument('--simulate',
                        action='store_true',
                        default=False,
                        help='Use simulated RuuviTag measurements')

    args = parser.parse_args()

    def report_and_exit(err_msg: str, exit_code):
        logging.error(err_msg)
        parser.print_help(sys.stderr)
        sys.exit(exit_code)

    if args.mode == "stdout":
        if args.config is not None:
            logging.warning("Configuration file ignored in 'stdout' mode")
    else:
        if args.config is None:
            report_and_exit(
                "Configuration file needed when not using 'stdout' mode!",
                os.EX_USAGE)
        if not os.path.exists(args.config):
            report_and_exit(
                "Given configuration doesn't exist! ({})".format(args.config),
                os.EX_NOINPUT)

    if args.interval < 1:
        report_and_exit("Interval must be greater than zero", os.EX_DATAERR)

    return args


async def main(args, tags: RuuviTags, client: Connectable):
    try:
        await client.connect(args.config)
    except ConnectionError:
        sys.exit(os.EX_UNAVAILABLE)

    listeners = []
    if args.mode == "azure":
        listeners = [
            asyncio.create_task(
                client.execute_method_listener("AddRuuviTag", add_ruuvitag,
                                               tags))
        ]
        listeners.append(
            asyncio.create_task(
                client.execute_method_listener("RemoveRuuviTag",
                                               remove_ruuvitag, tags)))
        listeners.append(
            asyncio.create_task(
                client.execute_method_listener("GetRuuviTags", get_ruuvitags,
                                               tags)))

    tasks = listeners + [
        asyncio.create_task(publish_ruuvi_data(args, client, tags))
    ]
    loop = asyncio.get_event_loop()

    # Signals to initiate a graceful shutdown
    for signame in {'SIGINT', 'SIGTERM'}:
        loop.add_signal_handler(
            getattr(signal, signame),
            functools.partial(cancel_tasks, signame, *tasks))

    await asyncio.gather(*tasks)


if __name__ == '__main__':
    assert sys.version_info >= (3, 10), "Python 3.10 or greater required"
    args = parse_args()
    logging.basicConfig(level=args.log_level)
    tags = RuuviTags(args.ruuvitags.name)
    client = FACTORIES[args.mode]()
    asyncio.run(main(args, tags, client))
    logging.info("RuuviGate was shutdown")
