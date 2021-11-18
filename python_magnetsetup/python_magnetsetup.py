"""
Create template json model files for Feelpp/HiFiMagnet simu
From a yaml definition file of an insert
Inputs:
* method : method of solve, with feelpp cfpdes, getdp...
* time: stationnary or transient case
* geom: geometry of solve, 3D or Axi
* model: physic solved, thermic, thermomagnetism, thermomagnetism-elastic
* phytype: if the materials are linear or non-linear
* cooling: what type of cooling, mean or grad
Output: 
* tmp.json
App setup is stored in a json file that defines
the mustache template to be used.
Default path:
magnetsetup.json
mustache templates
"""

# TODO check for unit consistency
# depending on Length base unit

import sys
import os
import requests
import requests.exceptions
import ast
import pandas as pd

import math

import yaml
from python_magnetgeo import Helix
from python_magnetgeo import Ring
from python_magnetgeo import InnerCurrentLead
from python_magnetgeo import OuterCurrentLead
from python_magnetgeo import Insert
from python_magnetgeo import python_magnetgeo #import get_main_characteristics

import chevron
import json

import argparse
import pathlib

#import numpy as np 
import warnings
from pint import UnitRegistry, Unit, Quantity

# Ignore warning for pint
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    Quantity([])

# Pint configuration
ureg = UnitRegistry()
ureg.default_system = 'SI'
ureg.autoconvert_offset_to_baseunit = True

# Global variables
url_api = 'http://localhost:8000/api'

def Merge(dict1, dict2):
    """
    Merge dict1 and dict2 to form a new dictionnary
    """
    res = {**dict1, **dict2}
    return res

def convert_data(distance_unit, confdata, R1, R2, Z1, Z2, Zmin, Zmax, Dh, Sh, h, mu0):
    """Return the dictionnary confdata_convert and distances : R1, R2,
        Z1, Z2, Zmin, Zmax, Dh and Sh with values converted on distance
        unit : distance_unit.
        
        input:
            - distance_unit (str)
            - confdata (dict)
            - R1, R2, Z1, Z2, Zmin, Zmax, Dh, Sh (float)
        
        return:
            - confdata_convert (dict)
            - R1_convert, R2_convert, Z1_convert, Z2_convert, Zmin_convert, Zmax_convert, Dh_convert, Sh_convert (float)
    """
    
    # Convert
    confdata_convert = confdata.copy()

    for mtype in ["Helix", "Ring", "Lead"]:
        for i in range(len(confdata_convert[mtype])):
            
            # ThermalConductivity : W/m/K --> W/distance_unit/K
            confdata_convert[mtype][i]["material"]["ThermalConductivity"] = Quantity( confdata_convert[mtype][i]["material"]["ThermalConductivity"], ureg.watt / ureg.meter / ureg.kelvin ).to( ureg.watt / ureg.Unit(distance_unit) / ureg.kelvin ).magnitude
            
            # Young : kg/m/s --> kg/distance_unit/s
            confdata_convert[mtype][i]["material"]["Young"] = Quantity( confdata_convert[mtype][i]["material"]["Young"], ureg.kilogram / ureg.meter / ureg.second ).to( ureg.kilogram / ureg.Unit(distance_unit) / ureg.second ).magnitude
            
            # VolumicMass : kg/m3 --> kg/distance_unit**3
            confdata_convert[mtype][i]["material"]["VolumicMass"] = Quantity( confdata_convert[mtype][i]["material"]["VolumicMass"], ureg.kilogram / ureg.meter**3 ).to( ureg.kilogram / ureg.Unit(distance_unit)**3 ).magnitude
            
            # ElectricalConductivity : S/m --> S/distance_unit
            confdata_convert[mtype][i]["material"]["ElectricalConductivity"] = Quantity( confdata_convert[mtype][i]["material"]["ElectricalConductivity"], ureg.siemens / ureg.meter ).to( ureg.siemens / ureg.Unit(distance_unit) ).magnitude

            # Rpe : kg/m/s --> kg/distance_unit/s
            confdata_convert[mtype][i]["material"]["Rpe"] = Quantity( confdata_convert[mtype][i]["material"]["Rpe"], ureg.kilogram / ureg.meter / ureg.second ).to( ureg.kilogram / ureg.Unit(distance_unit) / ureg.second ).magnitude

    # mm -> distance_unit
    R1_convert   = Quantity( R1, ureg.millimeter ).to( ureg.Unit(distance_unit) ).magnitude.tolist()
    R2_convert   = Quantity( R2, ureg.millimeter ).to( ureg.Unit(distance_unit) ).magnitude.tolist()
    Z1_convert   = Quantity( Z1, ureg.millimeter ).to( ureg.Unit(distance_unit) ).magnitude.tolist()
    Z2_convert   = Quantity( Z2, ureg.millimeter ).to( ureg.Unit(distance_unit) ).magnitude.tolist()
    Zmin_convert = Quantity( Zmin, ureg.millimeter ).to( ureg.Unit(distance_unit) ).magnitude.tolist()
    Zmax_convert = Quantity( Zmax, ureg.millimeter ).to( ureg.Unit(distance_unit) ).magnitude.tolist()
    Dh_convert   = Quantity( Dh, ureg.millimeter ).to( ureg.Unit(distance_unit) ).magnitude.tolist()
    Sh_convert   = Quantity( Sh, ureg.millimeter ).to( ureg.Unit(distance_unit) ).magnitude.tolist()
    
    # MagnetPermeability of vacuum : H/m --> H/distance_unit
    mu0_convert = Quantity( mu0, ureg.henry / ureg.meter ).to( ureg.henry / ureg.Unit(distance_unit) ).magnitude

    # Convection coefficients : W/m2/K --> W/distance_unit**2/K
    h_convert = Quantity( h, ureg.watt / ureg.meter**2 / ureg.kelvin ).to( ureg.watt / ureg.Unit(distance_unit)**2 / ureg.kelvin ).magnitude

    return confdata_convert, R1_convert, R2_convert, Z1_convert, Z2_convert, Zmin_convert, Zmax_convert, Dh_convert, Sh_convert, h_convert, mu0_convert

