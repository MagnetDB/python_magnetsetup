from typing import List, Optional

import sys
import os
import json
class appenv():
    
    def __init__(self, debug: bool = False):
        self.url_api: str = None
        self.yaml_repo: Optional[str] = None
        self.mesh_repo: Optional[str] = None
        self.template_repo: Optional[str] = None
        self.simage_repo: Optional[str] = None

        from decouple import Config, RepositoryEnv
        envdata = RepositoryEnv("settings.env")
        data = Config(envdata)
        if debug:
            print("appenv:", RepositoryEnv("settings.env").data)

        self.url_api = data.get('URL_API')
        if 'TEMPLATE_REPO' in envdata:
            self.template_repo = data.get('TEMPLATE_REPO')
        if 'SIMAGE_REPO' in envdata:
            self.simage_repo = data.get('SIMAGE_REPO')

    def template_path(self, debug: bool = False):
        """
        returns template_repo
        """
        if not self.template_repo:
            default_path = os.path.dirname(os.path.abspath(__file__))
            repo = os.path.join(default_path, "templates")
        else:
            repo = self.template_repo

        if debug:
            print("appenv/template_path:", repo)
        return repo

    def simage_path(self, debug: bool = False):
        """
        returns simage_repo
        """
        if not self.simage_repo:
            repo = os.path.join("/home/singularity")
        else:
            repo = self.simage_repo

        if debug:
            print("appenv/simage_path:", repo)
        return repo


def loadconfig():
    """
    Load app config (aka magnetsetup.json)
    """

    default_path = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(default_path, 'magnetsetup.json'), 'r') as appcfg:
        magnetsetup = json.load(appcfg)
    return magnetsetup

def loadtemplates(appenv: appenv, appcfg: dict , method_data: List[str], linear: bool=True, debug: bool=False):
    """
    Load templates into a dict

    method_data:
    method
    time
    geom
    model
    cooling

    """
    
    [method, time, geom, model, cooling, units_def] = method_data
    template_path = os.path.join(appenv.template_path(), method, geom, model)

    cfg_model = appcfg[method][time][geom][model]["cfg"]
    json_model = appcfg[method][time][geom][model]["model"]
    if linear:
        conductor_model = appcfg[method][time][geom][model]["conductor-linear"]
    else:
        if geom == "3D": 
            json_model = appcfg[method][time][geom][model]["model-nonlinear"]
        conductor_model = appcfg[method][time][geom][model]["conductor-nonlinear"]
    insulator_model = appcfg[method][time][geom][model]["insulator"]
    
    fcfg = os.path.join(template_path, cfg_model)
    if debug:
        print("fcfg:", fcfg, type(fcfg))
    fmodel = os.path.join(template_path, json_model)
    fconductor = os.path.join(template_path, conductor_model)
    finsulator = os.path.join(template_path, insulator_model)
    if model != 'mag':
        cooling_model = appcfg[method][time][geom][model]["cooling"][cooling]
        flux_model = appcfg[method][time][geom][model]["cooling-post"][cooling]
        stats_T_model = appcfg[method][time][geom][model]["stats_T"]
        stats_Power_model = appcfg[method][time][geom][model]["stats_Power"]

        fcooling = os.path.join(template_path, cooling_model)
        if debug:
            print("fcooling:", fcooling, type(fcooling))
        fflux = os.path.join(template_path, flux_model)
        fstats_T = os.path.join(template_path, stats_T_model)
        fstats_Power = os.path.join(template_path, stats_Power_model)

    material_generic_def = ["conductor", "insulator"]
    if time == "transient":
        material_generic_def.append("conductor-nosource") # only for transient with mqs

    dict = {
        "cfg": fcfg,
        "model": fmodel,
        "conductor": fconductor,
        "insulator": finsulator,
        "cooling": fcooling,
        "flux": fflux,
        "stats": [fstats_T, fstats_Power],
        "material_def" : material_generic_def
    }

    if check_templates(dict):
        pass

    return dict    

def check_templates(templates: dict):
    """
    check if template file exist
    """
    print("\n\n=== Checking Templates ===")
    for key in templates:
        if isinstance(templates[key], str):
            print(key, templates[key])
            with open(templates[key], "r") as f: pass

        elif isinstance(templates[key], str):
            for s in templates[key]:
                print(key, s)
                with open(s, "r") as f: pass
    print("==========================\n\n")
    
    return True
