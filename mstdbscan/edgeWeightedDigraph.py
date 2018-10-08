# -*- coding: utf-8 -*-
import copy
from . import directedEdge as de
from . import weightedQuickUnionDictionary as wqud
#from ..DataStructure import WeightedQuickUnionDictionary as wqud

class EdgeWeightedDigraph():
    def __init__(self):
        self.nodeNumber = 0
        self.maxNodeID = 0
        self.node = {}
        self.__node = {}
        self.adj = {}
        #self.live = [False]*n
        #self.role = [None]*n

    def addNode(self, nodeID, dict=None):
        if nodeID not in self.node:
            self.node[nodeID] = {}
            self.__node[nodeID] = {"live":False, "role":"noise", "marked":False, "edgeTo":nodeID, "parents":[nodeID], "size":1}
            self.adj[nodeID] = {}
            self.nodeNumber += 1

        if not dict is None:
            self.node[nodeID].update(dict)

    def getNode(self, v=None):
        if v is None:
            return self.node
        elif v in self.node:
            return self.node[v]
        else:
            return None

    def getMetaNode(self, v=None):
        if v is None:
            return self.__node
        elif v in self.__node:
            return self.__node[v]
        else:
            return None

    def removeNode(self, v):
        if v in node:
            self.nodeNumber -= 1
            self.node.pop(v)
            self.__node.pop(v)
            self.adj.pop(v)
            for nodeID in self.adj:
                self.removeEdge(nodeID, v)

    def addNodeOneAttribute(self, nodeID, key, value):
        self.node[nodeID][key] = value

    def addNodeMultipleAttributes(self, nodeID, dict):
        self.node[nodeID].update(dict)

    ###########################################################################

    def addEdge(self, e):
        v = e.getStart()
        w = e.getEnd()

        self.addNode(v)
        self.addNode(w)

        if w not in self.adj[v]:
            self.adj[v][w] = e

    def getEdge(self, v, w):
        return self.adj[v][w]

    def removeEdge(self, v, w):
        self.adj[v].pop(w)

    def removeAllEdges(self):
        self.adj = {}

    ###########################################################################
    def setRole(self, v, value):
        self.__node[v]["role"] = value
        if value == "core":
            self.checkCoreParents(v)

    def getRole(self, v):
        return self.__node[v]["role"]

    def setParents(self, v, theList):
        self.__node[v]["parents"] = theList

    def appendOneParent(self, v, value):
        self.__node[v]["parents"].append(value)

    def removeOneParent(self, v, value):
        if value in self.__node[v]["parents"]:
            self.__node[v]["parents"].remove(value)

    def getParents(self, v):
        return copy.copy(self.__node[v]["parents"])

    def checkParents(self, v):
        role = self.__node[v]["role"]
        parents = self.getParents(v)
        if role == "core":
            if len(parents) > 1:
                sizes = [self.__node[i]["size"] for i in parents]
                self.__node[v]["parents"] = [parents[sizes.index(max(sizes))]]
            else:
                pass

        else:
            if len(parents) == 0:
                self.__node[v]["parents"].append(v)

    def checkCoreParents(self, v):
        if self.__node[v]["role"] == "core":
            parents = self.getParents(v)
            if len(parents) > 1:
                sizes = [self.__node[i]["size"] for i in parents]
                self.__node[v]["parents"] = [parents[sizes.index(max(sizes))]]

    def checkNonCoreParents(self, v):
        role = self.__node[v]["role"]
        if role == "border" or role == "noise":
            parents = self.getParents(v)
            if len(parents) == 0:
                self.__node[v]["parents"].append(v)


    def setSize(self, v, value):
        self.__node[v]["size"] = value

    def getSize(self, v):
        return self.__node[v]["size"]

    def setMarked(self, v, value):
        self.__node[v]["marked"] = value

    def getMarked(self, v):
        return self.__node[v]["marked"]

    def enable(self, v):
        self.__node[v]["live"] = True

    def disable(self, v):
        self.__node[v]["live"] = False
        self.__node[v]["marked"] = False
        parents = self.__findParents(v)
        for parent in parents:
            self.__node[parent]["size"] -= 1

    def isLive(self, v):
        return self.__node[v]["live"]

    ############################################################################

    def copy(self):
        return copy.deepcopy(self)


    def getSubgraph(self, partIDs):
        allIDs = list(self.node.keys())
        newGraph = self.copy()

        for nodeID in allIDs:
            if nodeID not in partIDs:
                newGraph.removeNode(nodeID)

        return newGraph


    ###########################################################################
    # spliting for MST_DBSCAN

    def splitting(self, liveNodes, clusterIDs):
        clusterSplitDict = {}
        for nodeID in liveNodes:
            parents = self.__node[nodeID]["parents"]
            for parent in parents:
                if parent in clusterIDs:
                    if parent not in clusterSplitDict:
                        clusterSplitDict[parent] = {"member":[], "subclusters":{}}
                    clusterSplitDict[parent]["member"].append(nodeID)

        #print ("clusterSplitDict")
        #print (clusterSplitDict)

        splitInfo = {}
        for parent in clusterSplitDict:
            member = clusterSplitDict[parent]["member"]
            member.sort()
            self.splitWQUD = wqud.WeightedQuickUnionDictionary(member)

            self.__dfs4splitting(member, parent)

            #clusterSplitDict[parent]["subclusters"] = self.splitWQUD.getCC()

            subclusters = self.splitWQUD.getCC()

            splitInfo[parent] = self.__getSplitInfo(parent, subclusters)


        return splitInfo


    def __dfs4splitting(self, members, parent):
        for i in members:
            self.__node[i]["marked"] = False

        for nodeID in members:
            if (self.__node[nodeID]["role"] == "core" and not self.__node[nodeID]["marked"]):
                self.__node[nodeID]["marked"] = True
                self.__recursiveDFS4splitting(nodeID, parent)


    def __recursiveDFS4splitting(self, nodeID, parent):
        for neighborID in self.adj[nodeID]:

            if not self.__node[neighborID]["live"]:
                continue

            if parent not in self.__node[neighborID]["parents"]:
                continue

            neighborRole = self.__node[neighborID]["role"]

            if not self.__node[neighborID]["marked"]:
                self.__node[neighborID]["marked"] = True
                self.__node[neighborID]["edgeTo"] = nodeID

                if neighborRole == "core":
                    self.splitWQUD.unionCores(nodeID, neighborID)
                    self.__recursiveDFS4splitting(neighborID, parent)
                else:
                    self.splitWQUD.unionCoreBorder(nodeID, neighborID)

            else:
                # meet core, merge
                if neighborRole == "core":
                    self.splitWQUD.unionCores(nodeID, neighborID)
                # meet border, stop
                else:
                    self.splitWQUD.unionCoreBorder(nodeID, neighborID)

    def __getSplitInfo(self, parent, subclusters):
        # fine the inherit ID
        inheritID = None
        inheritCount = 0
        validClusterIDs = []
        for subclusterID in subclusters:
            member = subclusters[subclusterID]

            if len(member) == 1 and not self.__node[member[0]]["marked"]:
                self.removeOneParent(member[0], parent)
                self.setSize(member[0], 1)
                continue
            else:
                validClusterIDs.append(subclusterID)

                memberCount = len(member)
                if memberCount > inheritCount:
                    inheritID = subclusterID
                    inheritCount = memberCount
                else:
                    continue

        if inheritID is None:
            return []

        # change parent to inherit ID if needed
        if parent in subclusters and parent in validClusterIDs:
            pass
        else:
            subclusters[parent] = subclusters.pop(inheritID)
            validClusterIDs[validClusterIDs.index(inheritID)] = parent

        # reset parents for the points which do not inherit parent
        for subclusterID in validClusterIDs:
            member = subclusters[subclusterID]
            self.setSize(subclusterID, len(member))

            if subclusterID == parent:
                continue
            else:
                for nodeID in member:
                    if self.getRole(nodeID) == "core":
                        self.setParents(nodeID, [subclusterID])
                    else:
                        self.removeOneParent(nodeID, parent)
                        self.appendOneParent(nodeID, subclusterID)

        return validClusterIDs

    ###########################################################################
    #clustering for MST_DBSCAN

    def clustering(self, liveNodes):
        liveNodes.sort()

        self.mergeEWD = EdgeWeightedDigraph()

        # start DFS
        self.__dfs(liveNodes)

        # record the result of DFS
        currentClusters = {}
        noises = []
        for nodeID in liveNodes:
            if not self.__node[nodeID]["marked"]:
                self.__node[nodeID]["role"] = "noise"

            role = self.__node[nodeID]["role"]
            if role == "noise":
                noises.append(nodeID)
                continue

            parents = self.__findParents(nodeID)
            #parents = self.__node[nodeID]["parents"]

            for parent in parents:
                if parent not in currentClusters:
                    currentClusters[parent] = {"coreMember":[], "borderMember":[]}

                if role == "core":
                    currentClusters[parent]["coreMember"].append(nodeID)
                else:
                    currentClusters[parent]["borderMember"].append(nodeID)

        return (self.mergeEWD, currentClusters, noises)


    def __dfs(self, liveNodes):
        for i in liveNodes:
            self.__node[i]["marked"] = False

        for nodeID in liveNodes:
            if (self.__node[nodeID]["role"] == "core" and not self.__node[nodeID]["marked"]):
                self.__node[nodeID]["marked"] = True
                parents = self.__findParents(nodeID)
                for parent in parents:
                    self.mergeEWD.addNode(parent)
                self.__recursiveDFS(nodeID)


    def __recursiveDFS(self, nodeID):
        for neighborID in self.adj[nodeID]:
            if not self.isLive(neighborID):
                continue

            neighborRole = self.__node[neighborID]["role"]

            if not self.__node[neighborID]["marked"]:
                self.__node[neighborID]["marked"] = True
                self.__node[neighborID]["edgeTo"] = nodeID

                if neighborRole == "core":
                    self.__unionCores(nodeID, neighborID)
                    self.__recursiveDFS(neighborID)
                else:
                    self.__node[neighborID]["role"] = "border"
                    self.__unionCoreBorder(nodeID, neighborID)

            else:
                # meet core, merge
                if neighborRole == "core":
                    self.__unionCores(nodeID, neighborID)
                # meet border, stop
                else:
                    self.__unionCoreBorder(nodeID, neighborID)


    def __findParents(self, nodeID):
        #parents = self.__node[nodeID]["parents"]
        parents = self.getParents(nodeID)

        for i in range(len(parents)):
            parents[i] = self.__findOneParent(parents[i])

        self.__node[nodeID]["parents"] = list(set(parents))

        return parents


    def __findOneParent(self, nodeID):
        i = nodeID
        while (i not in self.__node[i]["parents"]):
            i = self.__node[i]["parents"][0]
        self.__node[nodeID]["parents"][0] = i

        return i


    def __isConnected(self, p, q):
        if set(self.__findParent(p)).isdisjoint(set(self.__findParent(q))):
            return False
        else:
            return True

    def __unionCores(self, p, q):
        parentsP = self.__findParents(p)
        parentsQ = self.__findParents(q)

        if len(parentsP) > 1:
            raise NameError("parents P is larger than 1 !!")

        if len(parentsQ) > 1:
            raise NameError("parents Q is larger than 1 !!")

        parentP = parentsP[0]
        parentQ = parentsQ[0]

        if parentP == parentQ:
            return

        if self.__node[parentP]["size"] < self.__node[parentQ]["size"]:  # prefer P as parent, but if Q is bigger than Q become parent
            self.__node[parentP]["parents"][0] = parentQ
            self.__node[parentQ]["size"] += self.__node[parentP]["size"]
            self.__recordCombine(parentP, parentQ)

        else:
            self.__node[parentQ]["parents"][0] = parentP
            self.__node[parentP]["size"] += self.__node[parentQ]["size"]
            self.__recordCombine(parentQ, parentP)



    def __unionCoreBorder(self, p ,q):

        parentsP = self.__findParents(p)
        parentsQ = self.__findParents(q)

        if len(parentsP) > 1:
            raise NameError("parents P is larger than 1 !!")

        parentP = parentsP[0]

        if len(parentsQ) == 1:

            if parentP == parentsQ[0]:
                return

            # core union new border
            if q == parentsQ[0]:
                self.__node[q]["parents"][0] = parentP
                self.__recordCombine(q, parentP)

            # core union old border who has only one parent
            else:

                self.__node[q]["parents"].append(parentP)
        else:
            for i in parentsQ:
                if i == parentP:
                    return

            # core union old border who has multiple parents
            self.__node[q]["parents"].append(parentP)

        self.__node[parentP]["size"] += self.__node[q]["size"]



        '''
        if q in parentsQ:
            self.__node[q]["parents"][0] = parentP
            self.__recordCombine(q, parentP)

        else:
            for i in parentsQ:
                if i == parentP:
                    return

            self.__node[q]["parents"].append(parentP)

        self.__node[parentP]["size"] += self.__node[q]["size"]
        '''




    def __recordCombine(self, clusterID1, clusterID2):
        e = de.DirectedEdge(clusterID1, clusterID2)
        self.mergeEWD.addEdge(e)
