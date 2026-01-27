import os
import json
import enum
from dataclasses import dataclass, field

from .job import JobManager, JobManagerType
from .logging_config import get_logger

logger = get_logger(__name__)


class NodeType(str, enum.Enum):
    compute = "compute"
    visu = "visu"


@dataclass
class NodeSpec:
    name: str
    dns: str
    otype: NodeType = NodeType.compute
    smp: bool = True
    manager: JobManager = field(default_factory=lambda: JobManager())
    cores: int = 2
    multithreading: bool = True
    mgkeydir: str = r"/opt/MeshGems"


def load_machines(debug: bool = False):
    """
    load machines definition as a dict
    """
    logger.debug("load machines")
    logger.debug("load_machines")

    default_path = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(default_path, "machines.json"), "r") as cfg:
        logger.debug("load_machines from: %s", cfg.name)
        data = json.load(cfg)
        logger.debug("data=%s", data)

    machines = {}
    for item, value in data.items():
        logger.debug("server: %s type=%s", item, value["type"])
        server = NodeSpec(
            name=item,
            otype=NodeType[value["type"]],
            smp=value["smp"],
            dns=value["dns"],
            cores=value["cores"],
            multithreading=value["multithreading"],
            manager=JobManager(
                otype=JobManagerType[value["jobmanager"]["type"]],
                queues=value["jobmanager"]["queues"],
            ),
            mgkeydir=value["mgkeydir"],
        )
        machines[item] = server

    return machines


def loadmachines(server: str):
    """
    Load app server config (aka machines.json)
    """

    server_defs = load_machines()
    if server in server_defs:
        return server_defs[server]
    else:
        raise ValueError(f"loadmachine: {server} no such server defined")
    pass
