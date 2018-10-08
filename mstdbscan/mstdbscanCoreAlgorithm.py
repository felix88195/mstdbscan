# -*- coding: utf-8 -*-
#python 3.6
import math
import numpy as np
import os.path

from . import directedEdge as de
from . import edgeWeightedDigraph as ewd
from . import transmissionCluster as tc
from . import mstdbscanGear as gear
#from . import EdgeWeightedDigraphCC


###############################################################################


class MSTdbscanCoreAlgorithm():
    def __init__(self, timeBar, pointTimeDict, points, epsSpatial, epsTemporalLow, epsTemporalHigh, minPts, movingRatio=0.1, areaRatio=0.1):
        self.timeBar = timeBar
        self.pointTimeDict = pointTimeDict
        self.points = points
        self.EWD = ewd.EdgeWeightedDigraph()

        self.epsSpatial = epsSpatial
        self.epsTemporalLow = epsTemporalLow
        self.epsTemporalHigh = epsTemporalHigh
        self.minPts = minPts
        self.moveDistance = epsSpatial*movingRatio
        self.areaRatio = areaRatio

        self.allClusters = {}
        self.liveClusters = {}
        self.noiseOverTime = {}
        self.currentDataset = [] #dataset for clustering

        #######################################################################

        for t in self.timeBar:
            # get the points appearing at time t
            newPoints = []
            if t in self.pointTimeDict:
                newPoints = self.pointTimeDict[t]
                for pointID in newPoints:
                    self.EWD.addNode(pointID, self.points[pointID])
                    self.EWD.enable(pointID)

            # disable died points
            diedPoints = []
            diedTime = t - self.epsTemporalHigh - 1
            if diedTime in self.pointTimeDict:
                diedPoints = self.pointTimeDict[diedTime]

            for pointID in diedPoints:
                self.EWD.disable(pointID)
                self.currentDataset.remove(pointID)

            # update information for existing points
            for pointID in self.currentDataset:
                self.__updateOnePointInfo(pointID, newPoints)

            # update information for new points if needed
            if self.epsTemporalLow == 0:
                for pointID in newPoints:
                    self.__updateOnePointInfo(pointID, newPoints)

            self.currentDataset += newPoints


            ###################################################################
            # splitting live clusters  first

            splitInfo = self.EWD.splitting(self.currentDataset, list(self.liveClusters.keys()))

            # check the parents for border point and noise point
            for nodeID in self.EWD.node:
                #role = self.EWD.getRole(nodeID)
                #if role == "border"or role == "noise":
                self.EWD.checkNonCoreParents(nodeID)

            #print ("splitInfo")
            #print (splitInfo)
            ###################################################################
            #start to clustering
            self.clusterEWD, currentClusters, noises = self.EWD.clustering(self.currentDataset)
            self.noiseOverTime[t] = noises

            # record cluster result
            #print ("currentClusters")
            #print (currentClusters)
            for clusterID in currentClusters:
                if clusterID not in self.liveClusters: # may be new cluster
                    newTransmissionCluster = tc.TransmissionCluster(clusterID)
                    self.liveClusters[clusterID] = newTransmissionCluster

                coreMember = currentClusters[clusterID]["coreMember"]
                borderMember = currentClusters[clusterID]["borderMember"]

                buffers = []
                xList = []
                yList = []
                for nodeID in coreMember:
                    buffers.append(self.points[nodeID]["buffer"])
                    xList.append(self.points[nodeID]["coordinate"].x)
                    yList.append(self.points[nodeID]["coordinate"].y)

                for nodeID in borderMember:
                    xList.append(self.points[nodeID]["coordinate"].x)
                    yList.append(self.points[nodeID]["coordinate"].y)

                shape = gear.dissolveBuffer(buffers)
                center = gear.getMeanCenter(xList, yList)

                self.liveClusters[clusterID].updateAllInfo(t, coreMember, borderMember, center, shape)


            ###################################################################
            # record interaction type
            for parent in splitInfo:
                oneClusterSplit = splitInfo[parent]
                if len(oneClusterSplit) == 0:
                    finalID = self.__recursivelyFindClusterCombination(parent)
                    #disappear
                    if finalID == parent:
                        self.liveClusters[parent].addHistory(t, parent, "Disappear")
                    # merge to other cluster
                    else:
                        self.__recordInteractionPattern(t, parent, finalID, "Merge")

                    self.allClusters[parent] = self.liveClusters.pop(parent)

                elif len(oneClusterSplit) == 1:
                    #single cluster evolution or merge others
                    if parent in currentClusters:
                        pass

                    # merge to other cluster
                    else:
                        finalID = self.__recursivelyFindClusterCombination(parent)
                        self.__recordInteractionPattern(t, parent, finalID, "Merge")

                        self.allClusters[parent] = self.liveClusters.pop(parent)

                else:
                    if parent not in currentClusters:
                        newParent = self.__changeInheritParent(oneClusterSplit, currentClusters)

                        # cluster is splitted out
                        if newParent is None:
                            for subclusterID in oneClusterSplit:
                                finalID = self.__recursivelyFindClusterCombination(subclusterID)
                                self.__recordInteractionPattern(t, parent, finalID, "Split")
                            self.allClusters[parent] = self.liveClusters.pop(parent)
                            continue

                        # successfully change parent
                        else:
                            parent = newParent
                    else:
                        pass


                    #oneClusterSplit.remove(parent)

                    for subclusterID in oneClusterSplit:
                        if subclusterID == parent:
                            continue
                        elif subclusterID in currentClusters:
                            self.__recordInteractionPattern(t, parent, subclusterID, "Split")

                        else:
                            finalID = self.__recursivelyFindClusterCombination(subclusterID)
                            if finalID == parent:
                                continue
                            else:
                                #print (self.clusterEWD.node)
                                self.__recordInteractionPattern(t, parent, finalID, "Split")

            ###################################################################
            # record single pattern and merge-split
            invalidClusters = []
            for parent in self.liveClusters:

                if parent not in currentClusters:
                    invalidClusters.append(parent)
                    continue

                currentHistory = self.liveClusters[parent].getHistory(t)
                if currentHistory is None:
                    self.__recordSinglePattern(t, parent)
                else:
                    interactionPattern = self.__checkInteractionPattern(currentHistory)
                    if interactionPattern is None:
                        continue
                    else:
                        self.liveClusters[parent].addHistory(t, parent, interactionPattern)


            # remove died clusters
            for parent in invalidClusters:
                self.liveClusters[parent].addHistory(t, parent, "Disappear")
                self.allClusters[parent] = self.liveClusters.pop(parent)


            ###################################################################
            # shift liveClusters to allClusters at the last time
            if t == self.timeBar[-1]:
                parents = list(self.liveClusters.keys())
                for parent in parents:
                    self.allClusters[parent] = self.liveClusters.pop(parent)





    ###########################################################################
    def __survive(self, pointTime, t):
        if t-pointTime > self.epsTemporalHigh:
            return False
        else:
            return True


    def __updateOnePointInfo(self, pointID, newPoints):
        neighbors = self.points[pointID]["neighbors"]
        for newPointID in newPoints:
            if newPointID in neighbors:
                e = de.DirectedEdge(pointID, newPointID)
                self.EWD.addEdge(e)

        if len(self.EWD.adj[pointID]) >= self.minPts:
            self.EWD.setRole(pointID, "core")


    def __recursivelyFindClusterCombination(self, clusterID):
        if clusterID not in self.clusterEWD.adj:
            return clusterID
        else:
            neighbors = list(self.clusterEWD.adj[clusterID].keys())
            if len(neighbors) > 1:
                raise NameError("more then one edge !!")
            elif len(neighbors) == 1:
                return self.__recursivelyFindClusterCombination(neighbors[0])
            else:
                return clusterID


    def __changeInheritParent(self, candidates, currentClusters):
        inheritID = None
        inheritCount = 0
        for subclusterID in candidates:
            if subclusterID in currentClusters:
                coreMember = currentClusters[subclusterID]["coreMember"]
                borderMember = currentClusters[subclusterID]["borderMember"]
                memberCount = len(coreMember) + len(borderMember)
                if memberCount > inheritCount:
                    inheritID = subclusterID
                    inheritCount = memberCount

        parent = inheritID
        return parent


    def __recordInteractionPattern(self, t, fromID, toID, theType):
        self.liveClusters[fromID].addHistory(t, toID, theType+"To")
        self.liveClusters[toID].addHistory(t, fromID, theType+"From")

    def __checkInteractionPattern(self, currentHistory):
        types = [i[0] for i in currentHistory]

        if "MergeTo" in types:
            return "Merge"

        elif "MergeFrom" in types:
            if "SplitTo" in types:
                return "SplitMerge"
            else:
                return "Merge"

        elif "SplitFrom" in types:
            if "SplitTo" in types:
                return "SplitMerge"
            else:
                return "Split"

        elif "SplitTo" in types:
            return "Split"

        else:
            return None



    def __recordSinglePattern(self, t, clusterID):
        theCluster = self.liveClusters[clusterID]
        lastTime = t-1


        oldCenter = theCluster.getCenter(lastTime)
        oldShape = theCluster.getShape(lastTime)

        if oldCenter is None:
            self.liveClusters[clusterID].addHistory(t, clusterID, "Emerge")
        else:
            newCenter = theCluster.getCenter(t)
            newShape = theCluster.getShape(t)
            theType = self.__decideSinglePattern(oldCenter, oldShape, newCenter, newShape)
            self.liveClusters[clusterID].addHistory(t, clusterID, theType)

    def __decideSinglePattern(self, oldCenter, oldShape, newCenter, newShape):
        distance = oldCenter.distance(newCenter)
        areaChange = (newShape.area - oldShape.area)/oldShape.area
        areaChangeAbs = np.abs(areaChange)

        isMove = False
        if distance >= self.moveDistance:
            isMove = True

        theType = ""
        if areaChangeAbs >= self.areaRatio:
            if areaChange > 0:
                if isMove:
                    theType = "Directional growth"
                else:
                    theType = "Growth"
            else:
                if isMove:
                    theType = "Directional reduction"
                else:
                    theType = "Reduction"
        else:
            if isMove:
                theType = "Move"
            else:
                theType = "Steady"

        return theType




    ###########################################################################
    def getResult(self):
        return {"allClusters": self.allClusters, "noiseOverTime": self.noiseOverTime}
