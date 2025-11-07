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

import os
import itertools

# from python_magnetgeo.Insert import Insert
# from python_magnetgeo.MSite import MSite
from python_magnetgeo.utils import getObject
from python_magnetgeo.MSite import MSite
from python_magnetgeo.Insert import Insert
from python_magnetgeo.Bitters import Bitters
from python_magnetgeo.Supras import Supras
from python_magnetgeo.Bitter import Bitter
from python_magnetgeo.Supra import Supra

# from .config import appenv
from .config import loadconfig, loadtemplates

# from .objects import load_object, load_object_from_db
from .objects import load_object
from .utils import NMerge
from .cfg import create_cfg
from .jsonmodel import create_json

from .insert import Insert_setup, Insert_simfile
from .bitter import Bitter_setup

# from .bitter import Bitter_simfile
from .supra import Supra_setup, Supra_simfile

from .file_utils import MyOpen, findfile, search_paths

# from .units import load_units, convert_data
from glob import glob

from .node import NodeSpec


def magnet_simfile(
    MyEnv, confdata: str, cad: Insert | Bitters | Supras, addAir: bool = False, debug: bool = False, session=None
):
    """
    create sim files for magnet
    """
    files = []
    yamlfile = confdata["geom"]
    with MyOpen(yamlfile, "r", paths=search_paths(MyEnv, "geom")) as cfgdata:

        match cad:
            case Insert():
                files.append(cfgdata.name)
                tmp_files = Insert_simfile(MyEnv, confdata, cad, addAir)
                for tmp_f in tmp_files:
                    files.append(tmp_f)
            case Bitters():
                for obj in confdata["Bitter"]:
                    yamlfile = obj["geom"]
                    with MyOpen(yamlfile, "r", paths=search_paths(MyEnv, "geom")) as f:
                        files.append(f.name)
            case Supras():
                for i, obj in enumerate(confdata["Supra"]):
                    mcad = cad.magnets[i]
                    yamlfile = obj["geom"]
                    with MyOpen(yamlfile, "r", paths=search_paths(MyEnv, "geom")) as f:
                        files.append(f.name)
                    
                    struct = Supra_simfile(MyEnv, obj, mcad)
                    if struct:
                            files.append(struct)
            case _:
                raise Exception(f"magnet_simfile: unexpected cad type {type(cad)}")

    return files


def magnet_setup(
    MyEnv,
    mname: str,
    confdata: dict,
    cad: Insert | Bitters | Supras,
    method_data: list,
    templates: dict,
    current: float = 31.0e3,
    debug: bool = False,
):
    """
    Creating dict for setup for magnet
    """

    print(f"magnet_setup: mname={mname}")
    if debug:
        print(f"magnet_setup: confdata={confdata}"),

    mdict = {}
    mmat = {}
    mmodels = {}
    mpost = {}

    innerbore = cad.innerbore
    outerbore = cad.outerbore
    print(
        f"Load magnet: mname={mname}, cad={cad.name}, innerbore={innerbore}, outerbore={outerbore}"
    )

    match cad:
        case Insert():
            print(f"Load an insert: mname={mname}")
            # if isinstance(cad, Insert):
            (mdict, mmat, mmodels, mpost) = Insert_setup(
                MyEnv, mname, confdata, cad, method_data, templates, current, debug
            )
        case Bitters():
            print(f"Load a Bitters: mname={mname}")
            # if isinstance(cad, Bitter):
            for i, obj in enumerate(confdata["Bitter"]):
                (mdict, mmat, mmodels, mpost) = Bitter_setup(
                    MyEnv, mname, obj, cad.magnets[i], method_data, templates, current, debug
                )
                (mdict, mmat, mmodels, mpost) = _setup(mname, "Bitter", cad.name, tdict, tmat, tmodels, tpost, debug)
        case Supras():
            print(f"Load a Supras: mname={mname}")
            # if isinstance(cad, Supra):
            for i, obj in enumerate(confdata["Supra"]):
                (tdict, tmat, tmodels, tpost) = Supra_setup(
                    MyEnv, mname, obj, cad.magnets[i], method_data, templates, current, debug
                )
                (mdict, mmat, mmodels, mpost) = _setup(mname, "Supra", cad.name, tdict, tmat, tmodels, tpost, debug)
        case _:
            raise Exception(f"magnet_setup: unexpected cad type {type(cad)}")

    if debug:
        print(f"magnet_setup: mdict={mdict}")
    return (mdict, mmat, mmodels, mpost)

