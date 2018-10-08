# -*- coding: utf-8 -*-
#python 3.6
import numpy as np
import math
import shapely.geometry as sg
from shapely.ops import cascaded_union


def calculateDistance(a,b):
    dis = ((a[0]-b[0])**2+(a[1]-b[1])**2)**0.5
    return dis

def getMeanCenter(xList, yList):
    xCenter = np.mean(xList)
    yCenter = np.mean(yList)
    return sg.Point(xCenter,yCenter)

def calBufferArea(polyBuffer):
    return polyBuffer.area

def createBuffer(x,y,radius):
    p = sg.Point(x,y)
    circle = p.buffer(radius,128)
    return circle

def dissolveBuffer(bufferList):
    poly = cascaded_union(bufferList)
    return poly

def shapefile2PolygonClass(aShapefile,fieldName):
    fields = aShapefile.fields[1:]
    field_names = [field[0] for field in fields]

    sr = aShapefile.shapeRecords()
    length = len(sr)

    attList=[None]*length
    polygonList = [None]*length
    for i in range(length):
        aShape = sg.Polygon((sr[i].shape.points))
        polygonList[i] = aShape
        att = dict(zip(field_names, sr[i].record))
        attList[i] = att[fieldName]
    numClass = set(attList)

    out = (zip(polygonList,attList),numClass)
    return out

def shapefile2PolygonList(aShapefile):
    fields = aShapefile.fields[1:]
    field_names = [field[0] for field in fields]

    sr = aShapefile.shapeRecords()
    length = len(sr)

    polygonList = [None]*length
    for i in range(length):
        aShape = sg.Polygon((sr[i].shape.points))
        att = dict(zip(field_names, sr[i].record))
        polygonList[i] = (sr[i],aShape,att)
    return polygonList

def pointInPolygon(x,y,polygonList):
    p = sg.Point(x,y)
    for i in range(len(polygonList)):
        if p.within(polygonList[i][1]):
            return i