def create_indices(NHelices, Nsections):
    """Create indices of Markers :
    return :
        index_H (list)                  : list of indices of all sections of Helices
        index_conductor (list)          : list of indices of all Conductor sections of Helices
        index_Helices   (list)          : list of range of sections of Helices
        index_HelicesConductor (list)   : list of range of Conductor sections of Helices
    """

    index_H = []
    index_conductor = []
    index_Helices = []
    index_HelicesConductor = []

    for i in range(NHelices):
        for j in range(Nsections[i]+2):
            index_H.append( [str(i+1),str(j)] )
        for j in range(Nsections[i]):
            index_conductor.append( [str(i+1),str(j+1)] )
        index_Helices.append(["0:{}".format(Nsections[i]+2)])
        index_HelicesConductor.append(["1:{}".format(Nsections[i]+1)])
    
    return index_H, index_conductor, index_Helices, index_HelicesConductor

def create_part_withoutAir(args, NHelices, Nsections, NRings):
    "Return all Markers name except the Air"

    part_withoutAir = []  # list of name of all parts without Air

    if args.geom == '3D':
        for i in range(NHelices):
            part_withoutAir.append("H{}_Cu".format(i+1))
        for i in range(1,NRings+1):
            part_withoutAir.append("R{}".format(i))
        part_withoutAir.append('iL1')
        part_withoutAir.append('oL2')

    elif args.geom == 'Axi':
        for i in range(NHelices):
            for j in range(Nsections[i]+2):
                part_withoutAir.append("H{}_Cu{}".format(i+1,j))
        for i in range(1,NRings+1):
            part_withoutAir.append("R{}".format(i))
    
    return part_withoutAir

def create_boundary_Ring(NRings):
    "Return all Markers name of elastic boundaries"

    boundary_Ring = [ "H1_HP", "H_HP" ] # list of name of boundaries of Ring for elastic part
    for i in range(1,NRings+1):
        if i % 2 == 1 :
            boundary_Ring.append("R{}_BP".format(i))
        else :
            boundary_Ring.append("R{}_HP".format(i))
    
    return boundary_Ring

