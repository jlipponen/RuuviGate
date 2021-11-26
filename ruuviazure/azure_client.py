from azure.iot.device import IoTHubDeviceClient
from azure.iot.device import ProvisioningDeviceClient
from azure.iot.device import Message
from enum import Enum
import json
import uuid
import logging


class AzureClient:
    class Message(Enum):
        Encoding = "utf8"
        ContentType = "application/json"

    def __init__(self):
        self.client_ = None
        self.dataBuf_ = {}

    def __del__(self):
        if self.client_ != None:
            self.client_.shutdown()
            self.client_ = None

    def connect(self, device_key: str, device_id: str, iotcentral_hostname: str):
        try:
            self.client_ = IoTHubDeviceClient.create_from_symmetric_key(
                symmetric_key=device_key,
                hostname=iotcentral_hostname,
                device_id=device_id,
            )
            self.client_.connect()
        except Exception:
            logging.error(
                "Unable to connect to Azure. Please check the coenction parameters." +
                " Is this device provisioned to Azure IoT Central?")
            self.client_ = None
            raise ConnectionError()

    def send_data(self, data = {}):
        """
            param data: dictionary of values to send
        """
        self.dataBuf_.update(data)

        msg = Message(json.dumps(self.dataBuf_))
        msg.content_encoding = AzureClient.Message.Encoding.value
        msg.content_type = AzureClient.Message.ContentType.value
        msg.message_id = uuid.uuid4()
        
        self.client_.send_message(msg)
        logging.info("Sent message " + str(data) +
                     " with id " + str(msg.message_id))

    def buffer_data(self, data):
        self.dataBuf_.update(data)

    @staticmethod
    def provision_device(provisioning_host, id_scope, registration_id, symmetric_key, model_id):
        provisioning_device_client = ProvisioningDeviceClient.create_from_symmetric_key(
            provisioning_host=provisioning_host,
            registration_id=registration_id,
            id_scope=id_scope,
            symmetric_key=symmetric_key,
        )

        provisioning_device_client.provisioning_payload = {"modelId": model_id}
        registration_result = provisioning_device_client.register()

        if registration_result.status == "assigned":
            logging.info("Device was assigned")
            logging.info(registration_result.registration_state.assigned_hub)
            logging.info(registration_result.registration_state.device_id)
        else:
            raise RuntimeError(
                "Could not provision device."
            )

        return registration_result.registration_state.assigned_hub
