import json
import uuid
import logging
from enum import Enum

from azure.iot.device.aio import IoTHubDeviceClient
from azure.iot.device.aio import ProvisioningDeviceClient
from azure.iot.device import MethodResponse
from azure.iot.device import Message


class AzureClient:
    class Message(Enum):
        Encoding = "utf8"
        ContentType = "application/json"

    def __init__(self):
        self.client_ = None
        self.dataBuf_ = {}

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
                "Unable to connect to Azure! {}: {}".format(
                    type(ex).__name__, ex.args)
            )
            self.client_ = None
            raise ConnectionError()

    async def execute_method_listener(self, method_name, handler):
        logging.info("Executing a listener for \"" + method_name + "\" method")
        while True:
            method_request = await self.client_.receive_method_request(method_name)
            logging.info("Method request \"" + method_name +
                         "\" received with payload:\n"+method_request.payload)

            response_payload = await handler(method_request.payload)
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
                print("Responding to command request \"{}\" failed".format(method_name))

    async def send_data(self, data={}):
        """
            param data: dictionary of values to send
        """
        self.dataBuf_.update(data)

        msg = Message(json.dumps(self.dataBuf_))
        msg.content_encoding = AzureClient.Message.Encoding.value
        msg.content_type = AzureClient.Message.ContentType.value
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