def _setup(mname, mtype, cad_name, tdict, tmat, tmodels, tpost, debug):

    mdict = {}
    mmat = {}
    mmodels = {}
    mpost = {}

    if debug:
        print(f"tdict: {tdict}")
    NMerge(
        tdict,
        mdict,
        debug,
        name=f"magnet_setup {mtype} mdict for {mname}/{cad_name}",
    )
    # print(f"magnet_setup: {mtype}, mname={mname}, tdict={tdict}")
    # print(f"magnet_setup: {mtype}, mname={mname}, mdict={mdict}")
    print(
        f'magnet_setup: {mtype}, mname={mname}, mdict[init_temp]={mdict["init_temp"]}'
    )
    # print(f"magnet_setup: {mtype}, mname={mname}, mdict[power_magnet]={mdict['power_magnet']}")
    # list_name = [item['name'] for item in mdict['int_temp']]

    if debug:
        print(f"tmat: {tmat}")
    NMerge(tmat, mmat, debug, name="magnet_setup Bitter/Supra mmat")

    if debug:
        print(f"tmodels: {tmodels}")
    for physic in tmodels:
        if physic not in mmodels:
            mmodels[physic] = {}
        NMerge(
            tmodels[physic],
            mmodels[physic],
            debug,
            name="magnet_setup Bitter/Supra mmodels ",
        )

    if debug:
        print(f"tpost: {tpost}")
    NMerge(
        tpost, mpost, debug, name="magnet_setup Bitter/Supra mpost"
    )  # debug)
    if debug:
        print(f"magnet_setup: {mtype}, mname={mname}, tpost={tpost}")
        print(f"magnet_setup: {mtype}, mname={mname}, mpost={mpost}")

    for key in ["Current", "Power"]:
        list_current = []
        for item in mpost[key]:
            if isinstance(item, dict) and "part_electric" in item:
                list_current = list(
                    set(list_current + item["part_electric"])
                )
        if list_current:
            mpost[key] = [{"part_electric": list_current}]
            if debug:
                print(
                    f"magnet_setup {mname}: force mpost[{key}]={mpost[key]}"
                )

    tdict.clear()
    tmat.clear()
    tmodels.clear()
    tpost.clear()

    # fix init_temp and power_magnet entries in mdict
    print(f"mdict: key={mdict.keys()}")
    for key in ["init_temp", "power_magnet", "T_magnet"]:
        if len(mdict[key]) > 1:
            # print(f"setup/magnet_setup mname={mname}: mdict[{key}]={mdict[key]}")
            _key = [item["name"] for item in mdict[key]]
            _keys = list(set(_key))
            if key == "init_temp":
                _pref = [item["prefix"] for item in mdict[key]]
                _prefs = list(set(_pref))
            if len(_keys) > 1:
                raise Exception(
                    f"setup/magnet_setup mname={mname}: mdict[{key}] seems broken - mdict[{key}]={mdict[key]}"
                )

            _list = [item["magnet_parts"] for item in mdict[key]]
            _lists = list(set(list(itertools.chain(*_list))))
            if key == "init_temp":
                mdict[key] = [
                    {
                        "name": _keys[0],
                        "prefix": _prefs[0],
                        "magnet_parts": _lists,
                    }
                ]
            else:
                mdict[key] = [{"name": _keys[0], "magnet_parts": _lists}]
            if debug:
                print(
                    f"setup/magnet_setup mname={mname}: force mdict[{key}] to = {{'name': _keys[0], 'magnet_parts': _lists}}"
                )

    return (mdict, mmat, mmodels, mpost)          



