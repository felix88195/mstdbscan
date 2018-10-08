


class TransmissionCluster():
    def __init__(self,ID):
        self.ID = ID
        self.history = {}

        self.coreMember = {}
        self.borderMember = {}
        self.center = {}
        self.shape = {}


    def addHistory(self,t,cid,theType):
        if t in self.history:
            self.history[t].append((theType, cid))
        else:
            self.history[t] = [(theType, cid)]

    def addCoreMember(self, t, coreMembers):
        self.coreMember[t] = coreMembers

    def addBorderMember(self, t, borderMembers):
        self.borderMember[t] = borderMembers

    def addCenter(self, t, theCenter):
        self.center[t] = theCenter

    def addShape(self, t, theShape):
        self.shape[t] = theShape

    def updateAllInfo(self, t, coreMembers, borderMembers, theCenter, theShape):
        self.coreMember[t] = coreMembers
        self.borderMember[t] = borderMembers
        self.center[t] = theCenter
        self.shape[t] = theShape

    #########################################################################
    def getHistory(self, t=None):
        if t is None:
            return self.history
        elif t in self.history:
            return self.history[t]
        else:
            return None

    def getCoreMember(self, t=None):
        if t is None:
            return self.coreMember
        elif t in self.coreMember:
            return self.coreMember[t]
        else:
            return None

    def getBorderMember(self, t=None):
        if t is None:
            return self.borderMember
        elif t in self.borderMember:
            return self.borderMember[t]
        else:
            return None

    def getCenter(self, t=None):
        if t is None:
            return self.center
        elif t in self.center:
            return self.center[t]
        else:
            return None

    def getShape(self, t=None):
        if t is None:
            return self.shape
        elif t in self.shape:
            return self.shape[t]
        else:
            return None
