#!/usr/bin/python
# -*- coding: utf8 -*-
"""
Application to view a GAT.
Flávio J. Saraiva @ 2011-10-24 (Python 2.7.2)

Requires:
    ogre (http://www.pythonogre.com/)
    gat.py
"""
from gat import *
import sys
import ogre.renderer.OGRE.sf_OIS as sf
import ogre.renderer.OGRE as ogre
import ogre.io.OIS as OIS


class GatViewerApp(sf.Application):

    def __init__ (self, gat):
        assert gat
        sf.Application.__init__(self)
        self.gat = gat

    def createGatMesh(self):
        width = self.gat.getWidth()
        height = self.gat.getHeight()
        center = ogre.Vector3(width / 2, 0, height / 2)
 
        side = 5
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
        mo = ogre.ManualObject("GatObject")
        mo.setDynamic(True)
        cells = self.gat.getCells()
        remaining = range(0, len(cells))
        while len(remaining) > 0:
            grouptype = cells[remaining[0]].type
            group = [i for i in remaining if cells[i].type == grouptype]
            remaining = [i for i in remaining if cells[i].type != grouptype]
            if grouptype >= 0 and grouptype <= 6:
                material = "GatCell/" + str(grouptype)
            else:
                material = "GatCell/Unknown"
            mo.begin(material, ogre.RenderOperation.OT_TRIANGLE_LIST)
            offset = 0
            for i in group:
                cell = cells[i]
                xpos = (int(i % width) - center.x) * side # west->east (-x to +x)
                zpos = (center.z - int(i / width)) * side # south->north (+z to -z)
                mo.position(xpos,        -cell.height[0], zpos + side)
                mo.textureCoord(0, 1)
                mo.position(xpos + side, -cell.height[1], zpos + side)
                mo.textureCoord(1, 1)
                mo.position(xpos,        -cell.height[2], zpos)
                mo.textureCoord(0, 0)
                mo.position(xpos + side, -cell.height[3], zpos)
                mo.textureCoord(1, 0)
                mo.triangle(offset, offset+1, offset+3)
                mo.triangle(offset, offset+3, offset+2)
                offset += 4
            mo.end()
        mo.convertToMesh("GatMesh")

    def _createScene(self):
        self.createGatMesh()
        self.sceneManager.setAmbientLight((1, 1, 1))

        radius = self.gat.getHeight() * 5 / 2 # start at south edge of map
        self.camera.setPosition(0, radius / 2, radius)
        self.camera.lookAt(0, 0, 0)

        gat = self.sceneManager.createEntity("Gat", "GatMesh")
        sg = self.sceneManager.createStaticGeometry("GatGeometry")
        sg.addEntity(gat,(0,0,0))
        sg.build()


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print "Usage: " + sys.argv[0] + " file.gat"
    else:
        filename = sys.argv[1]
        gat = GAT(filename)
        try:
            app = GatViewerApp(gat)
            app.go()
        except ogre.OgreException, e:
            print e
        del gat