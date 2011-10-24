#!/usr/bin/python
# -*- coding: utf8 -*-
"""
Interface with roint's GAT file format.
Flávio J. Saraiva @ 2011-10-24 (Python 2.7.2)

Requires:
    roint (C shared library) (https://gitorious.org/open-ragnarok/roint)
"""
from ctypes import *


class ROGatCell(Structure):
    _pack_ = 1
    _fields_ = [
        ("height", c_float * 4),
        ("type", c_int)
    ]


class ROGat(Structure):
    _pack_ = 1
    _fields_ = [
        ("vermajor", c_ubyte),
        ("verminor", c_ubyte),
        ("width", c_uint),
        ("height", c_uint),
        ("cells", POINTER(ROGatCell))
    ]


class GAT:
    """Ground Altitude File."""

    def __init__ (self,fn=None):
        """Constructor."""
        self._gat = None
        roint = CDLL("roint")

        #self._loadFromData = roint.gat_loadFromData
        #self._loadFromData.argtypes = [POINTER(c_ubyte),c_uint]
        #self._loadFromData.restype = POINTER(ROGat)

        self._loadFromFile = roint.gat_loadFromFile
        self._loadFromFile.argtypes = [c_char_p]
        self._loadFromFile.restype = POINTER(ROGat)

        #self._loadFromGrf = roint.gat_loadFromGrf
        #self._loadFromGrf.argtypes = [POINTER(ROGrfFile)]
        #self._loadFromGrf.restype = POINTER(ROGat)

        self._unload = roint.gat_unload
        self._unload.argtypes = [POINTER(ROGat)]
        self._unload.restype = None

        self._gat = self._loadFromFile(fn);
        assert self._gat, "failed to load GAT"

    def __del__ (self):
        """Destructor."""
        if self._gat:
            self._unload(self._gat)

    def getVerMajor (self):
        return self._gat[0].vermajor

    def getVerMinor (self):
        return self._gat[0].verminor

    def getWidth (self):
        return self._gat[0].width

    def getHeight (self):
        return self._gat[0].height

    def getCell (self, i):
        assert i >= 0 and i < self.getWidth() * self.getHeight()
        return self._gat[0].cells[i]

    def getCells (self):
        return self._gat[0].cells[: self.getWidth() * self.getHeight()]
