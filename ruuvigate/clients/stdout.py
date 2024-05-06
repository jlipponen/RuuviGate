from typing import Dict


class StdOut:
    def __init__(self):
        self._dataBuf: Dict[str, str] = {}

    async def connect(self, _):
        pass

    async def publish_data(self, data={}):
        self._dataBuf.update(data)
        print(self._dataBuf)
        self._dataBuf.clear()

    async def buffer_data(self, data: Dict[str, str]):
        self._dataBuf.update(data)
