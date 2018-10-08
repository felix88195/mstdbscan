# -*- coding: utf-8 -*-
import copy

class WeightedQuickUnionDictionary():
    def __init__(self, nodes):
        self.nodes = nodes
        self.individualN = len(nodes)
        self.reset()

    def reset(self):
        self.nodeInfo = {}
        for i in self.nodes:
            self.nodeInfo[i] = {"parents":[i], "size":1}

        self.clusterN = self.individualN
        self.ccDict = {}


    def findParents(self, nodeID):
        parents = copy.copy(self.nodeInfo[nodeID]["parents"])
        for i in range(len(parents)):
            parents[i] = self.__findOneParent(parents[i])
        self.nodeInfo[nodeID]["parents"] = list(set(parents))

        return parents


    def __findOneParent(self, nodeID):
        i = nodeID
        while (i not in self.nodeInfo[i]["parents"]):
            i = self.nodeInfo[i]["parents"][0]
        self.nodeInfo[nodeID]["parents"][0] = i

        return i


    def isConnected(self, p, q):
        if set(self.__findParent(p)).isdisjoint(set(self.__findParent(q))):
            return False
        else:
            return True

    def unionCores(self, p, q):
        parentsP = self.findParents(p)
        parentsQ = self.findParents(q)

        if len(parentsP) > 1:
            raise NameError("parents P is larger than 1 !!")

        if len(parentsQ) > 1:
            raise NameError("parents Q is larger than 1 !!")

        parentP = parentsP[0]
        parentQ = parentsQ[0]

        if parentP == parentQ:
            return

        if self.nodeInfo[parentP]["size"] < self.nodeInfo[parentQ]["size"]:  # prefer P as parent, but if Q is bigger than Q become parent
            self.nodeInfo[parentP]["parents"][0] = parentQ
            self.nodeInfo[parentQ]["size"] += self.nodeInfo[parentP]["size"]

        else:
            self.nodeInfo[parentQ]["parents"][0] = parentP
            self.nodeInfo[parentP]["size"] += self.nodeInfo[parentQ]["size"]

        self.clusterN = self.clusterN-1



    def unionCoreBorder(self, p ,q):
        parentsP = self.findParents(p)
        parentsQ = self.findParents(q)

        if len(parentsP) > 1:
            raise NameError("parents P is larger than 1 !!")

        parentP = parentsP[0]

        if len(parentsQ) == 1:

            if parentP == parentsQ[0]:
                return

            # core union new border
            if q == parentsQ[0]:
                self.nodeInfo[q]["parents"][0] = parentP
            # core union old border who has only one parent
            else:

                self.nodeInfo[q]["parents"].append(parentP)
        else:
            for i in parentsQ:
                if i == parentP:
                    return

            # core union old border who has multiple parents
            self.nodeInfo[q]["parents"].append(parentP)

        self.nodeInfo[parentP]["size"] += self.nodeInfo[q]["size"]

        '''
        if q in parentsQ:
            self.nodeInfo[q]["parents"][0] = parentP
            self.clusterN = self.clusterN-1
        else:
            for i in parentsQ:
                if i == parentP:
                    return

            self.nodeInfo[q]["parents"].append(parentP)

        self.nodeInfo[parentP]["size"] += self.nodeInfo[q]["size"]
        '''



    def getClusterNumber(self):
        return self.clusterN

    def getCC(self):
        self.ccDict = {}
        for nodeID in self.nodes:
            parents = self.findParents(nodeID)
    
            for parent in parents:
                if parent not in self.ccDict:
                    self.ccDict[parent] = []
                self.ccDict[parent].append(nodeID)

        return self.ccDict

    def getNodesInfo(self):
        for nodeID in self.nodes:
            self.findParents(nodeID)

        return self.nodeInfo