def msite_simfile(MyEnv, confdata: str, cad: MSite, addAir: bool = False, session=None):
    """
    Creating list of simulation files for msite
    """

    files = []

    # TODO: get xao and brep if they exist, otherwise go on
    # TODO: add suffix _Air if needed ??
    try:
        xaofile = confdata["name"] + ".xao"
        if addAir:
            xaofile = confdata["name"] + "_withAir.xao"
        f = findfile(xaofile, paths=search_paths(MyEnv, "cad"))
        files.append(f)

        brepfile = confdata["name"] + ".brep"
        if addAir:
            brepfile = confdata["name"] + "_withAir.brep"
        f = findfile(brepfile, paths=search_paths(MyEnv, "cad"))
        files.append(f)
    except:
        for i, magnet in enumerate(confdata["magnets"]):
            mconfdata = load_object(MyEnv, magnet + "-data.json")
            mcad = cad.magnets[i]

            files += magnet_simfile(MyEnv, mconfdata, mcad)

    return files


def msite_setup(
    MyEnv,
    confdata: str,
    cad: MSite,
    method_data: list,
    templates: dict,
    currents: dict,
    debug: bool = False,
    session=None,
):
    """
    Creating dict for setup for msite
    """
    print(f"msite_setup: confdata={confdata}")
    if debug:
        print("msite_setup:", "confdata=", confdata)
        print("msite_setup: confdata[magnets]=", confdata["magnets"])

    mdict = {}
    mmat = {}
    mmodels = {}
    mpost = {}

    for i, magnet in enumerate(confdata["magnets"]):
        mname = list(magnet.keys())[0]
        print(f"msite_setup: magnet_setup[{mname}]")
        if debug:
            print(f"msite_setup: magnet_setup[{mname}]: {magnet}, confdata={magnet}")

        mconfdata = magnet[mname]
        mcad = cad.magnets[i]
        current = currents[mname]["value"]
        (tdict, tmat, tmodels, tpost) = magnet_setup(
            MyEnv, mname, mconfdata, mcad, method_data, templates, current, debug
        )
        # print(f"msite_setup({mname}): tdict={tdict}")
        # print(f"msite_setup({mname}): tdict[init_temp]={tdict['init_temp']}")
        # print(f"msite_setup({mname}): tdict[power_magnet]={tdict['power_magnet']}")
        if debug:
            print(f"tpost[{mname}][Current]: {tpost['Current']}")

        NMerge(tdict, mdict, debug, name=f"msite_setup: merge(mdict,tdict) for {mname}")
        # if debug:
        # print("tdict[part_electric]:", tdict['part_electric'])
        # print("tdict[part_thermic]:", tdict['part_thermic'])
        # print("mdict[part_electric]:", mdict['part_electric'])
        # print("mdict[part_thermic]:", mdict['part_thermic'])

        NMerge(tmat, mmat, debug, "msite_setup/tmat")
        if debug:
            print("mmat:", mmat)

        if debug:
            print(f"tmodels: {tmodels}")
        for physic in tmodels:
            if physic not in mmodels:
                mmodels[physic] = {}
            NMerge(
                tmodels[physic],
                mmodels[physic],
                debug,
                name="msite_setup mmodels ",
            )

        NMerge(tpost, mpost, debug, "msite_setup/tpost")

        tdict.clear()
        tmat.clear()
        tmodels.clear()
        tpost.clear()

        for key in ["Current", "Power"]:
            list_current = []
            for item in mpost[key]:
                if isinstance(item, dict) and "part_electric" in item:
                    list_current = list(set(list_current + item["part_electric"]))
            if list_current:
                mpost[key] = [{"part_electric": list_current}]
                if debug:
                    print(f"msite_setup {mname}: force mpost[{key}]={mpost[key]}")
        if debug:
            print("NewMerge:", mpost)

    # print(f"msite_setup: mdict={mdict}")
    # print(f"msite_setup: mdict[init_temp]={mdict['init_temp']}")
    # print(f"msite_setup: mdict[power_magnet]={mdict['power_magnet']}")

    if debug:
        print(f"mpost: {mpost}")

    if debug:
        print("mdict:", mdict)
    return (mdict, mmat, mmodels, mpost)


