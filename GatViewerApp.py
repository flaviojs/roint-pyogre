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

    def createGatObject(self):
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
        sg = self.sceneManager.createStaticGeometry("GatObject")
        for i in range(0, width * height):
            cell = self.gat.getCell(i)# west->east, south->north ordering
            if cell.type >= 0 and cell.type <= 6:
                material = "GatCell/" + str(cell.type)
            else:
                material = "GatCell/Unknown"

            # TODO this is very inefficient, revisit this when more familiar with ogre (requires geometry with different materials)
            mo = ogre.ManualObject("GatCellObject" + str(i))
            mo.begin(material, ogre.RenderOperation.OT_TRIANGLE_LIST)
            mo.position(0,    -cell.height[0], side)
            mo.textureCoord(0, 1)
            mo.position(side, -cell.height[1], side)
            mo.textureCoord(1, 1)
            mo.position(0,    -cell.height[2], 0)
            mo.textureCoord(0, 0)
            mo.position(side, -cell.height[3], 0)
            mo.textureCoord(1, 0)
            mo.triangle(0, 1, 3)
            mo.triangle(0, 3, 2)
            mo.end()
            mo.convertToMesh("GatCellMesh" + str(i))
            ent = self.sceneManager.createEntity("cell" + str(i), "GatCellMesh" + str(i))
            pos = ogre.Vector3((int(i % width) - center.x) * side, # west->east (-x to +x)
                               0,
                               (center.z - int(i / width)) * side) # south->north (+z to -z)
            sg.addEntity(ent, pos)
        sg.build()
 
    def _createScene(self):
        self.sceneManager.setAmbientLight((1, 1, 1))

        dist = self.gat.getHeight() * 5 / 2 # start at south edge of map
        self.camera.setPosition(0, dist, dist)
        self.camera.lookAt(0, 0, 0)

        self.createGatObject()


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
