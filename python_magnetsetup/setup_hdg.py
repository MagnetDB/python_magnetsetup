#############################
# Create JSON file for HDG
#############################


def json_hdg():

    with open(yamlfile, 'r') as cfgdata:
        cad = yaml.load(cfgdata, Loader = yaml.FullLoader)
        if isinstance(cad, Insert):
            (NHelices, NRings, NChannels, Nsections, index_h, 
                R1, R2, Z1, Z2, Zmin, Zmax, Dh, Sh) = python_magnetgeo.get_main_characteristics(cad)
        else:
            raise Exception("expected Insert yaml file")

    # TODO : manage the scale
    for i in range(len(Zmin)): Zmin[i] *= args.scale
    for i in range(len(Zmax)): Zmax[i] *= args.scale
    for i in range(len(Dh)): Dh[i] *= args.scale
    for i in range(len(Sh)): Sh[i] *= args.scale

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

    part_withoutAir = []  # list of name of all parts without Air
    for i in range(NHelices):
        for j in range(Nsections[i]+2):
            part_withoutAir.append("H{}_Cu{}".format(i+1,j))
    for i in range(1,NRings+1):
        part_withoutAir.append("R{}".format(i))

    boundary_Ring = [] # list of name of boundaries of Ring for elastic part
    for i in range(1,NRings+1):
        if i % 2 == 1 :
            boundary_Ring.append("R{}_BP".format(i))
        else :
            boundary_Ring.append("R{}_HP".format(i))

    return {}