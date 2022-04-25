from .graph import Graph
from .namespaces import BRICK, A, REF, BACNET
from rdflib import Namespace, Literal
import BAC0
import logging

logging.basicConfig(level=logging.INFO)
logging.getLogger("BAC0_Root.BAC0").propagate = False
logging.getLogger("BAC0_Root.BAC0").setLevel(logging.WARNING)


def clean_name(name):
    return name.replace(" ", "_").replace("-", "_").replace(".", "_").replace("/", "_")


def scan() -> Graph:
    """
    Scan for BACnet devices on the provided network
    """
    NET = Namespace("urn:bacnet-scan/")
    graph = Graph()

    # ping=False avoids spamming messages on the network
    client = BAC0.connect(ping=False)
    client.discover()
    for dev in client.devices:
        print(dev)
        name, _, address, deviceid = dev
        name = clean_name(name)
        graph.add((NET[name], A, BACNET.BACnetDevice))
        graph.add((NET[name], BACNET["device-instance"], Literal(deviceid)))
        graph.add((NET[name], BACNET["hasAddress"], Literal(address)))

        logging.info(f"Scanning BACnet device {dev}")
        device = BAC0.device(
            dev[2], dev[3], client, history_size=0, segmentation_supported=False
        )
        for point in device.points:
            print(point)
            objectIdent = point.properties.address
            objectIRI = NET[name + "/" + str(objectIdent)]
            graph.add((objectIRI, A, BRICK.Point))
            props = [
                (A, REF.BACnetReference),
                (BACNET["object-identifier"], Literal(int(objectIdent))),
                (BACNET["objectOf"], NET[name]),
            ]
            props.append(
                (BACNET["object-name"], Literal(point.properties.name.strip()))
            )
            props.append(
                (
                    BACNET["object-description"],
                    Literal(point.properties.description.strip()),
                )
            )
            props.append((BACNET["object-type"], Literal(point.properties.type)))
            props.append((BACNET["units"], Literal(point.properties.units_state)))
            graph.add((objectIRI, REF.hasExternalReference, props))

    return graph