def setup(MyEnv, args, confdata, jsonfile: str, currents: dict, session=None):
    """
    generate sim files
    """
    print(f"setup: currents={currents}")

    # loadconfig
    AppCfg = loadconfig()

    # Get current dir
    cwd = os.getcwd()
    if args.wd:
        os.chdir(args.wd)
    print(f"setup/main: {os.getcwd()}")

    # load appropriate templates
    # TODO force millimeter when args.method == "HDG"
    method_data = [
        args.method,
        args.time,
        args.geom,
        args.model,
        args.cooling,
        "meter",
        args.nonlinear,
    ]

    # TODO: if HDG meter -> millimeter
    templates = loadtemplates(MyEnv, AppCfg, method_data)

    mdict = {}
    mmat = {}
    mpost = {}

    if args.debug:
        print(f"setup: confdata={confdata}")
    cad_basename = ""
    if "geom" in confdata:
        if args.debug:
            print(f"Load a magnet {confdata['geom']}")
        with MyOpen(confdata["geom"], "r", paths=search_paths(MyEnv, "geom")) as f:
            print(f.name)
            cad = getObject(f.name)
            cad_basename = cad.name

        [mname] = currents.keys()
        current = currents[mname]["value"]
        (mdict, mmat, mmodels, mpost) = magnet_setup(
            MyEnv,
            "",
            confdata,
            cad,
            method_data,
            templates,
            current,
            args.debug or args.verbose,
        )
    else:
        if args.debug:
            print(f"Load a msite {confdata['name']}")
        cad_basename = confdata["name"]

        # why do I need that???
        try:
            f = findfile(confdata["name"] + ".yaml", search_paths(MyEnv, "geom"))
            print(f.name)
            cad = getObject(f.name)
            cad_basename = cad.name

        except FileNotFoundError as e:
            print(f"setup: {e}")

        # print(f"{confdata['name']}: {confdata}")
        (mdict, mmat, mmodels, mpost) = msite_setup(
            MyEnv,
            confdata,
            cad,
            method_data,
            templates,
            currents,
            args.debug or args.verbose,
            session,
        )
    if args.debug:
        print(f"setup: mpost[]={mpost}")

    name = jsonfile
    if name in confdata:
        name = confdata["name"]
        if args.debug:
            print(f"name={name} from confdata")

    # create cfg
    jsonfile += "-" + args.method
    jsonfile += "-" + args.model
    if args.nonlinear:
        jsonfile += "-nonlinear"
    jsonfile += "-" + args.geom
    jsonfile += "-sim.json"
    cfgfile = jsonfile.replace(".json", ".cfg")

    # addAir = False
    # if "mag" in args.model or "mqs" in args.model:
    #     addAir = True

    # retreive xaofile and meshfile
    xaofile = cad_basename + ".xao"
    if args.geom == "Axi" and args.method == "cfpdes":
        xaofile = cad_basename + "-Axi.xao"
        if "mqs" in args.model or "mag" in args.model:
            xaofile = cad_basename + "-Axi_withAir.xao"

    meshfile = xaofile.replace(".xao", ".med")
    if args.geom == "Axi" and args.method == "cfpdes":
        # # if gmsh:
        meshfile = xaofile.replace(".xao", ".msh")
    print(f"setup: meshfile={meshfile}")

    # TODO create_mesh() or load_mesh()
    # generate properly meshfile for cfg
    # generate solver section for cfg
    # here name is from args (aka name of magnet and/or msite if from db)
    create_cfg(
        cfgfile,
        os.path.basename(name),
        meshfile,
        args.nonlinear,
        jsonfile.replace(f"{os.path.dirname(name)}/", ""),
        templates["cfg"],
        method_data,
        args.debug,
    )

    # create json
    create_json(
        jsonfile, mdict, mmat, mmodels, mpost, templates, method_data, args.debug
    )

    if "geom" in confdata:
        print(f'magnet geo: {confdata["geom"]}')
        yamlfile = confdata["geom"]
    else:
        print(f'site geo: {confdata["name"]}')
        yamlfile = confdata["name"] + ".yaml"

    # copy some additional json file
    material_generic_def = ["conductor", "insulator"]
    if args.time == "transient":
        material_generic_def.append("conduct-nosource")  # only for transient with mqs

    if args.method == "cfpdes":
        if args.debug:
            print("cwd=", cwd)
        from shutil import copyfile

        for jfile in material_generic_def:
            filename = AppCfg[args.method][args.time][args.geom][args.model][
                "filename"
            ][jfile]
            src = os.path.join(
                MyEnv.template_path(), args.method, args.geom, args.model, filename
            )
            dst = os.path.join(
                os.getcwd(), f"{jfile}-{args.method}-{args.model}-{args.geom}.json"
            )
            if args.debug:
                print(f"{jfile}, filename={filename}, src={src}, dst={dst}")
            copyfile(src, dst)

        csvfiles = glob("./*.csv")
        print(f"csvfiles: {csvfiles}")
        if args.debug:
            print(f"pwd: {os.getcwd()}, ls: {os.listdir(os.curdir)}")

    return (yamlfile, cfgfile, jsonfile, xaofile, meshfile, csvfiles)  # , tarfilename)

