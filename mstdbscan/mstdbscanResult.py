
import pandas as pd
import geopandas as gpd
import numpy as np

from . import diffusionZone as ds

class MSTdbscanResult():
    def __init__(self, timeBar, pointGDF, points, allClusters, noiseOverTime):
        self.__timeBar = timeBar
        self.__pointGDF = pointGDF
        self.__points = points
        self.__allClusters = allClusters
        self.__noiseOverTime = noiseOverTime

        self.__clusterIDList = list(self.__allClusters.keys())
        self.__clusterIDList.sort()

        self.__clusterGDF = None
        self.__pointResultGDF = None

        #self.diffusionZoneGDF = None
        #self.polygonEvolutionGDF = None
        #self.temporalPolygonEvolutionGDF = None

        self.__polygonGDF = None
        self.__dateInfo = None
        self.__polygonTypeDict = None
        self.__polygonResultGDF = None

        self.__setResult()





    def __setResult(self):
        clusterDict = {"clusterID":[], "mstTime":[], "type":[], "centerX":[], "centerY":[], "shape":[]}
        pointDict = {"pointID":[], "mstTime":[], "role":[], "clusterID":[], "geometry":[]}

        for time in self.__noiseOverTime:
            currentNoise = self.__noiseOverTime[time]
            for point in currentNoise:
                 pointDict["pointID"].append(point)
                 pointDict["mstTime"].append(time)
                 pointDict["role"].append("noise")
                 pointDict["clusterID"].append(-1)
                 pointDict["geometry"].append(self.__points[point]["coordinate"])


        for clusterID in self.__allClusters:
            oneCluster = self.__allClusters[clusterID]
            orderedClusterID = self.__clusterIDList.index(clusterID)
            for t in self.__timeBar:
                center = oneCluster.getCenter(t)
                shape = oneCluster.getShape(t)

                if shape is None:
                    continue

                currentHistory = oneCluster.getHistory(t)

                types = [i[0] for i in currentHistory]
                theType = None

                if "SplitMerge" in types:
                    theType = "SplitMerge"
                elif "Merge" in types:
                    theType = "Merge"
                elif "Split" in types:
                    theType = "Split"
                else:
                    theType = types[0]


                clusterDict["clusterID"].append(orderedClusterID)
                clusterDict["mstTime"].append(t)
                clusterDict["type"].append(theType)
                clusterDict["centerX"].append(center.x)
                clusterDict["centerY"].append(center.y)
                clusterDict["shape"].append(shape)
                ###############################################################
                coreMember = oneCluster.getCoreMember(t)
                for point in coreMember:
                    pointDict["pointID"].append(point)
                    pointDict["mstTime"].append(t)
                    pointDict["role"].append("core")
                    pointDict["clusterID"].append(orderedClusterID)
                    pointDict["geometry"].append(self.__points[point]["coordinate"])


                borderMember = oneCluster.getBorderMember(t)
                for point in coreMember:
                    pointDict["pointID"].append(point)
                    pointDict["mstTime"].append(t)
                    pointDict["role"].append("border")
                    pointDict["clusterID"].append(orderedClusterID)
                    pointDict["geometry"].append(self.__points[point]["coordinate"])

                ###############################################################

        clusterDF = pd.DataFrame.from_dict(clusterDict)
        self.__clusterGDF = gpd.GeoDataFrame(clusterDF, geometry="shape")
        self.__clusterGDF.crs = self.__pointGDF.crs

        pointResultGDF = pd.DataFrame.from_dict(pointDict)
        self.__pointResultGDF = gpd.GeoDataFrame(pointResultGDF, geometry="geometry")
        pointDF = pd.DataFrame(self.__pointGDF)
        pointDF.drop("geometry", axis=1, inplace=True)
        self.__pointResultGDF = pd.merge(self.__pointResultGDF, pointDF, left_on="pointID", right_index=True)
        self.__pointResultGDF.crs = self.__pointGDF.crs
        #self.__pointGDF.reset_index(inplace=True)

    ###########################################################################

    def getClusteringResult(self):
        return (self.__allClusters, self.__noiseOverTime)

    @property
    def clusters(self):
        return self.__clusterGDF

    @property
    def points(self):
        return self.__pointResultGDF

    ###########################################################################
    # polygon-related analysis
    ###########################################################################
    def setPolygons(self, polygonGDF):
        if polygonGDF is None:
            raise ValueError("The input polygon cannot be None.")
        elif self.__polygonGDF is None or self.__polygonGDF != polygonGDF:
            self.__polygonGDF = polygonGDF
            self.__polygonResultGDF = None

            self.__getPolygonTypeDict()
            self.__getDZ()
            self.__getPE()
            self.__polygonResultGDF.crs = self.__polygonGDF.crs
        else:
            pass


    @property
    def polygons(self):
        if self.__polygonResultGDF is None:
            raise AttributeError("Please set the polygons first.")
        return self.__polygonResultGDF


    def __getPolygonTypeDict(self):
        self.__polygonTypeDict = {}
        for index in range(len(self.__polygonGDF)):
            temporalDict = {}
            for t in self.__timeBar:
                temporalDict[t] = []
            self.__polygonTypeDict[index] = temporalDict

        for clusterID in self.__allClusters:
            oneCluster = self.__allClusters[clusterID]
            orderedClusterID = self.__clusterIDList.index(clusterID)
            for t in self.__timeBar:
                center = oneCluster.getCenter(t)
                shape = oneCluster.getShape(t)

                if shape is None:
                    continue

                currentHistory = oneCluster.getHistory(t)

                types = [i[0] for i in currentHistory]
                theType = None

                if "SplitMerge" in types:
                    theType = "SplitMerge"
                elif "Merge" in types:
                    theType = "Merge"
                elif "Split" in types:
                    theType = "Split"
                else:
                    theType = types[0]


                ###############################################################
                isIntersect = self.__polygonGDF.intersects(shape)
                #polygonIDs = [i for i, x in enumerate(isIntersect) if x is True]

                for index in range(len(isIntersect)):
                    if isIntersect[index] and (theType not in self.__polygonTypeDict[index][t]):
                        self.__polygonTypeDict[index][t].append(theType)

    ###########################################################################

    def __getDZ(self):
        diffusionZone = ds.DiffusionZone(self.__timeBar, self.__polygonGDF, self.__polygonTypeDict)
        self.__polygonResultGDF = diffusionZone.getResult()


    def __getPE(self):
        fields = [str(t) for t in self.__timeBar]

        polygonEvolutionDict = []
        for index in range(len(self.__polygonGDF)):
            theTypes = []
            for t in self.__timeBar:
                types = self.__polygonTypeDict[index][t]

                theType = "no cluster"
                if "Emerge" in types or "Growth" in types or "Directional growth" in types or "Merge" in types:
                    theType = "increase"
                elif "Steady" in types or "Move" in types or "SplitMerge" in types:
                    theType = "keep"
                elif "Reduction" in types or "Directional reduction" in types or "Split" in types:
                    theType = "decrease"
                else:
                    theType = "no cluster"

                theTypes.append(theType)
            polygonEvolutionDict.append(theTypes)

        polygonEvolutionDF = pd.DataFrame(polygonEvolutionDict, columns=fields)
        self.__polygonResultGDF = pd.concat([self.__polygonGDF, polygonEvolutionDF], axis=1)
