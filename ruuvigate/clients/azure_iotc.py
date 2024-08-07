import atexit
import os
import json
import uuid
import logging
import asyncio
import yaml
from enum import Enum
from typing import Any, Callable

# Type information will be there, eventually: https://github.com/Azure/azure-iot-sdk-python/pull/1163
from azure.iot.device.aio import IoTHubDeviceClient  # type: ignore
from azure.iot.device.aio import ProvisioningDeviceClient  # type: ignore
from azure.iot.device import MethodResponse  # type: ignore
from azure.iot.device import Message  # type: ignore


class AzureIOTC:
    '''
    Class to provide device connectivity to an Azure IoT Central application with
    Azure IoT SDK (https://github.com/Azure/azure-iot-sdk-python)
    '''
    MethodNames = {
        "AddRuuviTag": "RuuviGate_250*AddRuuviTag",
        "RemoveRuuviTag": "RuuviGate_250*RemoveRuuviTag",
        "GetRuuviTags": "RuuviGate_250*GetRuuviTags"
    }

    class AzureParams(Enum):
        DeviceKey = "IOTHUB_DEVICE_DPS_DEVICE_KEY"
        DeviceID = "IOTHUB_DEVICE_DPS_DEVICE_ID"
        DeviceIDScope = "IOTHUB_DEVICE_DPS_ID_SCOPE"
        ProvisioningHost = "IOTHUB_DEVICE_DPS_ENDPOINT"
        ModelID = "IOTHUB_DEVICE_DPS_MODEL_ID"

    class Message(Enum):
        Encoding = "utf8"
        ContentType = "application/json"

    def __init__(self):
        self._client = None
        self._databuf = {}
        atexit.register(self.disconnect)

    def __connected(func: Callable) -> Any:  # type: ignore

        def wrapper(self, *args, **kwargs):
            assert self._client is not None, "AzureIOTC not connected"
            return func(self, *args, **kwargs)

        return wrapper

    async def connect(self, config_path: str):
        config = self.__parse_config(config_path)

        # Provision the device
        device_host = await self.__provision_device(
            config[self.AzureParams.ProvisioningHost.value],
            config[self.AzureParams.DeviceIDScope.value],
            config[self.AzureParams.DeviceID.value],
            config[self.AzureParams.DeviceKey.value],
            config[self.AzureParams.ModelID.value])

        logging.info("Got device hostname: " + device_host)

        # Open the connection
        try:
            self._client = IoTHubDeviceClient.create_from_symmetric_key(
                symmetric_key=config[self.AzureParams.DeviceKey.value],
                hostname=device_host,
                device_id=config[self.AzureParams.DeviceID.value],
            )
            await self._client.connect()
        except Exception as ex:
            logging.error("Unable to connect to Azure: {} {}".format(
                type(ex).__name__, ex.args))
            self._client = None
            raise ConnectionError()

    async def disconnect(self):
        if self._client != None:
            logging.info("Disconnecting AzureIOTC")
            await self._client.shutdown()
            self._client = None

    @__connected
    async def execute_method_listener(self, method_name, handler, cookie):
        logging.info("Executing a listener for \"" + method_name + "\" method")
        while True:
            try:
                method_request = await self._client.receive_method_request(
                    self.MethodNames.get(method_name))
                logging.info("Received method request \"" + method_name + "\"")

                response_payload = await handler(method_request.payload,
                                                 cookie)
                response_status = 200 if response_payload.get(
                    "result") else 400

                command_response = MethodResponse.create_from_method_request(
                    method_request, response_status, response_payload)
                try:
                    await self._client.send_method_response(command_response)
                except RuntimeError:
                    logging.error(
                        "Responding to command request \"{}\" failed".format(
                            method_name))
            except asyncio.CancelledError:
                logging.info("Exiting \"" + method_name + "\" listener")
                break

    @__connected
    async def publish_data(self, data={}):
        """
            param data: dictionary of values to send
        """
        self._databuf.update(data)

        msg = Message(json.dumps(self._databuf))
        msg.content_encoding = AzureIOTC.Message.Encoding.value
        msg.content_type = AzureIOTC.Message.ContentType.value
        msg.message_id = uuid.uuid4()

        await self._client.send_message(msg)
        logging.info("Sent message " + str(msg) + " with id " +
                     str(msg.message_id))

        self._databuf.clear()

    async def buffer_data(self, data={}):
        self._databuf.update(data)

    @staticmethod
    def __parse_config(config_path: str):
        if not os.path.exists(config_path):
            logging.error("Can't find file: " + config_path)
            raise FileNotFoundError(config_path)

        with open(config_path, "r") as stream:
            try:
                config = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                logging.error(exc)
                raise exc

        # Check that all needed configurations exist
        for param in AzureIOTC.AzureParams:
            if param.value not in config:
                logging.error("Configuration error! Missing configuration: " +
                              param.value)
                raise ValueError("Missing configuration")

        return config

    @staticmethod
    async def __provision_device(provisioning_host, id_scope, registration_id,
                                 symmetric_key, model_id):
        provisioning_device_client = ProvisioningDeviceClient.create_from_symmetric_key(
            provisioning_host=provisioning_host,
            registration_id=registration_id,
            id_scope=id_scope,
            symmetric_key=symmetric_key,
        )

        provisioning_device_client.provisioning_payload = {"modelId": model_id}
        registration_result = await provisioning_device_client.register()

        if registration_result.status == "assigned":
            logging.info("Device was assigned")
            logging.info(registration_result.registration_state.assigned_hub)
            logging.info(registration_result.registration_state.device_id)
        else:
            raise RuntimeError("Could not provision device.")

        return registration_result.registration_state.assigned_hub