def commissioning_setup(MyEnv, args, confdata, jsonfile: str, currents: dict, session=None):
    """
    generate sim files for commissiong
    """
    import copy

    print(f"commissioning_setup: args={args} (type={args}), currents={currents}")

    # loadconfig
    AppCfg = loadconfig()

    # Get current dir
    cwd = os.getcwd()
    if args.wd:
        os.chdir(args.wd)
    print(f"commissioning_setup/main: {os.getcwd()}")

    if args.geom ==  "3D":
        raise RuntimeError(f"commissioning_setup for 3D geometries not implemented yet")

    # call setup for several scenario corresponding to cooling
    heatcorrelations = [args.hcorrelation]
    if args.hcorrelation == "all":
        heatcorrelations = ["Montgomery", "Dittus", "Colburn", "Silverberg"]

    frictions = [args.frictions]
    if args.friction == "all":
        frictions = ["Constant", "Blasius", "Filonenko", "Colebrook", "Swanee"]

    coolings = [args.cooling]
    if args.cooling == "all":
        coolings = ["mean", "meanH", "grad", "gradH", "gradHZ", "gradHZH"]

    commissiong_data = {}
    for heatcorrelation in heatcorrelations:
        for cooling in coolings:
            for friction in frictions:
                setup_args = copy.deepcopy(args)
                setup_args.cooling = cooling
                setup_args.frictions = friction
                setup_args.hcorrelation = heatcorrelation
                setup_args.wd = f"{args.wd}/{cooling}/{friction}/{heatcorrelation}"
                (yamlfile, cfgfile, jsonfile, xaofile, meshfile, csvfiles) = setup(MyEnv, setup_args, confdata, jsonfile, currents, session)
                commissioning_setup[setup_args.wd] = (yamlfile, cfgfile, jsonfile, xaofile, meshfile, csvfiles)

    return commissiong_data

