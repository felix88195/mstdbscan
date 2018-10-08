
import pandas as pd
import geopandas as gpd
from scipy import spatial
import shapely.geometry as sg

import sys
sys.setrecursionlimit(10000)

from . import mstdbscanCoreAlgorithm as mstca
from . import mstdbscanResult as mstre

import time

class MSTdbscan():
    def __init__(self, pointGDF, tTitle="intTime"):
        self.__pointGDF = pointGDF
        self.__pointNumber = len(pointGDF)
        self.__tTitle = tTitle

        self.__kdtree = None

        self.__timeBar = []
        self.__pointTimeDict = {}
        self.__points = [None]*self.__pointNumber

        self.__allClusters = None
        self.__noiseOverTime = None
        self.__result = None

        self.__epsSpatial = None
        self.__epsTemporalLow = None
        self.__epsTemporalHigh = None
        self.__minPts = None
        self.__movingRatio = None
        self.__areaRatio = None

        self.__parametersSetted = False

        #######################################################################

        self.__pointGDF.sort_values(by=self.__tTitle, inplace=True)
        self.__pointGDF.reset_index(inplace=True)

        for index, row in self.__pointGDF.iterrows():
            #coord = sg.Point(float(row[self.__xTitle]), float(row[self.__yTitle]))
            coord = row.geometry
            time = float(row[self.__tTitle])

            dict = {"coordinate":coord, "time":time, "shape":None, "clusterID":index, "neighbors":[]}
            self.__points[index] = dict

            if not time in self.__pointTimeDict:
                self.__pointTimeDict[time] = []
                self.__timeBar.append(time)
            self.__pointTimeDict[time].append(index)

        self.__timeBar = range(int(min(self.__timeBar)),int(max(self.__timeBar))+1)
        points = [i["coordinate"].coords[0] for i in self.__points]
        self.__kdtree = spatial.cKDTree(points)

    def __isTemporalNeighbor(self, pointID, neighborID):
        t1 = self.__points[pointID]["time"]
        t2 = self.__points[neighborID]["time"]
        diff = t2-t1
        return (diff <= self.__epsTemporalHigh and diff >= self.__epsTemporalLow)

    def setParams(self, epsSpatial, epsTemporalLow, epsTemporalHigh, minPts, movingRatio=0.1, areaRatio=0.1):
        self.__epsSpatial = epsSpatial
        self.__epsTemporalLow = epsTemporalLow
        self.__epsTemporalHigh = epsTemporalHigh
        self.__minPts = minPts
        self.__movingRatio = movingRatio
        self.__areaRatio = areaRatio
        #self.spatialPairs = self.__kdtree.query_pairs(__epsSpatial)

        allSpatialNeighbors = self.__kdtree.query_ball_tree(self.__kdtree, epsSpatial)

        for pointID in range(self.__pointNumber):
            p = self.__points[pointID]["coordinate"]
            circle = p.buffer(self.__epsSpatial,128)
            self.__points[pointID]["buffer"] = circle

            spatialNeighbors = allSpatialNeighbors[pointID]

            for neighborID in spatialNeighbors:
                if neighborID == pointID:
                    continue

                if self.__isTemporalNeighbor(pointID, neighborID):
                    self.__points[pointID]["neighbors"].append(neighborID)

        self.__allClusters = None
        self.__noiseOverTime = None

        self.__parametersSetted = True


    def run(self):
        if not self.__parametersSetted:
            raise NameError("Please reset the parameters first!")

        # implement MST-DBSCAN
        start = time.time()
        MSTCA = mstca.MSTdbscanCoreAlgorithm(self.__timeBar, self.__pointTimeDict,\
        self.__points, self.__epsSpatial, self.__epsTemporalLow, self.__epsTemporalHigh,\
        self.__minPts, self.__movingRatio, self.__areaRatio)
        print ('core algorithm costs',"--- %s seconds ---" % (time.time() - start))

        MSTDBSCAN_Result = MSTCA.getResult()

        self.__storeResult(MSTDBSCAN_Result)


    def __storeResult(self, MSTDBSCAN_Result):
        self.__result = mstre.MSTdbscanResult(self.__timeBar,\
        self.__pointGDF, self.__points,\
        MSTDBSCAN_Result["allClusters"], MSTDBSCAN_Result["noiseOverTime"])


    ###########################################################################
    @property
    def result(self):
        if self.__result is None:
            raise ValueError("The result is None! Please implement 'run' function first.")
        else:
            return self.__result
