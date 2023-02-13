import csv
import functools
import glob
import os

import numpy as np
import SimpleITK as sitk

from collections import namedtuple
from util import XyzTuple, xyz2irc


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


class Ct:
    def __init__(self, series_uid):
        mhd_path = glob.glob('../dataset/subset*/{}.mhd'.format(series_uid))[0]
        ct_mhd = sitk.ReadImage(mhd_path)
        ct_a = np.array(sitk.GetArrayFromImage(ct_mhd), dtype=np.float32)
        ct_a.clip(-1000, 1000, ct_a)

        self.series_uid = series_uid
        self.hu_a = ct_a

        self.origin_xyz = XyzTuple(*ct_mhd.GetOrigin())
        self.vxSize_xyz = XyzTuple(*ct_mhd.GetSpacing())
        self.direction_a = np.array(ct_mhd.GetDirection()).reshape(3, 3)

    def getRawCandidate(self, center_xyz, width_irc):
        center_irc = xyz2irc(
            center_xyz,
            self.origin_xyz,
            self.vxSize_xyz,
            self.direction_a
        )

        slice_list = []
        for axis, center_val in enumerate(center_irc):
            start_ndx = int(round(center_val - width_irc[axis]/2))
            end_ndx = int(start_ndx + width_irc[axis])
            slice_list.append(slice(start_ndx, end_ndx))

        ct_chunk = self.hu_a[tuple(slice_list)]
        return ct_chunk, center_irc