def create_boundary_withoutV(NHelices, NRings, NChannels):
    "Return all boundar's markers except the markers of tension"

    boundary_withoutV = []

    for i in range(NHelices):
        boundary_withoutV.append("H{}_Interface0".format(i+1))
        boundary_withoutV.append("H{}_Interface1".format(i+1))

    for i in range(NRings):
        if i % 2 == 0 : boundary_withoutV.append("R{}_HP".format(i+1))
        if i % 2 == 1 : boundary_withoutV.append("R{}_BP".format(i+1))

    for i in range(NChannels):
        boundary_withoutV.append("Channel{}".format(i))

    boundary_withoutV.append("Inner1_R0n")
    boundary_withoutV.append("Inner1_R1n")
    boundary_withoutV.append("Inner1_FixingHoles")
    boundary_withoutV.append("OuterL2_R0n")
    boundary_withoutV.append("OuterL2_R1n")
    boundary_withoutV.append("OuterL2_CooledSurfaces")
    boundary_withoutV.append("OuterL2_Others")

    return boundary_withoutV

def create_boundary_withoutChannels(NHelices, NRings):
    "Return all boundar's markers except the markers of Channels"

    boundary_withoutChannels = []

    for i in range(NHelices):
        boundary_withoutChannels.append("H{}_Interface0".format(i+1))
        boundary_withoutChannels.append("H{}_Interface1".format(i+1))

    for i in range(NRings):
        if i % 2 == 0 : boundary_withoutChannels.append("R{}_HP".format(i+1))
        if i % 2 == 1 : boundary_withoutChannels.append("R{}_BP".format(i+1))

    boundary_withoutChannels.append("Inner1_R0n")
    boundary_withoutChannels.append("Inner1_R1n")
    boundary_withoutChannels.append("Inner1_LV0")
    boundary_withoutChannels.append("Inner1_FixingHoles")
    boundary_withoutChannels.append("OuterL2_R0n")
    boundary_withoutChannels.append("OuterL2_R1n")
    boundary_withoutChannels.append("OuterL2_LV0")
    boundary_withoutChannels.append("OuterL2_CooledSurfaces")
    boundary_withoutChannels.append("OuterL2_Others")

    return boundary_withoutChannels

def create_params_dict(args, Zmin, Zmax, Sh, Dh, Tinit, Tin, h, Tw, dTw, mu0, NHelices, Nsections):
    """
    Return params_dict, the dictionnary of section \"Parameters\" for JSON file.
    """

    # Tini, Aini for transient cases??
    params_dict = {}

    # for cfpdes only
    if args.method == "cfpdes":
        params_dict["bool_laplace"] = "1"
        params_dict["bool_dilatation"] = "1"

    # TODO : initialization of parameters
    params_dict["mu0"] = mu0
    params_dict["Tinit"] = Tinit
    params_dict["Tin"] = Tin

    # params per cooling channels
    # h%d, Tw%d, dTw%d, Dh%d, Sh%d, Zmin%d, Zmax%d :

    for i in range(NHelices+1):
        params_dict["h%d" % i] = h[i]
        params_dict["Tw%d" % i] = Tw[i]
        params_dict["dTw%d" % i] = dTw[i]
        params_dict["Zmin%d" % i] = Zmin[i]
        params_dict["Zmax%d" % i] = Zmax[i]
        params_dict["Sh%d" % i] = Sh[i]
        params_dict["Dh%d" % i] = Dh[i]

    # init values for U (Axi specific)
    if args.geom == "Axi":
        for i in range(NHelices):
            for j in range(Nsections[i]):
                params_dict["U_H%d_Cu%d" % (i+1, j+1)] = "1"

    return params_dict

