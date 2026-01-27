from .logging_config import get_logger

logger = get_logger(__name__)


def entry_cfg(template: str, rdata: dict, debug: bool = False) -> str:
    import chevron

    logger.debug("entry/loading %s" % str(template))
    logger.debug("entry/rdata:", rdata)
    with open(template, "r") as f:
        jsonfile = chevron.render(f, rdata)
    jsonfile = jsonfile.replace("'", '"')
    return jsonfile


def create_cfg(
    cfgfile: str,
    name: str,
    mesh: str,
    nonlinear: bool,
    jsonfile: str,
    template: str,
    method_data: list[str],
    debug: bool = False,
):
    """
    Create a cfg file
    """
    print(f"create_cfg {cfgfile} from {template}")
    print(f"create_cfg: {jsonfile}")

    dim = 2
    if method_data[2] == "3D":
        dim = 3

    linear = "linear"
    if nonlinear:
        linear = "nonlinear"

    data = {
        "dim": dim,
        "method": method_data[0],
        "model": method_data[3],
        "geom": method_data[2],
        "time": method_data[1],
        "linear": linear,
        "name": name,
        "jsonfile": jsonfile,
        "mesh": mesh,
        "scale": 0.001,
        "partition": 1,
    }

    mdata = entry_cfg(template, data, debug)
    logger.debug(f"create_cfg/mdata={mdata}")

    with open(cfgfile, "w+") as out:
        out.write(mdata)

    pass
