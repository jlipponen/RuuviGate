from abc import abstractmethod
from typing import Protocol, Type
from dataclasses import dataclass

from .azure_iotc import AzureIOTC
from .stdout import StdOut


class DataPublisher(Protocol):

    @abstractmethod
    async def publish_data(self, data={}):
        ...

    @abstractmethod
    async def buffer_data(self, data):
        ...

    @abstractmethod
    async def connect(self, config):
        ...

    @abstractmethod
    async def execute_method_listener(self, method_name, handler, cookie):
        ...


@dataclass
class ConnectableFactory:
    con_class: Type[DataPublisher]

    def __call__(self) -> DataPublisher:
        return self.con_class()


FACTORIES = {
    "azure": ConnectableFactory(AzureIOTC),
    "stdout": ConnectableFactory(StdOut),
}
