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

    candidateInfo_list = []
    with open('../dataset/candidates.csv', 'r') as f:
        for row in list(csv.reader(f))[1:]:
            series_uid = row[0]

            if series_uid not in presentOnDisk_set and requireOnDisk_bool:
                continue

            isNodule_bool = bool(int(row[4]))
            candidateCenter_xyz = tuple([float(x) for x in row[1:4]])

            candidateDiameter_mm = 0.0
            for annotation_tup in diameter_dict.get(series_uid, []):
                annotationCenter_xyz, annotationDiameter_mm = annotation_tup
                for i in range(3):
                    delta_mm = abs(candidateCenter_xyz[i] - annotationDiameter_mm[i])
                    if delta_mm > annotationDiameter_mm / 4:
                        break
                    else:
                        candidateDiameter_mm = annotationDiameter_mm
                        break

                candidateInfo_list.append(CandidateInfoTuple(
                    isNodule_bool,
                    candidateDiameter_mm,
                    series_uid,
                    candidateCenter_xyz
                ))

            candidateInfo_list.sort(reverse=True)
            return candidateInfo_list