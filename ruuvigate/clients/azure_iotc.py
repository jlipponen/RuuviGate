import json
import uuid
import logging
import asyncio
from enum import Enum

from azure.iot.device.aio import IoTHubDeviceClient
from azure.iot.device.aio import ProvisioningDeviceClient
from azure.iot.device import MethodResponse
from azure.iot.device import Message


class AzureIOTC:
    '''
    Class to provide device connectivity to an Azure IoT Central application with
    Azure IoT SDK (https://github.com/Azure/azure-iot-sdk-python)
    '''
    class Message(Enum):
        Encoding = "utf8"
        ContentType = "application/json"

    def __init__(self):
        self.client_ = None
        self.dataBuf_ = {}

    def __connected(func):
        def wrapper(self, *args, **kwargs):
            assert self.client_ != None, "AzureIOTC not connected"
            return func(self, *args, **kwargs)
        return wrapper

    async def connect(self, device_key: str, device_id: str, iotcentral_hostname: str):
        try:
            self.client_ = IoTHubDeviceClient.create_from_symmetric_key(
                symmetric_key=device_key,
                hostname=iotcentral_hostname,
                device_id=device_id,
            )
            await self.client_.connect()
        except Exception as ex:
            logging.error(
                "Unable to connect to Azure: {} {}".format(
                    type(ex).__name__, ex.args)
            )
            self.client_ = None
            raise ConnectionError()

    async def disconnect(self):
        if self.client_ != None:
            logging.info("Disconnecting AzureIOTC")
            await self.client_.shutdown()
            self.client_ = None

    @__connected
    async def execute_method_listener(self, method_name, handler, cookie):
        logging.info("Executing a listener for \"" + method_name + "\" method")
        while True:
            try:
                method_request = await self.client_.receive_method_request(method_name)
                logging.info("Received method request \"" + method_name + "\"")

                response_payload = await handler(method_request.payload, cookie)
                if response_payload.get("result"):
                    response_status = 200
                else:
                    response_status = 400

                command_response = MethodResponse.create_from_method_request(
                    method_request, response_status, response_payload
                )
                try:
                    await self.client_.send_method_response(command_response)
                except RuntimeError:
                    logging.error(
                        "Responding to command request \"{}\" failed".format(method_name))
            except asyncio.CancelledError:
                logging.info("Exiting \"" + method_name + "\" listener")
                break

    @__connected
    async def send_data(self, data={}):
        """
            param data: dictionary of values to send
        """
        self.dataBuf_.update(data)

        msg = Message(json.dumps(self.dataBuf_))
        msg.content_encoding = AzureIOTC.Message.Encoding.value
        msg.content_type = AzureIOTC.Message.ContentType.value
        msg.message_id = uuid.uuid4()

        await self.client_.send_message(msg)
        logging.info("Sent message " + str(msg) +
                     " with id " + str(msg.message_id))

        self.dataBuf_.clear()

    async def buffer_data(self, data):
        self.dataBuf_.update(data)

    @staticmethod
    async def provision_device(provisioning_host, id_scope, registration_id, symmetric_key, model_id):
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
            raise RuntimeError(
                "Could not provision device."
            )

        return registration_result.registration_state.assigned_hub
