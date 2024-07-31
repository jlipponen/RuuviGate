from typing import Dict


class StdOut:

    def __init__(self):
        self._dataBuf: Dict[str, str] = {}

    async def connect(self, _):
        """
        Dummy implementation for abstract connect method.

        Args:
            _: Placeholder argument.

        Returns:
            None
        """
        pass

    async def publish_data(self, data: Dict[str, str] = {}):
        """
        Publishes stored and provided data to the standard output.

        Args:
            data (dict): The data to be published. Defaults to an empty dictionary.

        Returns:
            None
        """
        self._dataBuf.update(data)
        print(self._dataBuf)
        self._dataBuf.clear()

    async def buffer_data(self, data: Dict[str, str]):
        """
        Buffer the provided data into the internal data buffer.

        Args:
            data (Dict[str, str]): The data to be buffered.

        Returns:
            None
        """
        self._dataBuf.update(data)
