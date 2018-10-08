import networkx as nx
import community


class DiffusionZone():
    def __init__(self, timeBar, polygonGDF, polygonTypeDict):
        self.__timeBar = timeBar
        self.__polygonGDF = polygonGDF
        self.__polygonTypeDict = polygonTypeDict
        self.__graph = nx.Graph()
        #######################################################################

        self.__calculateSimilarity()
        self.__partitionDict = community.best_partition(self.__graph)
        self.__polygonGDF["DZ"] = list(self.__partitionDict.values())




    def __calculateSimilarity(self):
        tLength = len(self.__timeBar)

        for polygonID1 in range(len(self.__polygonGDF)):
            for polygonID2 in range(polygonID1+1, len(self.__polygonGDF)):
                similarity = self.__calculateOnePairSimilarity(polygonID1, polygonID2)
                self.__graph.add_edge(polygonID1, polygonID2, weight=similarity)



    def __calculateOnePairSimilarity(self, polygonID1, polygonID2):
        count = 0
        for t in self.__timeBar:
            types1 = self.__polygonTypeDict[polygonID1][t]
            types2 = self.__polygonTypeDict[polygonID2][t]
            for oneType in types1:
                if oneType in types2:
                    count += 1
                    break

        similarity = float(count)/float(len(self.__timeBar))
        return similarity

    def getResult(self):
        return self.__polygonGDF