def create_materials_cfpdes(args, cwd, magnetsetup, template_path, confdata, finsulator, fconductor, fconductorbis, NHelices, Nsections, NRings):
    """
    Return materials_dict, the dictionnary of section \"Materials\" for JSON file for cfpdes method.
    """

    # copy json files to cwd (only for cfpdes)
    material_generic_def = ["conductor", "insulator"]

    if args.time == "transient":
        material_generic_def.append("conductor-nosource") # only for transient with mqs

    from shutil import copyfile
    for jsonfile in material_generic_def:
        filename = magnetsetup[args.method][args.time][args.geom][args.model]["filename"][jsonfile]
        src = os.path.join(template_path, filename)
        dst = os.path.join(cwd, jsonfile + ".json")
        #print(jsonfile, "filename=", filename, src, dst)
        copyfile(src, dst)

    # TODO loop for Plateau (Axi specific)

    materials_dict = {}

    for i in range(NHelices):
        
        # section j==0:  treated as conductor without current in Axi
        with open(fconductorbis, "r") as ftemplate:
            jsonfile = chevron.render(ftemplate, Merge({'name': "H%d_Cu%d" % (i+1, 0)}, confdata["Helix"][i]["material"]))
            jsonfile = jsonfile.replace("\'", "\"")
            # shall get rid of comments: //*
            mdata = json.loads(jsonfile)
            materials_dict["H%d_Cu%d" % (i+1, 0)] = mdata["H%d_Cu%d" % (i+1, 0)]
        
        # load conductor template
        for j in range(1,Nsections[i]+1):
            with open(fconductor, "r") as ftemplate:
                jsonfile = chevron.render(ftemplate, Merge({'name': "H%d_Cu%d" % (i+1, j)}, confdata["Helix"][i]["material"]))
                jsonfile = jsonfile.replace("\'", "\"")
                # shall get rid of comments: //*
                mdata = json.loads(jsonfile)
                materials_dict["H%d_Cu%d" % (i+1, j)] = mdata["H%d_Cu%d" % (i+1, j)]

        # section j==Nsections+1:  treated as conductor without current in Axi
        with open(fconductorbis, "r") as ftemplate:
            jsonfile = chevron.render(ftemplate, Merge({'name': "H%d_Cu%d" % (i+1, Nsections[i]+1)}, confdata["Helix"][i]["material"]))
            jsonfile = jsonfile.replace("\'", "\"")
            # shall get rid of comments: //*
            mdata = json.loads(jsonfile)
            materials_dict["H%d_Cu%d" % (i+1, Nsections[i]+1)] = mdata["H%d_Cu%d" % (i+1, Nsections[i]+1)]

        # loop for Rings:  treated as insulator in Axi
        for i in range(NRings):
            with open(finsulator, "r") as ftemplate:
                jsonfile = chevron.render(ftemplate, Merge({'name': "R%d" % (i+1)}, confdata["Ring"][i]["material"]))
                jsonfile = jsonfile.replace("\'", "\"")
                # shall get rid of comments: //*
                mdata = json.loads(jsonfile)
                materials_dict["R%d" % (i+1)] = mdata["R%d" % (i+1)]
        
        # Leads: treated as insulator in Axi
        # inner
        '''
        with open(finsulator, "r") as ftemplate:
            jsonfile = chevron.render(ftemplate, Merge({'name': "iL1"}, confdata["Lead"][0]["material"]))
            jsonfile = jsonfile.replace("\'", "\"")
            # shall get rid of comments: //*
            mdata = json.loads(jsonfile)
            materials_dict["iL1"] = mdata["iL1"]
        # outer
        with open(finsulator, "r") as ftemplate:
            jsonfile = chevron.render(ftemplate, Merge({'name': "oL2"}, confdata["Lead"][1]["material"]))
            jsonfile = jsonfile.replace("\'", "\"")
            # shall get rid of comments: //*
            mdata = json.loads(jsonfile)
            materials_dict["oL2"] = mdata["oL2"]
        '''

    return materials_dict