def setup_cmds(
    MyEnv,
    args,
    node_spec: NodeSpec,
    yamlfile: str,
    cfgfile: str,
    jsonfile: str,
    xaofile: str,
    meshfile: str,
    csvfiles: list,
    root_directory: str,
    currents: dict,
):
    """
    create cmds

    Watchout: gsmh/salome base mesh is always in millimeter
    For simulation it is madatory to use a mesh in meter except maybe for HDG
    """

    # loadconfig
    AppCfg = loadconfig()

    # TODO adapt NP to the size of the problem
    # if server is SMP mpirun outside otherwise inside singularity
    NP = node_spec.cores
    print(f"NP={NP}")
    if node_spec.multithreading:
        NP = int(NP / 2)
        print(f"NP={NP} multithreading on")
    if args.debug:
        print(f"NP={NP} {type(NP)}")
    if args.np > 0:
        if args.np > NP:
            print(
                f"requested number of cores {args.np} exceed {node_spec.name} capability (max: {NP})"
            )
            print(f"keep {NP} cores")
        else:
            NP = args.np
    print(f"NP={NP}, args.np={args.np}")

    simage_path = MyEnv.simage_path()
    hifimagnet = AppCfg["mesh"]["hifimagnet"]
    salome = AppCfg["mesh"]["salome"]
    gmsh = AppCfg["mesh"]["gsmh"]
    feelpp = AppCfg[args.method]["feelpp"]
    partitioner = AppCfg["mesh"]["partitioner"]
    if "exec" in AppCfg[args.method]:
        exec = AppCfg[args.method]["exec"]
    if "exec" in AppCfg[args.method][args.time][args.geom][args.model]:
        exec = AppCfg[args.method][args.time][args.geom][args.model]

    print(f"currents({type(currents)}): {currents}")
    # currents: {mname: {value: x, type: t}}

    pyfeel = " -m python_magnetworkflows.cli"  # fix-current, commisioning, fixcooling
    pyfeel_args = f"--current {currents} --cooling {args.cooling} --eps {1.e-5} --itermax {20} --flow_params {args.flow_params}"

    # TODO infty as params
    if "mqs" in args.model or "mag" in args.model:
        geocmd = (
            f"salome -w1 -t {hifimagnet}/HIFIMAGNET_Cmd.py args:{yamlfile},--air,8,6"
        )
        meshcmd = f"salome -w1 -t {hifimagnet}/HIFIMAGNET_Cmd.py args:{yamlfile},--air,8,6,--wd,$PWD,mesh,--group,CoolingChannels,Isolants"  # -wd ??
    else:
        geocmd = f"salome -w1 -t {hifimagnet}/HIFIMAGNET_Cmd.py args:{yamlfile},8,6"
        meshcmd = f"salome -w1 -t {hifimagnet}/HIFIMAGNET_Cmd.py args:{yamlfile},8,6,--wd,$PWD,mesh,--group,CoolingChannels,Isolants"  # -wd ??

    gmshfile = meshfile.replace(".med", ".msh")
    meshconvert = ""

    if args.geom == "Axi" and args.method == "cfpdes":
        if "mqs" in args.model or "mag" in args.model:
            geocmd = f"salome -w1 -t {hifimagnet}/HIFIMAGNET_Cmd.py args:{yamlfile},--axi,--air,8,6"
        else:
            geocmd = (
                f"salome -w1 -t {hifimagnet}/HIFIMAGNET_Cmd.py args:{yamlfile},--axi"
            )

        # let xao decide mesh caracteristic length ??:
        meshcmd = f"python3 -m python_magnetgmsh.xao2msh {xaofile} --wd data/geometries --geo {yamlfile} mesh --group CoolingChannels"

        # or use gmsh api (do not support Supra with details)
        # meshcmd = f"python3 -m python_magnetgmsh.cli {yamlfile} --wd data/geometries --thickslit --mesh --group CoolingChannels"

    else:
        gmshfile = meshfile.replace(".med", ".msh")
        meshconvert = f"gmsh -0 {meshfile} -bin -o {gmshfile}"

    scale = ""
    if args.method != "HDG":
        scale = "--mesh.scale=0.001"
    h5file = xaofile.replace(".xao", f"_p{NP}.json")

    partcmd = f"{partitioner} --ifile $PWD/data/geometries/{gmshfile} --odir $PWD/data/geometries --part {NP} {scale}"

    tarfile = cfgfile.replace("cfg", "tgz")
    # TODO if cad exist do not print CAD command
    cmds = {
        "Unpack": f"tar zxvf {tarfile}",
        "CAD": f"singularity exec {simage_path}/{salome} {geocmd}",
    }

    # TODO add mount specific point for selected node
    if args.geom == "Axi":
        cmds["Mesh"] = f"singularity exec {simage_path}/{gmsh} {meshcmd}"
    else:
        cmds["Mesh"] = f"singularity exec {simage_path}/{salome} {meshcmd}"

    if meshconvert:
        cmds["Convert"] = f"singularity exec {simage_path}/{salome} {meshconvert}"

    if args.geom == "3D":
        cmds["Partition"] = f"singularity exec {simage_path}/{feelpp} {partcmd}"
        meshfile = h5file
        update_partition = (
            f"perl -pi -e 's|gmsh.partition=.*|gmsh.partition = 0|' {cfgfile}"
        )
        cmds["Update_Partition"] = update_partition

    if args.geom == "Axi":
        cmds["Partition"] = f"singularity exec {simage_path}/{feelpp} {partcmd} --dim 2"
        meshfile = h5file

    update_cfgmesh = f"perl -pi -e 's|mesh.filename=.*|mesh.filename=\$cfgdir/data/geometries/{meshfile}|' {cfgfile}"
    cmds["Update_Mesh"] = update_cfgmesh

    # TODO add command to change mesh.filename in cfgfile

    feelcmd = f"{exec} --directory {root_directory} --config-file {cfgfile}"
    pyfeelcmd = f"python {pyfeel} {cfgfile} {pyfeel_args}"
    if node_spec.smp:
        feelcmd = f"mpirun -np {NP} {feelcmd}"
        pyfeelcmd = f"mpirun -np {NP} {pyfeelcmd}"
        # feelcmd = f"mpirun --allow-run-as-root -np {NP} {exec} --config-file {cfgfile}"
        # pyfeelcmd = f"mpirun --allow-run-as-root -np {NP} python {pyfeel} {cfgfile}"
        cmds["Run"] = f"singularity exec {simage_path}/{feelpp} {feelcmd}"
        cmds["Workflow"] = f"singularity exec {simage_path}/{feelpp} {pyfeelcmd}"
    else:
        cmds[
            "Run"
        ] = f"mpirun -np {NP} singularity exec {simage_path}/{feelpp} {feelcmd}"
        cmds[
            "Workflow"
        ] = f"mpirun -np {NP} singularity exec {simage_path}/{feelpp} {pyfeelcmd}"

    # compute resultdir:
    # with open(cfgfile, 'r') as f:
    #     directory = re.sub('directory=', '', f.readline(), flags=re.DOTALL)
    # home_env = 'HOME'
    # result_dir = f'{os.getenv(home_env)}/feelppdb/{directory.rstrip()}/np_{NP}'
    # result_arch = cfgfile.replace('.cfg', '_res.tgz')
    result_dir = f"{root_directory}/feelppdb/np_{NP}"
    print(f"result_dir={result_dir}")

    paraview = AppCfg["post"]["paraview"]

    # change to use hifimagnet.paraview stuff
    # # get expr and exprlegend from method/model/...
    if "post" in AppCfg[args.method][args.time][args.geom][args.model]:
        postdata = AppCfg[args.method][args.time][args.geom][args.model]["post"]

        # TODO: Get Path to pv-scalarfield.py:  /usr/lib/python3/dist-packages/python_magnetsetup/postprocessing/
        for key in postdata:
            pyparaview = f'/usr/lib/python3/dist-packages/python_magnetsetup/postprocessing//pv-scalarfield.py --cfgfile {cfgfile}  --jsonfile {jsonfile} --expr {key} --exprlegend "{postdata[key]}" --resultdir {result_dir}'
            # pyparaview = f'pv-scalarfield.py --cfgfile {cfgfile}  --jsonfile {jsonfile} --expr {key} --exprlegend \"{postdata[key]}\" --resultdir {result_dir}'
            pyparaviewcmd = f"pvpython {pyparaview}"
            cmds[
                "Postprocessing"
            ] = f"singularity exec {simage_path}/{paraview} {pyparaviewcmd}"

    # cmds["Save"] = f"pushd {result_dir}/.. && tar zcf {result_arch} np_{NP} && popd && mv {result_dir}/../{result_arch} ."

    # TODO jobmanager if node_spec.manager != JobManagerType.none
    # Need user email at this point
    # Template for oar and slurm

    # TODO what about postprocess??
    # TODO get results (value.csv, png, raw data) to magnetdb

    return cmds

