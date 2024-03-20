import sys
import os
import json
import yaml

from .config import appenv

def load_object(appenv: appenv, datafile: str, debug: bool = False):
    """
    Load object props
    """

    if appenv.yaml_repo:
        print("Look for %s in %s" % (datafile, appenv.yaml_repo))
    else:
        print("Look for %s in workingdir %s" % (datafile, os.getcwd()))

    with open(datafile, 'r') as cfgdata:
            confdata = json.load(cfgdata)
    return confdata


