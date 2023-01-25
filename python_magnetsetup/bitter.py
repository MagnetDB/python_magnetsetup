from typing import List, Optional

import yaml

from python_magnetgeo import Bitter
from python_magnetgeo import python_magnetgeo

from .jsonmodel import create_params_bitter, create_bcs_bitter, create_materials_bitter, create_models_bitter
from .utils import Merge, NMerge

import os

from .file_utils import MyOpen, findfile, search_paths

def Bitter_simfile(MyEnv, confdata: dict, cad: Bitter, debug: bool=False):
    print(f"Bitter_simfile: cad={cad.name}")

    from .file_utils import MyOpen, findfile

    yamlfile = confdata["geom"]
    with MyOpen(yamlfile, 'r', paths=search_paths(MyEnv, "geom")) as cfgdata:
        return cfgdata

def Bitter_setup(MyEnv, mname: str, confdata: dict, cad: Bitter, method_data: List, templates: dict, debug: bool=False):
    print(f'Bitter_setup: magnet={mname}, cad={cad.name}') #, "debug=", debug, "confdata:", confdata)
    if debug:
        print(f'Bitter_setup/Bitter confdata: {confdata}')

    part_thermic = []
    part_electric = []
    index_Bitters = ""

    boundary_meca = []
    boundary_maxwell = []
    boundary_electric = []

    yamlfile = confdata["geom"]
    if debug: 
        print(f'Bitter_setup/Bitter yamlfile: {yamlfile}')

    NSections = len(cad.axi.turns)
    if debug:
        print(f"cad: {cad} tpe: {type(cad)}")

    snames = []
    name = f"{mname}_{cad.name}" #.replace('Bitter_','')
    if method_data[2] == "Axi":
        for i in range(len(cad.axi.turns)):
            snames.append(f"{name}_B{i+1}")
            part_electric.append(snames[-1])
            if 'th' in method_data[3]:
                part_thermic.append(snames[-1])
        index_Bitters = f"1:{NSections+1}"
        if debug: print("sname:", snames)
    else:
        part_electric.append(cad.name)
        if 'th' in method_data[3]:
            part_thermic.append(cad.name)

    gdata = (name, snames, cad.axi.turns)

    if debug:
        print("bitter part_thermic:", part_thermic)
        print("bitter part_electric:", part_electric)
        
    if  method_data[2] == "Axi" and ('el' in method_data[3] and  method_data[3] != 'thelec'):
        boundary_meca.append("{}_V0".format(name))
        boundary_meca.append("{}_V1".format(name))    
                
        boundary_maxwell.append("ZAxis")
        boundary_maxwell.append("Infty")
    
    # params section
    params_data = create_params_bitter(mname, gdata, method_data, debug)

    # bcs section
    bcs_data = create_bcs_bitter(boundary_meca, 
                          boundary_maxwell,
                          boundary_electric,
                          gdata, confdata, templates, method_data, debug) # merge all bcs dict

    # build dict from geom for templates
    # TODO fix initfile name (see create_cfg for the name of output / see directory entry)
    # eg: $home/feel[ppdb]/$directory/cfpdes-heat.save

    main_data = {
        "part_thermic": part_thermic,
        "part_electric": part_electric,
        "index_V0": boundary_electric,
        "temperature_initfile": "tini.h5",
        "V_initfile": "Vini.h5"
    }
    mdict = NMerge( NMerge(main_data, params_data), bcs_data, debug, "bitter_setup mdict")

    print("bitter_setup: post-processing section")
    currentH_data = []
    powerH_data = []
    meanT_data = []
    Stress_data = []
    VonMises_data = []

    from .units import load_units, convert_data
    unit_Length = method_data[5] # "meter"
    units = load_units(unit_Length)
    plotB_data = { "Rinf": convert_data(units, cad.r[-1], "Length"), "Zinf": convert_data(units, cad.z[-1], "Length")}
    
    if method_data[2] == "Axi":
        currentH_data.append( {"part_electric": part_electric } )
        powerH_data.append( {"header": f"Power_{name}", "markers": { "name": f"{name}_B%1%", "index1": index_Bitters}} )
        meanT_data.append( {"header": f"T_{name}", "markers":  { "name": f"{name}_B%1%", "index1": index_Bitters}} )
        Stress_data.append( {"header": f"Stress_{name}", "markers":  { "name": f"{name}_B%1%", "index1": index_Bitters}} )
        VonMises_data.append( {"header": f"VonMises_{name}", "markers":  { "name": f"{name}_B%1%", "index1": index_Bitters}} )

    else:
        print("bitter3D post not implemented")
        
    mpost = {
        "Power": powerH_data ,
        "Current": currentH_data,
        "Flux": {},
        "T" : meanT_data,
        "Stress": Stress_data,
        "VonMises": VonMises_data,
    }

    if 'mag' in method_data[3] or 'mqs' in method_data[3]:
        mpost["B"] = plotB_data

    # check mpost output
    # print(f"bitter {name}: mpost={mpost}")
    mmat = create_materials_bitter(gdata, confdata, templates, method_data, debug)
    
    mmodels = {}
    if 'th' in method_data[3]:
        mmodels["heat"] = create_models_bitter(gdata, confdata, templates, method_data, "heat", debug)

    if 'mag' in method_data[3] or 'mqs' in method_data[3] :
        mmodels["magnetic"] = create_models_bitter(gdata, confdata, templates, method_data, "magnetic", debug)
    
    if 'magel' in method_data[3] :
        mmodels["elastic"] = create_models_bitter(gdata, confdata, templates, method_data, "elastic", debug)

    if 'mqsel' in method_data[3] :
        mmodels["elastic1"] = create_models_bitter(gdata, confdata, templates, method_data, "elastic1", debug)
        mmodels["elastic2"] = create_models_bitter(gdata, confdata, templates, method_data, "elastic2", debug)

    # update U and hw, dTw param
    print("Update U for I0=31kA")
    # print(f"insert: mmat: {mmat}")
    # print(f"insert: mdict['Parameters']: {mdict['Parameters']}")
    I0 = 31.e+3
    if method_data[2] == "Axi":
        import math
        params = params_data['Parameters']
        print('params:', params)
        for key in params:
            print(f"{key}")
        for j in range(len(cad.axi.turns)):
            marker = f"{name}_B{j+1}"
            # print("marker:", marker)
            item = {"name": f"U_{marker}", "value":"1"}
            index = params.index(item)
            mat = mmat[marker]
            # print("U=", params[index], mat['sigma'], R1[i], pitch_h[i][j])
            if method_data[6]:
                sigma = float(mat['sigma0'])
            else:
                sigma = float(mat['sigma'])
            I_s = I0 * cad.axi.turns[j]
            j1 = I_s / (math.log(cad.r[1]/cad.r[0]) * (cad.r[0]*1.e-3) * (cad.axi.pitch[j]*1.e-3) * cad.axi.turns[j] )
            U_s = 2 * math.pi * (cad.r[0] * 1.e-3) * j1 / sigma
            # print("U=", params[index]['name'], cad.r[0], cad.axi.pitch[j], mat['sigma'], "U_s=", U_s, "j1=", j1)
            item = {"name": f"U_{marker}", "value":str(U_s)}
            params[index] = item
                
    
    return (mdict, mmat, mmodels, mpost)