def commissioning_cmds(
    MyEnv,
    args,
    node_spec: NodeSpec,
    commissioning_data: dict,
    root_directory: str,
    currents: dict,
    ):
    """
    create cmds for commissioning
    """
    import copy

    # loadconfig
    AppCfg = loadconfig()

    # TODO adapt NP to the size of the problem
    # if server is SMP mpirun outside otherwise inside singularity
    NP = node_spec.cores
    print(f"NP={NP}")
    if node_spec.multithreading:
        NP = int(NP / 2)
        print(f"NP={NP} multithreading on")
    if args.debug:
        print(f"NP={NP} {type(NP)}")
    if args.np > 0:
        if args.np > NP:
            print(
                f"requested number of cores {args.np} exceed {node_spec.name} capability (max: {NP})"
            )
            print(f"keep {NP} cores")
        else:
            NP = args.np
    print(f"NP={NP}, args.np={args.np}")

    simage_path = MyEnv.simage_path()
    feelpp = AppCfg[args.method]["feelpp"]

    # create mdata from currents only once
    keys = list(commissioning_data)
    cfgfile = commissioning_data[keys[0]][1]

    mdata = {}

    # call setup for several scenario corresponding to cooling
    heatcorrelations = [args.hcorrelation]
    if args.hcorrelation == "all":
        heatcorrelations = ["Montgomery", "Dittus", "Colburn", "Silverberg"]

    frictions = [args.frictions]
    if args.friction == "all":
        frictions = ["Constant", "Blasius", "Filonenko", "Colebrook", "Swanee"]

    coolings = [args.cooling]
    if args.cooling == "all":
        coolings = ["mean", "meanH", "grad", "gradH", "gradHZ", "gradHZH"]

    # workflow matrix
    pyfeel = " -m  python_magnetworkflows.run commissioning"  # fix-current, commisioning, fixcooling
    pyfeel_args = f"--cfgfile {keys[0]}/{cfgfile}"
    pyfeel_args += f" --mdata {mdata}"
    pyfeel_args += f" --coolings {coolings}"
    pyfeel_args += f" --hcorrelations {heatcorrelations}"
    pyfeel_args += f" --frictions {frictions}"

    cmds = {}
    for key in commissioning_data:
        basedir, cooling, friction, heatcorrelation = key.split("/")
        setup_args = copy.deepcopy(args)
        setup_args.cooling = cooling
        setup_args.frictions = friction
        setup_args.hcorrelation = heatcorrelation
        setup_args.wd = f"{args.wd}/{cooling}/{friction}/{heatcorrelation}"
        (yamlfile, cfgfile, jsonfile, xaofile, meshfile, csvfiles) = commissioning_data[key]
        sub_cmds = setup_cmds(MyEnv, setup_args, node_spec, yamlfile, cfgfile, jsonfile, xaofile, meshfile, csvfiles, root_directory, currents)
        print(f'{key}: sub_cmds={list(sub_cmds.keys())}')
        # shall remove run and workflow from sub_cmds

    pyfeelcmd = f"python {pyfeel} {cfgfile} {pyfeel_args}"
    if node_spec.smp:
        pyfeelcmd = f"mpirun -np {NP} {pyfeelcmd}"
        cmds["Workflow"] = f"singularity exec {simage_path}/{feelpp} {pyfeelcmd}"
    else:
        cmds[
            "Workflow"
        ] = f"mpirun -np {NP} singularity exec {simage_path}/{feelpp} {pyfeelcmd}"

    # to be fixed
    # result_dir = f"{root_directory}/feelppdb/np_{NP}"
    # print(f"result_dir={result_dir}")

    return cmds
