#!/usr/bin/python
# -*- coding: utf8 -*-
"""
Interface with roint's GND file format.
Flávio J. Saraiva @ 2011-10-24 (Python 2.7.2)

Requires:
    roint (C shared library) (https://gitorious.org/open-ragnarok/roint)
"""
from ctypes import *


class ROGrf(Structure):
    pass


class ROGrfFile(Structure):
    _fields_ = [
        ("fileName", c_char_p),
        ("compressedLength", c_int),
        ("compressedLengthAligned", c_int),
        ("uncompressedLength", c_int),
        ("flags", c_char),
        ("offset", c_int),
        ("cycle", c_int),
        ("grf", POINTER(ROGrf)),
        ("data", POINTER(c_ubyte))
    ]


class ROGrfHeader(Structure):
    _fields_ = [
        ("signature", c_char * 16),
        ("allowencryption", c_ubyte * 14),
        ("filetableoffset", c_uint),
        ("number1", c_uint),
        ("number2", c_uint),
        ("version", c_uint)
    ]


class ROGrf(Structure):
    _fields_ = [
        ("header", ROGrfHeader),
        ("fp", c_void_p),
        ("files", POINTER(ROGrfFile)),
    ]


class GRF:
    """GRF archive."""

    def __init__ (self,fn=None):
        """Constructor."""
        self._grf = None
        roint = CDLL("roint")

        self._open = roint.grf_open
        self._open.argtypes = [c_char_p]
        self._open.restype = POINTER(ROGrf)

        self._close = roint.grf_close
        self._close.argtypes = [POINTER(ROGrf)]
        self._close.restype = None

        self._filecount = roint.grf_filecount
        self._filecount.argtypes = [POINTER(ROGrf)]
        self._filecount.restype = c_uint

        self._getdata = roint.grf_getdata
        self._getdata.argtypes = [POINTER(ROGrfFile)]
        self._getdata.restype = c_int


        self._freedata = roint.grf_freedata
        self._freedata.argtypes = [POINTER(ROGrfFile)]
        self._freedata.restype = None

        self._grf = self._open(fn);
        assert self._grf, "failed to load GRF"

    def __del__ (self):
        """Destructor."""
        if self._grf:
            self._close(self._grf)

    def getFileCount (self):
        return self._filecount(self._grf)

    def getFiles (self):
        filecount = self.getFileCount()
        return cast(self._grf[0].files, POINTER(ROGrfFile * filecount))[0]

    def getFileData (self, filename):
        grffiles = self.getFiles()
        for i in range(0, len(grffiles)):
            if filename == grffiles[i].fileName:
                grffile = grffiles[i]
                self._getdata(byref(grffile))
                size = grffiles[i].uncompressedLength
                data = cast(grffiles[i].data, POINTER(c_ubyte * size))[0]
                data = data[:]
                self._freedata(byref(grffile))
                return data
        return None

    def getFileDataCaseInsensitive (self, filename):
        filename = filename.lower()
        grffiles = self.getFiles()
        for i in range(0, len(grffiles)):
            if filename == grffiles[i].fileName.lower():
                grffile = grffiles[i]
                self._getdata(byref(grffile))
                size = grffiles[i].uncompressedLength
                data = cast(grffiles[i].data, POINTER(c_ubyte * size))[0]
                data = data[:]
                self._freedata(byref(grffile))
                return data
        return None
