import csv
import functools
import glob
import os
from collections import namedtuple


CandidateInfoTuple = namedtuple(
    'CandidateInfoTuple',
    'isNodule_bool, diameter_mm, series_uid, center_xyz',
)

@functools.lru_cache(1) # standard library in memory caching
def getCandidateInfoList(requireOnDisk_bool=True):
    mhd_list = glob.glob('../dataset/subset*/*.mhd') # list all .mhd file
    presentOnDisk_set = {os.path.split(p)[-1][:-4] for p in mhd_list} # get filename

    diameter_dict = {}
    with open('../dataset/annotations.csv', 'r') as f: # open csv file
        for row in list(csv.reader(f))[1:]: # iterate through csv file except column name
            series_uid = row[0]
            annotationCenter_xyz = tuple([float(x) for x in row[1:4]]) 
            annotationDiameter_mm = float(row[4])

            diameter_dict.setdefault(series_uid, []).append(
                (annotationCenter_xyz, annotationDiameter_mm)
            )