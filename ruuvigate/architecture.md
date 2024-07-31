```mermaid
---
title: RuuviGate
---
classDiagram

    class DataPublisher {
        <<protocol>>
       +connect(config)*
       +publish_data(data)*
       +buffer_data(data)*
       +execute_method_listener(method_name, handler, cookie)*
    }

    class DataPublisherFactory {
        <<dataclass>>
        +DataPublisher publisher
        +__call__() DataPublisher()
    }

    class AzureIOTC {
        -IoTHubDeviceClient _client
        -Dict~str, str~ _databuf
        +connect(data)
        +disconnect()
        +publish_data(data)
        +buffer_data(data)
        +execute_method_listener(method_name, handler, cookie)
        -parse_config()$
        -provision_device()$
    }

    class StdOut {
        +connect(data)
        +publish_data(data)
        +buffer_data(data)
        +execute_method_listener(method_name, handler, cookie)
    }

    class RuuviTags {
        -str _macs_file
        -List~str~ _macs
        +add_mac(mac)
        +remove_mac(mac)
        +get_macs()
        +is_legal_mac(mac)$
        -parse_ruuvitag_file()
        -write_macs_to_ruuvitag_file

    }

    DataPublisher <|-- DataPublisherFactory : create
    DataPublisher <|-- AzureIOTC : adheres
    DataPublisher <|-- StdOut : adheres
```
