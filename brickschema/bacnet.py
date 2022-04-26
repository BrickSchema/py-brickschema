from .graph import Graph
from .namespaces import BRICK, A, REF, BACNET
from rdflib import Namespace, Literal
import BAC0
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO)
logging.getLogger("BAC0_Root.BAC0").propagate = False
logging.getLogger("BAC0_Root.BAC0").setLevel(logging.WARNING)

NET = Namespace("urn:bacnet-scan/")


def clean_name(name):
    return name.replace(" ", "_").replace("-", "_").replace(".", "_").replace("/", "_")


# TODO: provide namespace for graph
def scan(ns: Namespace = NET, ip: Optional[str] = None) -> Graph:
    """
    Scan for BACnet devices on the provided network. If no network is provided,
    use the default scan logic which scans all available interfaces. Provide a
    network by indicating the IP address that BAC0 should bind to

    The Optional 'ns' parameter provides a namespace for the graph containing
    the scanned results.
    """
    graph = Graph()

    # ping=False avoids spamming messages on the network
    client = BAC0.connect(ip=ip, ping=False)
    client.discover()
    for dev in client.devices:
        print(dev)
        name, _, address, deviceid = dev
        name = clean_name(name)
        graph.add((ns[name], A, BACNET.BACnetDevice))
        graph.add((ns[name], BACNET["device-instance"], Literal(deviceid)))
        graph.add((ns[name], BACNET["hasAddress"], Literal(address)))

        logging.info(f"Scanning BACnet device {dev}")
        device = BAC0.device(
            dev[2], dev[3], client, history_size=0, segmentation_supported=False
        )
        for point in device.points:
            print(point)
            objectIdent = point.properties.address
            objectIRI = ns[name + "/" + str(objectIdent)]
            graph.add((objectIRI, A, BRICK.Point))
            props = [
                (A, REF.BACnetReference),
                (BACNET["object-identifier"], Literal(int(objectIdent))),
                (BACNET["objectOf"], ns[name]),
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
