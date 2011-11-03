#!/usr/bin/python
# -*- coding: utf8 -*-
"""
Interface with roint's GND file format.
Flávio J. Saraiva @ 2011-10-24 (Python 2.7.2)

Requires:
    roint (C shared library) (https://gitorious.org/open-ragnarok/roint)
"""
from ctypes import *


class ROGndCell(Structure):
    _pack_ = 1
    _fields_ = [
        ("height", c_float * 4),
        ("topSurfaceId", c_int),
        ("frontSurfaceId", c_int),
        ("rightSurfaceId", c_int)
    ]


class ROGndColor(Structure):
    _pack_ = 1
    _fields_ = [
        ("b", c_ubyte),
        ("g", c_ubyte),
        ("r", c_ubyte),
        ("a", c_ubyte)
    ]


class ROGndSurface(Structure):
    _pack_ = 1
    _fields_ = [
        ("u", c_float * 4),
        ("v", c_float * 4),
        ("textureId", c_short),
        ("lightmapId", c_short),
        ("color", ROGndColor)
    ]


class ROGndIntensity(Structure):
    _pack_ = 1
    _fields_ = [
        ("r", c_ubyte),
        ("g", c_ubyte),
        ("b", c_ubyte)
    ]


class ROGndLightmap(Structure):
    _pack_ = 1
    _fields_ = [
        ("brightness", c_ubyte * 8 * 8),
        ("intensity", ROGndIntensity * 8 * 8)
    ]


class ROGnd(Structure):
    _pack_ = 1
    _fields_ = [
        ("vermajor", c_ubyte),
        ("verminor", c_ubyte),
        ("width", c_uint),
        ("height", c_uint),
        ("zoom", c_float),
        ("texturecount", c_uint),
        ("textures", POINTER(c_char_p)),
        ("lightmapcount", c_uint),
        ("lightmaps", POINTER(ROGndLightmap)),
        ("surfacecount", c_uint),
        ("surfaces", POINTER(ROGndSurface)),
        ("cells", POINTER(ROGndCell))
    ]


class GND:
    """Ground File."""

    def __init__ (self,fn=None):
        """Constructor."""
        self._gnd = None
        roint = CDLL("roint")

        self._loadFromFile = roint.gnd_loadFromFile
        self._loadFromFile.argtypes = [c_char_p]
        self._loadFromFile.restype = POINTER(ROGnd)

        self._unload = roint.gnd_unload
        self._unload.argtypes = [POINTER(ROGnd)]
        self._unload.restype = None

        self._gnd = self._loadFromFile(fn);
        assert self._gnd, "failed to load GND"

    def __del__ (self):
        """Destructor."""
        if self._gnd:
            self._unload(self._gnd)

    def getVerMajor (self):
        return self._gnd[0].vermajor

    def getVerMinor (self):
        return self._gnd[0].verminor

    def getWidth (self):
        return self._gnd[0].width

    def getHeight (self):
        return self._gnd[0].height

    def getZoom (self):
        return self._gnd[0].zoom

    def getTextures (self):
        return cast(self._gnd[0].textures, POINTER(c_char_p * self._gnd[0].texturecount))[0]

    def getLightmaps (self):
        return cast(self._gnd[0].lightmaps, POINTER(ROGndLightmap * self._gnd[0].lightmapcount))[0]

    def getSurfaces (self):
        return cast(self._gnd[0].surfaces, POINTER(ROGndSurface * self._gnd[0].surfacecount))[0]

    def getCells (self):
        cellcount = self.getWidth() * self.getHeight()
        return cast(self._gnd[0].cells, POINTER(ROGndCell * cellcount))[0]