def create_materials_hdg_cg(confdata, finsulator, fconductor, NHelices, NRings):
    """
    Return materials_dict, the dictionnary of section \"Materials\" for JSON file for HDG method.
    """

    materials_dict = {}

    # loop for Helices
    for i in range(NHelices):
        with open(fconductor, "r") as ftemplate:
            jsonfile = chevron.render(ftemplate, Merge({'name': "H%d_Cu" % (i+1)}, confdata["Helix"][i]["material"]))
            jsonfile = jsonfile.replace("\'", "\"")
            # shall get rid of comments: //*
            mdata = json.loads(jsonfile)
            materials_dict["H%d_Cu" % (i+1)] = mdata["H%d_Cu" % (i+1)]

    # loop for Rings
    for i in range(NRings):
        with open(fconductor, "r") as ftemplate:
            jsonfile = chevron.render(ftemplate, Merge({'name': "R%d" % (i+1)}, confdata["Ring"][i]["material"]))
            jsonfile = jsonfile.replace("\'", "\"")
            # shall get rid of comments: //*
            mdata = json.loads(jsonfile)
            materials_dict["R%d" % (i+1)] = mdata["R%d" % (i+1)]

    # Leads
    # inner
    with open(fconductor, "r") as ftemplate:
        jsonfile = chevron.render(ftemplate, Merge({'name': "iL1"}, confdata["Lead"][0]["material"]))
        jsonfile = jsonfile.replace("\'", "\"")
        # shall get rid of comments: //*
        mdata = json.loads(jsonfile)
        materials_dict["iL1"] = mdata["iL1"]

    # outer
    with open(fconductor, "r") as ftemplate:
        jsonfile = chevron.render(ftemplate, Merge({'name': "oL2"}, confdata["Lead"][1]["material"]))
        jsonfile = jsonfile.replace("\'", "\"")
        # shall get rid of comments: //*
        mdata = json.loads(jsonfile)
        materials_dict["oL2"] = mdata["oL2"]

    return materials_dict

def create_bcsFlux_dict(NChannels, fcooling):
    """
    Return bcs_dict, the dictionnary of section \"BoundaryConditions\" for JSON file especially for cooling.
    """

    bcs_dict = {}

    for i in range(NChannels):
        # load insulator template for j==0
        with open(fcooling, "r") as ftemplate:
            jsonfile = chevron.render(ftemplate, {'i': i})
            jsonfile = jsonfile.replace("\'", "\"")
            # shall get rid of comments: //*
            mdata = json.loads(jsonfile)
            bcs_dict["Channel%d" % i] = mdata["Channel%d" % i]

    return bcs_dict

