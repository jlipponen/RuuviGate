from abc import abstractmethod
from typing import Protocol, Type
from dataclasses import dataclass

from .azure_iotc import AzureIOTC
from .stdout import StdOut


class Connectable(Protocol):

    @abstractmethod
    async def connect(self, config):
        ...


class DataPublisher(Protocol):

    @abstractmethod
    async def publish_data(self, data):
        ...

    @abstractmethod
    async def buffer_data(self, data):
        ...


@dataclass
class ConnectableFactory:
    con_class: Type[Connectable]

    def __call__(self) -> Connectable:
        return self.con_class()


FACTORIES = {
    "azure": ConnectableFactory(AzureIOTC),
    "stdout": ConnectableFactory(StdOut),
}
