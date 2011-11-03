#!/usr/bin/python
# -*- coding: utf8 -*-
"""
Application to view a GND.
Flávio J. Saraiva @ 2011-10-24 (Python 2.7.2, ogre 1.7.2)

TODO surface lightmaps
TODO surface color
TODO surfaceId -1

Requires:
    ogre (http://www.pythonogre.com/)
    gnd.py
    grf.py
"""
from gnd import *
from grf import GRF
#from GrfArchive import GrfArchiveFactory
import sys
import os
import ogre.renderer.OGRE.sf_OIS as sf
import ogre.renderer.OGRE as ogre
import ogre.io.OIS as OIS


class GndViewerApp(sf.Application):

    def __init__ (self, gnd, grfs):
        sf.Application.__init__(self)
        assert gnd
        self.gnd = gnd
        self.grfs = grfs[:]
        self.archives = [GRF(filename) for filename in grfs]
        self.textures = dict()
        self.lightmaps = dict()
        self.materials = dict()
        self.ropaths = {
            '.act': "data\\sprite\\",
            '.rma': "data\\model\\",
            '.gat': "data\\",
            '.bmp': "data\\texture\\",
            '.tga': "data\\texture\\",
            '.jpg': "data\\texture\\",
            '.ebm': "_tmpEmblem\\",
            '.str': "data\\texture\\effect\\",
            '.gnd': "data\\",
            '.imf': "data\\imf\\",
            '.rsm': "data\\model\\",
            '.rsx': "data\\model\\",
            '.gr2': "data\\model\\3dmob\\",
            '.pal': "data\\palette\\",
            '.spr': "data\\sprite\\",
            '.wav': "data\\wav\\",
            '.rsw': "data\\"
            }

    def __del__ (self):
        for archive in self.archives:
            del archive

    def getROFilename (self, filename):
        root,ext = os.path.splitext(filename)
        if self.ropaths.has_key(ext):
            return self.ropaths[ext] + filename
        return filename

    def openDataStream (self, filename):
        for archive in self.archives:
            data = archive.getFileDataCaseInsensitive(filename)
            if data:
                stream = ogre.MemoryDataStream(
                    len(data),
                    freeOnClose=False,
                    readOnly=True)
                stream.setData(data)
                return stream
        return None

    def getTexture (self, textureId):
        filename = self.gnd.getTextures()[textureId]
        filename = filename.lower()
        filename = self.getROFilename(filename)
        print "DEBUG -", filename
        if not self.textures.has_key(filename):
            stream = self.openDataStream(filename)
            assert stream
            image = ogre.Image()
            image.load(stream)
            texture = ogre.TextureManager.getSingleton().loadImage(
                filename,
                ogre.ResourceGroupManager.DEFAULT_RESOURCE_GROUP_NAME,
                image)
            self.textures[filename] = texture
        return filename

    def getSurfaceMaterial (self, surfaceId):
        if surfaceId == -1:
            return ""
        surface = self.gnd.getSurfaces()[surfaceId]
        name = "GndSurfaceMaterial/" + str(surface.textureId)
        #name = name + "_" + str(surface.lightmapId)
        #name = name + "_%x" % surface.color
        if not self.materials.has_key(name):
            print "DEBUG -", name
            textureId = surface.textureId
            material = ogre.MaterialManager.getSingleton().create(
                name,
                ogre.ResourceGroupManager.DEFAULT_RESOURCE_GROUP_NAME)
            material.getTechnique(0).getPass(0).createTextureUnitState(self.getTexture(textureId))
            #material.getTechnique(0).getPass(0).setSceneBlending(ogre.SBT_TRANSPARENT_ALPHA)
            self.materials[name] = material
        return name

    def createGndMesh (self):
        width = self.gnd.getWidth()
        height = self.gnd.getHeight()
        print "DEBUG - %dx%d" % (width,height)
        center = ogre.Vector3(width / 2, 0, height / 2)
 
        side = self.gnd.getZoom()
        # World coordinates:
        #  y
        #  |__x
        #  /
        # z
        #
        # Texture coordiates:
        #  __u
        # |
        # v
        mo = ogre.ManualObject("GndObject")
        mo.setDynamic(True)
        
        cells = self.gnd.getCells()
        surfaces = self.gnd.getSurfaces()
        remainingTop = range(0, len(cells))
        remainingFront = range(0, len(cells))
        remainingRight = range(0, len(cells))
        while True:
            print "DEBUG - remaining", \
                  len(remainingTop) +\
                  len(remainingFront) +\
                  len(remainingRight)
            if len(remainingTop) > 0:
                surfaceId = cells[remainingTop[0]].topSurfaceId
            elif len(remainingFront) > 0:
                surfaceId = cells[remainingFront[0]].frontSurfaceId
            elif len(remainingRight) > 0:
                surfaceId = cells[remainingRight[0]].rightSurfaceId
            else:
                break # done
            processingTop = [i for i in remainingTop if cells[i].topSurfaceId == surfaceId]
            processingFront = [i for i in remainingFront if cells[i].frontSurfaceId == surfaceId]
            processingRight = [i for i in remainingRight if cells[i].rightSurfaceId == surfaceId]
            remainingTop = [i for i in remainingTop if cells[i].topSurfaceId != surfaceId]
            remainingFront = [i for i in remainingFront if cells[i].frontSurfaceId != surfaceId]
            remainingRight = [i for i in remainingRight if cells[i].rightSurfaceId != surfaceId]
            if surfaceId >= 0 and surfaceId < len(surfaces):
                material = self.getSurfaceMaterial(surfaceId)
                surface = surfaces[surfaceId]
            else:
                continue # TODO
                material = ""
                surface = ROGndSurface()
            print "DEBUG - processing",\
                len(processingTop) + len(processingFront) + len(processingRight),\
                "surfaceId=%d textureId=%d lightmapId=%d color={b:%d,g:%d,r:%d,a:%d}" % (
                    surfaceId,
                    surface.textureId,
                    surface.lightmapId,
                    surface.color.b,
                    surface.color.g,
                    surface.color.r,
                    surface.color.b)
            mo.begin(material, ogre.RenderOperation.OT_TRIANGLE_LIST)
            offset = 0
            # top
            for i in processingTop:
                cell = cells[i]
                xpos = (int(i % width) - center.x) * side # west->east (-x to +x)
                zpos = (center.z - int(i / width)) * side # south->north (+z to -z)
                mo.position(xpos,        -cell.height[0], zpos + side)
                mo.textureCoord(surface.u[0], surface.v[0])#(0, 1)
                mo.position(xpos + side, -cell.height[1], zpos + side)
                mo.textureCoord(surface.u[1], surface.v[1])#(1, 1)
                mo.position(xpos,        -cell.height[2], zpos)
                mo.textureCoord(surface.u[2], surface.v[2])#(0, 0)
                mo.position(xpos + side, -cell.height[3], zpos)
                mo.textureCoord(surface.u[3], surface.v[3])#(1, 0)
                mo.triangle(offset, offset+1, offset+3)
                mo.triangle(offset, offset+3, offset+2)
                offset += 4
            # front
            for i in processingFront:
                cell = cells[i]
                front_i = i + width
                if front_i >= len(cells):
                    continue
                front_cell = cells[front_i]
                if cell.height[2] == front_cell.height[0] and\
                   cell.height[3] == front_cell.height[1]:
                    continue # nothing to show
                xpos = (int(i % width) - center.x) * side # west->east (-x to +x)
                zpos = (center.z - int(i / width)) * side # south->north (+z to -z)
                mo.position(xpos,        -cell.height[2],       zpos)
                mo.textureCoord(surface.u[0], surface.v[0])#(0, 1)
                mo.position(xpos + side, -cell.height[3],       zpos)
                mo.textureCoord(surface.u[1], surface.v[1])#(1, 1)
                mo.position(xpos,        -front_cell.height[0], zpos)
                mo.textureCoord(surface.u[2], surface.v[2])#(0, 0)
                mo.position(xpos + side, -front_cell.height[1], zpos)
                mo.textureCoord(surface.u[3], surface.v[3])#(1, 0)
                mo.triangle(offset, offset+1, offset+3)
                mo.triangle(offset, offset+3, offset+2)
                offset += 4
            # right
            for i in processingRight:
                cell = cells[i]
                right_i = i + 1
                if int(i / width) != int(right_i / width):
                    continue
                right_cell = cells[right_i]
                if cell.height[3] == right_cell.height[2] and\
                   cell.height[1] == right_cell.height[0]:
                    continue # nothing to show
                xpos = (int(i % width) - center.x) * side # west->east (-x to +x)
                zpos = (center.z - int(i / width)) * side # south->north (+z to -z)
                mo.position(xpos + side, -cell.height[3],       zpos)
                mo.textureCoord(surface.u[0], surface.v[0])#(0, 1)
                mo.position(xpos + side, -cell.height[1],       zpos + side)
                mo.textureCoord(surface.u[1], surface.v[1])#(1, 1)
                mo.position(xpos + side, -right_cell.height[2], zpos)
                mo.textureCoord(surface.u[2], surface.v[2])#(0, 0)
                mo.position(xpos + side, -right_cell.height[0], zpos + side)
                mo.textureCoord(surface.u[3], surface.v[3])#(1, 0)
                mo.triangle(offset, offset+1, offset+3)
                mo.triangle(offset, offset+3, offset+2)
                offset += 4
            mo.end()
        mo.convertToMesh("GndMesh")

    def _setUpResources(self):
        sf.Application._setUpResources(self)
        ## TODO figure out how to add an archive factory...
        #self.grffactory = GrfArchiveFactory()
        #ogre.ArchiveManager.getSingleton().addArchiveFactory(self.grffactory)
        #for grf in self.grfs:
        #    ogre.ResourceGroupManager.getSingleton().addResourceLocation(grf,"Grf","General")

    def _createScene (self):
        self.createGndMesh()
        self.sceneManager.setAmbientLight((1, 1, 1))

        radius = self.gnd.getHeight() * self.gnd.getZoom() / 2 # start at south edge of map
        self.camera.setPosition(0, radius / 2, radius)
        self.camera.lookAt(0, 0, 0)

        gnd = self.sceneManager.createEntity("Gnd", "GndMesh")
        sg = self.sceneManager.createStaticGeometry("GndGeometry")
        sg.addEntity(gnd,(0,0,0))
        sg.build()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "Usage: " + sys.argv[0] + " file.gnd [file.grf ...]"
    else:
        filename = sys.argv[1]
        grfs = sys.argv[2:]
        gnd = GND(filename)
        app = None
        try:
            app = GndViewerApp(gnd, grfs)
            app.go()
        except ogre.OgreException, e:
            print e
        if app:
            del app
        if gnd:
            del gnd
