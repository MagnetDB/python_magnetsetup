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

from setup_cfpdes import json_cfpdes
from setup_hdg import json_hdg

def export_table(table: str):
    """
    Return the pd.DataFrame correspondant to table of database from localhost:8000/api
    """

    # Connect to "http://localhost:8000/api/table/"
    base_url_db_api="http://localhost:8000/api/" + table + "/"

    page = requests.get(url=base_url_db_api)

    print("connect :", page.url, page.status_code)

    if page.status_code != 200 :
        print("cannot logging to %s" % base_url_db_api)
        sys.exit(1)
    
    # Create the DataFrame
    list_table = ast.literal_eval(page.text)
    n = len(list_table)

    keys = list_table[0].keys()
    data_table = pd.DataFrame(columns=keys)

    for id in range(n):
        serie = pd.Series(list_table[id])
        data_table= data_table.append(serie, ignore_index=True)
    
    return data_table

def create_confdata_magnet(magnet: str, debug=False):
    """
    Return confdata the dictionnary of configuration of magnet.
    """

    # Export magnets table
    data_magnets = export_table('magnets')
    #data_magnets = export_table('mpartmagnetlink')
    
    # Search magnet
    names = data_magnets['name']
    if  magnet not in names.values :
        print("magnet : " + magnet + " isn\'t in database.")
        exit(1)
    
    if debug:
        print("magnet : " + magnet + " is in database.")

    serie_magnet = data_magnets[ data_magnets['name']==magnet ]

    # Export mparts of magnet
    data_mparts = export_table('mparts')
    data_mparts = data_mparts[ data_mparts['be']==serie_magnet['be'][0] ]

    # Recuperate the materials
    data_materials = export_table('materials')

    # Create dictionnary of magnet's configuration
    confdata = {}

    confdata['geom'] = serie_magnet['geom'][0]
    confdata['Helix'] = []
    confdata['Ring'] = []
    confdata['Lead'] = []
    for id in data_mparts['id']:
        mpart = data_mparts[ data_mparts['id'] == id ]
        material = data_materials[ data_materials['id'] == mpart['material_id'].values[0] ]
        
        material = material.drop( labels=['name', 'id'], axis=1 )

        dict_mpart = {'geo': mpart['geom'].values[0] }
        dict_material = {}
        for column in material.columns :
            dict_material[column] = material[column].values[0]
        dict_mpart['material'] = dict_material

        confdata[ mpart['mtype'].values[0] ].append(dict_mpart)
    
    return confdata

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
    parser.add_argument("--scale", help="scale of geometry", type=float, default=1e-3)

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
        magnet = args.magnet
        confdata = create_confdata_magnet(magnet, args.debug)

    yamlfile = confdata["geom"]

    if args.debug:
        print("yamlfile=%s" % yamlfile)

    if args.method == 'cfpdes':
        data = json_cfpdes(args, confdata, yamlfile, magnetsetup, default_path, cwd)

    if args.method == 'hdg':
        data = json_hdg()
    
    # save json (NB use x to avoid overwrite file)
    if args.datafile != None :
        outfilename = args.datafile.replace(".json","")
    if args.magnet != None :
        outfilename = magnet
    outfilename += "-" + args.method
    outfilename += "-" + args.model
    outfilename += "-" + args.phytype
    outfilename += "-" + args.geom
    outfilename += "-sim.json"

    with open(outfilename, "w") as out:
        out.write(json.dumps(data, indent = 4))

if __name__ == "__main__":
    main()
