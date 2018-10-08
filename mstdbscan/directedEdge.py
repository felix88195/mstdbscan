# -*- coding: utf-8 -*-
class DirectedEdge():
    def __init__(self, v, w):
        self.v = v
        self.w = w
        self.attribute = {}


    def getStart(self):
        return self.v

    def getEnd(self):
        return self.w

    def addAttribute(self, key, value):
        self.attribute[key] = value

    def getAttribute(self, key=None):
        if key is None:
            return self.attribute
        elif key in self.attribute:
            return self.attribute[key]
        else:
            return None
