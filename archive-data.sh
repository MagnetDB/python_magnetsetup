#! /bin/bash

# set -x # force debug
tar \
    --exclude=*.xao* \
    --exclude=*.brep* \
    --exclude=*.med* \
    --exclude=*.msh* \
    --exclude=*.hdf \
    --exclude=*.stl* \
    --exclude=\#*\# \
    --exclude=*~ \
    --exclude=*log* \
    --exclude=*.log \
    --exclude=*.py* \
    --exclude=*.h5 \
    --exclude=*.tgz \
    --exclude=*.orig \
    --exclude=*.png \
    --exclude=*.geo \
  -zcvf magnetdb-data.tgz data