def main():

    # Manage Options
    command_line = None
    parser = argparse.ArgumentParser("Create template json model files for Feelpp/HiFiMagnet simu")
    parser.add_argument("--datafile", help="input data file (ex. HL-34-data.json)", default=None)
    parser.add_argument("--magnet", help="Magnet name (ex. HL-34)", default=None)

    parser.add_argument("--method", help="choose method (default is cfpdes", type=str,
                    choices=['cfpdes', 'CG', 'HDG', 'CRB'], default='cfpdes')
    parser.add_argument("--time", help="choose time type", type=str,
                    choices=['static', 'transient'], default='static')
    parser.add_argument("--geom", help="choose geom type", type=str,
                    choices=['Axi', '3D'], default='Axi')
    parser.add_argument("--model", help="choose model type", type=str,
                    choices=['th', 'mag', 'thmag', 'thmagel'], default='thmagel')
    parser.add_argument("--phytype", help="choose the type of physics", type=str,
                    choices=['linear', 'nonlinear'], default='linear')
    parser.add_argument("--cooling", help="choose cooling type", type=str,
                    choices=['mean', 'grad'], default='mean')
    parser.add_argument("--distance_unit", help="distance's unit", type=str,
                    choices=['meter','millimeter'], default='meter')

    parser.add_argument("--debug", help="activate debug", action='store_true')
    parser.add_argument("--verbose", help="activate verbose", action='store_true')

    args = parser.parse_args()

    if args.debug:
        print(args)

    if ( args.datafile == None ) and ( args.magnet == None ):
        print("You must enter datafile or magnet.")
        exit(1)

    if ( args.datafile != None ) and ( args.magnet != None ):
        print("You can't enter datafile and magnet together.")
        exit(1)

    if ( args.method == "HDG" ) or ( args.method == "CG" ):
        args.model = 'th'
        args.geom = '3D'

    # Get current dir
    cwd = os.getcwd()

    # Load magnetsetup config
    default_path = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(default_path, 'magnetsetup.json'), 'r') as appcfg:
        magnetsetup = json.load(appcfg)

    # Recuperate the data of configuration with datafile
    if args.datafile != None :
        # Load yaml file for geo config
        with open(args.datafile, 'r') as cfgdata:
            confdata = json.load(cfgdata)

        if args.debug:
            print("confdata=%s" % args.datafile)
            print(confdata['Helix'])

    # Recuperate the data of configuration with the direct name of magnet
    if args.magnet != None:
        print(url_api + '/magnet/mdata/' + args.magnet)
        r = requests.get(url= url_api + '/magnet/mdata/' + args.magnet )
        confdata = ast.literal_eval(r.text)

    yamlfile = confdata["geom"]

    if args.debug:
        print("yamlfile=%s" % yamlfile)
    with open(yamlfile, 'r') as cfgdata:
        cad = yaml.load(cfgdata, Loader = yaml.FullLoader)
        if isinstance(cad, Insert):
            (NHelices, NRings, NChannels, Nsections, index_h, 
                R1, R2, Z1, Z2, Zmin, Zmax, Dh, Sh) = python_magnetgeo.get_main_characteristics(cad)
        else:
            raise Exception("expected Insert yaml file")

    # Input values
    Tinit = 293
    Tin = 284.15
    h = [ 58222.1 ] * NChannels
    Tw = [ 290.671 ] * NChannels
    dTw = [ 12.74 ] * NChannels
    mu0 = 1 #4*math.pi * 1e-7

    # Manage the distance unit
    confdata, R1, R2, Z1, Z2, Zmin, Zmax, Dh, Sh, h, mu0 = convert_data(args.distance_unit, confdata, R1, R2, Z1, Z2, Zmin, Zmax, Dh, Sh, h, mu0)

    #print("R1={}, R2={}, Z1={}, Z2={}, Zmin={}, Zmax={}, Dh={}, Sh={}, h={}, mu0={}".format(type(R1), type(R2), type(Z1), type(Z2), type(Zmin), type(Zmax), type(Dh), type(Sh), type(h), type(mu0)))

    # Create indices and marker's names
    index_H, index_conductor, index_Helices, index_HelicesConductor = create_indices(NHelices, Nsections)
    part_withoutAir = create_part_withoutAir(args, NHelices, Nsections, NRings)
    boundary_Ring = create_boundary_Ring(NRings)
    boundary_withoutV = create_boundary_withoutV(NHelices, NRings, NChannels)
    boundary_withoutChannels = create_boundary_withoutChannels(NHelices, NRings)

    # load mustache template file
    # cfg_model  = magnetsetup[args.method][args.time][args.geom][args.model]["cfg"]
    json_model = magnetsetup[args.method][args.time][args.geom][args.model]["model"]
    if args.phytype == 'linear':
        conductor_model = magnetsetup[args.method][args.time][args.geom][args.model]["conductor-linear"]
        if args.geom == 'Axi':
            conductorbis_model = magnetsetup[args.method][args.time][args.geom][args.model]["insulator"]
    elif args.phytype == 'nonlinear':
        conductor_model = magnetsetup[args.method][args.time][args.geom][args.model]["conductor-nonlinear"]
        if args.geom == 'Axi':
            conductorbis_model = magnetsetup[args.method][args.time][args.geom][args.model]["conductorbis-nonlinear"]
    insulator_model = magnetsetup[args.method][args.time][args.geom][args.model]["insulator"]
    if args.model != 'mag':
        cooling_model = magnetsetup[args.method][args.time][args.geom][args.model]["cooling"][args.cooling]
        flux_model = magnetsetup[args.method][args.time][args.geom][args.model]["cooling-post"][args.cooling]

    # TODO create default path to mustache according to method, geom
    template_path = os.path.join(default_path, "templates", args.method, args.geom)
    fmodel = os.path.join(template_path, json_model)
    fconductor = os.path.join(template_path, conductor_model)
    if args.geom == 'Axi':
        fconductorbis = os.path.join(template_path, conductorbis_model)
    finsulator = os.path.join(template_path, insulator_model)
    if args.model != 'mag':
        fcooling = os.path.join(template_path, cooling_model)
        fflux = os.path.join(template_path, flux_model)
    
    with open(fmodel, "r") as ftemplate:
        jsonfile = chevron.render(ftemplate, {'index_h': index_h, 'index_conductor':index_conductor, 'imin': 0, 'imax': NHelices+1, 'part_withoutAir':part_withoutAir, 'boundary_Ring':boundary_Ring })
        jsonfile = jsonfile.replace("\'", "\"")
        # shall get rid of comments: //*
        # now tweak obtained json
        data = json.loads(jsonfile)
        
        # Fill parameters
        params_dict = create_params_dict(args, Zmin, Zmax, Sh, Dh, Tinit, Tin, h, Tw, dTw, mu0, NHelices, Nsections)
        
        for key in params_dict:
            data["Parameters"][key] = params_dict[key]

        # Fill materials (Axi specific)
        if args.method == 'cfpdes':
            materials_dict = create_materials_cfpdes(args, cwd, magnetsetup, template_path, confdata, finsulator, fconductor, fconductorbis, NHelices, Nsections, NRings)
        elif ( args.method == 'HDG' ) or ( args.method == 'CG' ) :
            materials_dict = create_materials_hdg_cg(confdata, finsulator, fconductor, NHelices, NRings)

        for key in materials_dict:
            data["Materials"][key] = materials_dict[key]

        # Fill BoundaryConditions
        # Cooling BCs
        if args.model != 'mag':
            if args.method == 'cfpdes':
                data["BoundaryConditions"]["heat"]["Robin"] = create_bcsFlux_dict(NChannels, fcooling)
            elif ( args.method == 'HDG' ) or ( args.method == 'CG' ) :
                data["BoundaryConditions"]["temperature"]["Robin"] = create_bcsFlux_dict(NChannels, fcooling)

        # HDG case
        if args.method == 'HDG':
            data["BoundaryConditions"]["electric-potential"]["Neumann"] = { "myneumannelec" : { "markers":boundary_withoutV, "expr":0 } }
            data["BoundaryConditions"]["temperature"]["Neumann"] = { "myneumannheat" : { "markers":boundary_withoutChannels, "expr":0 } }

        # Fill PostProcess
        # Flux
        if args.model != 'mag' and args.method == 'cfpdes' :
            # add flux_model for Flux_Channel calc
            with open(fflux, "r") as ftemplate:
                jsonfile = chevron.render(ftemplate, {'index_h': "0:%s" % str(NChannels)})
                jsonfile = jsonfile.replace("\'", "\"")
                mdata = json.loads(jsonfile)
                data["PostProcess"]["heat"]["Measures"]["Statistics"]["Flux_Channel%1%"] = mdata["Flux"]["Flux_Channel%1%"]
                for i in range(NHelices) :
                    data["PostProcess"]["heat"]["Measures"]["Statistics"]["MeanT_H{}".format(i+1)] = {"type" : ["min","max","mean"], "field":"temperature", "markers": {"name": "H{}_Cu%1%".format(i+1),"index1":index_Helices[i]}}

        if args.model != 'th' and args.method == 'cfpdes' :
            # Add Electrical Power by Helix
            for i in range(NHelices) :
                data["PostProcess"]["magnetic"]["Measures"]["Statistics"]["Power_H{}".format(i+1)] = {"type" : "integrate",
                    "expr":"2*pi*materials_sigma*(materials_U/2/pi)*(materials_U/2/pi)/x:materials_sigma:materials_U:x".format(i+1),
                    "markers": {"name": "H{}_Cu%1%".format(i+1),"index1":index_HelicesConductor[i]}}

        # save json (NB use x to avoid overwrite file)
        if args.datafile != None :
            outfilename = args.datafile.replace(".json","")
        if args.magnet != None :
            outfilename = args.magnet
        outfilename += "-" + args.method
        outfilename += "-" + args.model
        outfilename += "-" + args.phytype
        outfilename += "-" + args.geom
        outfilename += "-sim.json"

        with open(outfilename, "w") as out:
            out.write(json.dumps(data, indent = 4))

if __name__ == "__main__":
    main()