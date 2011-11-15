#!/usr/bin/python
# -*- coding: utf8 -*-
"""
Interface with roint's STR file format.
Flávio J. Saraiva @ 2011-10-24 (Python 2.7.2)

Requires:
    roint (C shared library) (https://gitorious.org/open-ragnarok/roint)
"""
from ctypes import *


class ROStrKeyFrame(Structure):
    _pack_ = 1
    _fields_ = [
        ("framenum", c_uint),
        ("type", c_uint),
        ("x", c_float),
	("y", c_float),
	("u", c_float),
	("v", c_float),
	("us", c_float),
	("vs", c_float),
	("u2", c_float),
	("v2", c_float),
	("us2", c_float),
	("vs2", c_float),
	("ax", c_float * 4),
	("ay", c_float * 4),
	("aniframe", c_float),
	("anitype", c_uint),
	("anidelta", c_float),
	("rz", c_float),
	("crR", c_float),
	("crG", c_float),
	("crB", c_float),
	("crA", c_float),
	("srcalpha", c_uint),
	("destalpha", c_uint),
	("mtpreset", c_uint)]


class ROStrTexture(Structure):
    _pack_ = 1
    _fields_ = [
        ("name", c_char * 128)]


class ROStrLayer(Structure):
    _pack_ = 1
    _fields_ = [
        ("texturecount", c_uint),
        ("textures", POINTER(ROStrTexture)),
        ("keyframecount", c_uint),
        ("keyframes", POINTER(ROStrKeyFrame))]


class ROStr(Structure):
    _pack_ = 1
    _fields_ = [
        ("version", c_uint),
        ("framecount", c_uint),
        ("fps", c_uint),
        ("layercount", c_uint),
        ("reserved", c_ubyte * 16),
        ("layers", POINTER(ROStrLayer))]


class STR:
    """Effect File."""

    def __init__ (self,fn=None):
        """Constructor."""
        self._str = None
        roint = CDLL("roint")

        self._loadFromFile = roint.str_loadFromFile
        self._loadFromFile.argtypes = [c_char_p]
        self._loadFromFile.restype = POINTER(ROStr)

        self._unload = roint.str_unload
        self._unload.argtypes = [POINTER(ROStr)]
        self._unload.restype = None

        self._str = self._loadFromFile(fn);
        assert self._str, "failed to load STR"

    def __del__ (self):
        """Destructor."""
        if self._str:
            self._unload(self._str)

    def getVersion (self):
        return self._str[0].version

    def getFrameCount (self):
        return self._str[0].framecount

    def getFPS (self):
        return self._str[0].fps

    def getReserved (self):
        return self._str[0].reserved

    def getLayers (self):
        if self._str[0].layercount == 0:
            return None
        return cast(self._str[0].layers, POINTER(ROStrLayer * self._str[0].layercount))[0]

    def getTextures (self, layerId):
        layer = self.getLayers()[layerId]
        if layer.texturecount == 0:
            return None
        return cast(layer.textures, POINTER(ROStrTexture * layer.texturecount))[0]

    def getKeyFrames (self, layerId):
        layer = self.getLayers()[layerId]
        if layer.keyframecount == 0:
            return None
        return cast(layer.keyframes, POINTER(ROStrKeyFrame * layer.keyframecount))[0]

if __name__ == '__main__':
    keyframe = ROStrKeyFrame()
    print keyframe
    print keyframe._fields_
    data = dict()
    for fieldname,fieldtype in keyframe._fields_:
        print fieldname,fieldtype
        
        data[fieldname] = getattr(keyframe, fieldname)
    print data
    for k in data.keys():
        print k,v
