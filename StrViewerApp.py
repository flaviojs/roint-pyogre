#!/usr/bin/python
# -*- coding: utf8 -*-
"""
Application to view a STR. (effect animation)
Flávio J. Saraiva @ 2011-11-17 (Python 2.7.2, ogre 1.7.2)

TODO used a proper animation instead of rebuilding each frame
TODO turn magenta pixels into transparent pixels for bmp/jpg (they don't have alpha)
TODO figure out the Ogre3D code equivalent to the DirectX code of mtpreset

Requires:
    ogre (http://www.pythonogre.com/)
    str.py
    grf.py
"""
from str import *
from grf import GRF
import sys
import os
import math
import ctypes
import ogre.renderer.OGRE.sf_OIS as sf
import ogre.renderer.OGRE as ogre
import ogre.io.OIS as OIS


def DEBUG (*args):
    args = ["DEBUG -"] + [str(arg) for arg in args]
    print " ".join(args)
    pass


def copyKeyframe (frame, keyframe):
    ctypes.memmove(
        ctypes.byref(frame),
        ctypes.byref(keyframe),
        ctypes.sizeof(ROStrKeyFrame))


class StrLayerData:
    def __init__ (self, layerId):
        self.layerId = layerId
        self.material = None # ogre.Material
        self.keyframeId = -1
        self.frame = ROStrKeyFrame()
        self.lastFrameId = 0


class StrHandler(ogre.FrameListener):

    def __init__ (self, app):
        ogre.FrameListener.__init__(self)
        self.app = app
        self.rostr = app.rostr
        self.mo = None
        self.layerId2data = dict() # int(layerId) -> StrLayerData

    def getBlendFactor (self, blend):
        """Converts a D3DBLEND_* value to an equivalent blend factor constant."""
        if blend == 1: # D3DBLEND_ZERO
            return ogre.SceneBlendFactor.SBF_ZERO
        elif blend == 2: # D3DBLEND_ONE
            return ogre.SceneBlendFactor.SBF_ONE
        elif blend == 3: # D3DBLEND_SRCCOLOR
            return ogre.SceneBlendFactor.SBF_SOURCE_COLOUR
        elif blend == 4: # D3DBLEND_INVSRCCOLOR
            return ogre.SceneBlendFactor.SBF_ONE_MINUS_SOURCE_COLOUR
        elif blend == 5: # D3DBLEND_SRCALPHA
            return ogre.SceneBlendFactor.SBF_SOURCE_ALPHA
        elif blend == 6: # D3DBLEND_INVSRCALPHA
            return ogre.SceneBlendFactor.SBF_ONE_MINUS_SOURCE_ALPHA
        elif blend == 7: # D3DBLEND_DESTALPHA
            return ogre.SceneBlendFactor.SBF_DEST_ALPHA
        elif blend == 8: # D3DBLEND_INVDESTALPHA
            return ogre.SceneBlendFactor.SBF_ONE_MINUS_DEST_ALPHA
        elif blend == 9: # D3DBLEND_DESTCOLOR
            return ogre.SceneBlendFactor.SBF_DEST_COLOUR
        elif blend == 10: # D3DBLEND_INVDESTCOLOR
            return ogre.SceneBlendFactor.SBF_ONE_MINUS_DEST_COLOUR
        else:
            DEBUG("getBlendFactor", blend, "TODO")
            assert False

    def updateLayerMaterial (self, data):
        """Updates the material of a layer."""
        frame = data.frame
        layerId = data.layerId
        material = data.material
        material.setLightingEnabled(False)
        material.setDepthWriteEnabled(False)
        material.setSceneBlending(
            self.getBlendFactor(frame.srcalpha),
            self.getBlendFactor(frame.destalpha))
        textures = self.rostr.getTextures(layerId)
        texturepath = "effect\\" + textures[int(frame.aniframe)].name
        texture = self.app.getTextureByName(texturepath)
        materialpass = material.getTechnique(0).getPass(0)
        materialpass.removeAllTextureUnitStates()
        textureunitstate = materialpass.createTextureUnitState(texture)
        textureunitstate.setTextureAddressingMode(ogre.TextureUnitState.TAM_CLAMP)
        textureunitstate.setTextureCoordSet(0)
        # TODO these are just guesses, hopefully equivalent to the DirectX code; should be checked by someone familiar with Ogre3D and DirectX... >.<
        if frame.mtpreset == 0:
            textureunitstate.setColourOperationEx(
                ogre.LayerBlendOperationEx.LBX_MODULATE,
                ogre.LayerBlendSource.LBS_TEXTURE)
            textureunitstate.setAlphaOperation(
                ogre.LayerBlendOperationEx.LBX_MODULATE,
                ogre.LayerBlendSource.LBS_TEXTURE)
        elif frame.mtpreset == 1 or frame.mtpreset == 2:
            textureunitstate.setColourOperationEx(
                ogre.LayerBlendOperationEx.LBX_MODULATE,
                ogre.LayerBlendSource.LBS_TEXTURE)
            textureunitstate.setAlphaOperation(
                ogre.LayerBlendOperationEx.LBX_SOURCE1,
                ogre.LayerBlendSource.LBS_TEXTURE)
        elif frame.mtpreset == 3:
            textureunitstate.setColourOperationEx(
                ogre.LayerBlendOperationEx.LBX_ADD,
                ogre.LayerBlendSource.LBS_TEXTURE)
            textureunitstate.setAlphaOperation(
                ogre.LayerBlendOperationEx.LBX_SOURCE2)
        elif frame.mtpreset == 4:
            textureunitstate.setColourOperationEx(
                ogre.LayerBlendOperationEx.LBX_BLEND_TEXTURE_ALPHA,
                ogre.LayerBlendSource.LBS_TEXTURE)
            textureunitstate.setAlphaOperation(
                ogre.LayerBlendOperationEx.LBX_SOURCE2)
        else:
            DEBUG('getLayerMaterial/mtpreset', frame.mtpreset, 'TODO')
            assert False
        return material

    def morphLayerDataSingle (self, data, curFrameId):
        """Morphs the layer data of a single frame."""
        keyframes = self.rostr.getKeyFrames(data.layerId)
        assert data.keyframeId + 1 < len(keyframes) # must have next keyframe
        keyframe = keyframes[data.keyframeId + 1]
        if data.keyframeId != 0 and keyframe.framenum == curFrameId:
            data.keyframeId += 1 # next keyframe
        if data.keyframeId + 1 >= len(keyframes):
            #DEBUG('morphLayerDataSingle', data.layerId, 'end of layer (keyframeId=%d)' % data.keyframeId)
            data.keyframeId = -1
            return # end of layer
        keyframe = keyframes[data.keyframeId]
        if keyframe.framenum > curFrameId:
            return # not there yet
        if keyframe.type == 0:
            # normal keyframe
            #DEBUG('morphLayerData', data.layerId, 'normal keyframe (%d)' % keyframe.framenum)
            copyKeyframe(data.frame, keyframe)
            keyframe = keyframes[data.keyframeId + 1]
            if keyframe.framenum == curFrameId:
                data.keyframeId += 1
        elif keyframe.type == 1:
            # morph keyframe
            #DEBUG('morphLayerData', data.layerId, 'morph keyframe (%d,%d)' %(keyframe.framenum, curFrameId))
            frame = data.frame
            frame.x += keyframe.x
            frame.y += keyframe.y
            frame.u += keyframe.u
            frame.v += keyframe.v
            frame.us += keyframe.us
            frame.vs += keyframe.vs
            frame.u2 += keyframe.u2
            frame.v2 += keyframe.v2
            frame.us2 += keyframe.us2
            frame.vs2 += keyframe.vs2
            frame.ax[0] += keyframe.ax[0]
            frame.ax[1] += keyframe.ax[1]
            frame.ax[2] += keyframe.ax[2]
            frame.ax[3] += keyframe.ax[3]
            frame.ay[0] += keyframe.ay[0]
            frame.ay[1] += keyframe.ay[1]
            frame.ay[2] += keyframe.ay[2]
            frame.ay[3] += keyframe.ay[3]
            frame.rz += keyframe.rz
            frame.crR += keyframe.crR
            frame.crG += keyframe.crG
            frame.crB += keyframe.crB
            frame.crA += keyframe.crA
            aniframe = frame.aniframe
            texturecount = len(self.rostr.getTextures(data.layerId))
            if keyframe.anitype == 0: # do nothing
                pass
            elif keyframe.anitype == 1: # add aniframe  ]-inf,inf[
                aniframe += keyframe.aniframe
            elif keyframe.anitype == 2: # add anidelta, limit  ]-inf,texturecount[
                aniframe += keyframe.anidelta
                if aniframe >= texturecount:
                    aniframe = texturecount - 1
            elif keyframe.anitype == 3: # add anidelta, loop  [0.0,texturecount[
                aniframe += keyframe.anidelta
                if aniframe >= texturecount:
                    aniframe = aniframe % texturecount
            elif keyframe.anitype == 4: # subtract anidelta, loop  [0.0,texturecount[  WARNING broken on 2004 client
                aniframe -= keyframe.anidelta
                if aniframe < 0:
                    aniframe = aniframe % texturecount
            elif keyframe.anitype == 5: # randomize with anidelta seed???  [0,ROStrLayer.texturecount - 1]
                value = (int)(aniframe + (curFrameId - frame.framenum) * keyframe.anidelta)
                lasttex = texturecount - 1
                n = value / lasttex
                if n & 1:
                    aniframe = lasttex * (n + 1) - value
                else:
                    aniframe = value - lasttex * n
            else:
                DEBUG('morphLayerData', data.layerId, 'keyframe.anitype', keyframe.anitype, 'TODO')
            frame.aniframe = aniframe
        else:
            DEBUG('morphLayerData', data.layerId, 'keyframe.type', keyframe.type, 'TODO')
            assert False
        self.updateLayerMaterial(data)

    def morphLayerData (self, data, lastFrameId):
        """Morphs the layer data up to the current frameId."""
        #DEBUG('morphLayerData', data.layerId)
        keyframes = self.rostr.getKeyFrames(data.layerId)
        # process each frame
        for curFrameId in range(lastFrameId + 1, self.frameId + 1):
            #DEBUG('morphLayerData', data.layerId, 'curFrameId', curFrameId)
            if data.keyframeId == -1:
                #DEBUG('morphLayerData', data.layerId, 'layer done')
                break # layer already ended
            if data.keyframeId + 1 >= len(keyframes):
                #DEBUG('morphLayerData', data.layerId, 'end of layer (keyframeId=%d)' % data.keyframeId)
                data.keyframeId = -1
                break # end of layer
            self.morphLayerDataSingle(data, curFrameId)

    def getLayerData (self, layerId):
        keyframes = self.rostr.getKeyFrames(layerId)
        if keyframes is None:
            return None # discard layer
        data = StrLayerData(layerId)
        materialname = "StrMaterial/Layer%d" % layerId
        data.material = ogre.MaterialManager.getSingleton().create(
            materialname,
            ogre.ResourceGroupManager.DEFAULT_RESOURCE_GROUP_NAME)
        data.keyframeId = -1
        data.lastFrameId = keyframes[len(keyframes) - 1].framenum
        return data

    def addGeometry (self, data):
        """Add frame geometry (of one layer)."""
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
        #
        # Keyframe coordinates:
        #  __x   __u
        # |     |
        # y     v
        #
        # Keyframe vertices:
        #   (u,v),(u2,v2)
        #  /
        # 0---1 - (u+us,v),(u2+us2,v2)
        # |   |
        # 3---2 - (u+us,v+vs),(u2+vs2,v2+vs2)
        #  \
        #   (u,v+vs),(u2,v2+vs2)
        # XXX official client ignores the second texture coordinates
        layerId = data.layerId
        frame = data.frame
        material = data.material
        mo = self.mo
        if frame.ax[0] < frame.ax[1]:
            x = frame.ax[:]
            u = [frame.u, frame.u + frame.us]
            u2 = [frame.u2, frame.u2 + frame.us2]
        else:
            x = frame.ax
            x = [x[1], x[0], x[3], x[2]]
            u = [frame.u + frame.us, frame.u]
            u2 = [frame.u2 + frame.us2, frame.u2]
        if frame.ay[1] < frame.ay[2]:
            y = frame.ay[:]
            v = [frame.v, frame.v + frame.vs]
            v2 = [frame.v2, frame.v2 + frame.vs2]
        else:
            y = frame.ay
            y = [y[3], y[2], y[1], y[0]]
            v = [frame.v + frame.vs, frame.v]
            v2 = [frame.v2 + frame.vs2, frame.v2]
        vertcolor = ogre.ColourValue(
            frame.crR / 255.0,
            frame.crG / 255.0,
            frame.crB / 255.0,
            frame.crA / 255.0)
        angle = math.radians(frame.rz * 360.0 / 1024.0)
        sinvalue = math.sin(angle)
        cosvalue = math.cos(angle)
        mo.begin(material.getName(), ogre.RenderOperation.OT_TRIANGLE_LIST)
        for i in range(0, 4):
            oldx, oldy = x[i], -y[i] # keyframe to world
            x[i] = oldx * cosvalue - oldy * sinvalue # rotate
            y[i] = oldy * cosvalue + oldx * sinvalue
            x[i] = x[i] + frame.x - 320 # translate to origin?
            y[i] = y[i] - frame.y + 240
        z = 0
        mo.position(x[0], y[0], z)
        mo.textureCoord(u[0], v[0])
        mo.textureCoord(u2[0], v2[0])
        mo.colour(vertcolor)
        mo.position(x[1], y[1], z)
        mo.textureCoord(u[1], v[0])
        mo.textureCoord(u2[1], v2[0])
        mo.colour(vertcolor)
        mo.position(x[2], y[2], z)
        mo.textureCoord(u[1], v[1])
        mo.textureCoord(u2[1], v2[1])
        mo.colour(vertcolor)
        mo.position(x[3], y[3], z)
        mo.textureCoord(u[0], v[1])
        mo.textureCoord(u2[0], v2[1])
        mo.colour(vertcolor)
        mo.triangle(3, 2, 1)
        mo.triangle(3, 1, 0)
        mo.end()
        
    def updateGeometry (self):
        """Update all geometry."""
        mo = self.mo
        mo.clear()
        mo.estimateVertexCount(4 * len(self.layerId2data))
        mo.estimateIndexCount(6 * len(self.layerId2data))
        hasFrames = False
        for layerId in sorted(self.layerId2data.keys()):
            data = self.layerId2data[layerId]
            if data.keyframeId == -1:
                continue # layer ended
            hasFrames = True
            if data.frame.framenum > self.frameId:
                continue # not there yet
            self.addGeometry(data)
        if not hasFrames and self.frameId != 0:
            self.restart()

    def createObject (self):
        if self.rostr.getLayers() is None:
            return None
        mo = ogre.ManualObject("StrObject")
        mo.setDynamic(True)
        mo.setKeepDeclarationOrder(True)
        self.mo = mo
        # get layer data
        self.layerId2data = dict()
        lastFrameId = -1
        for layerId in range(0, len(self.rostr.getLayers())):
            data = self.getLayerData(layerId)
            if data:
                self.layerId2data[layerId] = data
                if lastFrameId < data.lastFrameId:
                    lastFrameId = data.lastFrameId
        # XXX official client behaviour: -.-'
        #   - framecount is hardcoded???
        #   - fps is ignored, it just draws the next frame each processing cycle???
        #self.framecount = self.rostr.getFrameCount()
        #self.fps = self.rostr.getFPS()
        #self.duration = float(self.framecount) / self.fps
        #DEBUG("self.framecount", self.framecount)
        self.fps = 30
        self.duration = lastFrameId / self.fps
        DEBUG("self.lastFrameId", lastFrameId)
        DEBUG("self.fps", self.fps)
        DEBUG("self.duration", self.duration)
        self.restart()
        return mo

    def restart (self):
        DEBUG("restart")
        self.timeSinceStart = 0.0
        self.frameId = -1;
        for layerId in self.layerId2data.keys():
            data = self.layerId2data[layerId]
            data.keyframeId = 0
            keyframe = self.rostr.getKeyFrames(layerId)[0]
            copyKeyframe(data.frame, keyframe)
            assert data.frame.type == 0
            self.updateLayerMaterial(data)

    def frameStarted (self, evt):
        """Called when a frame is about to begin rendering."""
        lastFrameId = self.frameId
        self.timeSinceStart += evt.timeSinceLastFrame
        self.frameId = int(self.fps * self.timeSinceStart)
        if self.frameId != lastFrameId:
            DEBUG('frameStarted', self.frameId, "(%d)" % (self.frameId - lastFrameId), "timeSinceStart", self.timeSinceStart)
            for data in self.layerId2data.values():
                self.morphLayerData(data, lastFrameId)
            self.updateGeometry()
        return True

class StrViewerApp(sf.Application):

    def __init__ (self, rostr, rogrfs):
        sf.Application.__init__(self)
        assert rostr
        self.rostr = rostr
        self.rogrfs = rogrfs[:]
        self.roarchives = [GRF(filename) for filename in rogrfs]
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
        self.textures = dict()
        self.strhandler = None

    def __del__ (self):
        if self.roarchives:
            for archive in self.roarchives:
                del archive

    def getROFilename (self, filename):
        root,ext = os.path.splitext(filename)
        ext = ext.lower()
        if self.ropaths.has_key(ext):
            return self.ropaths[ext] + filename
        return filename

    def openDataStream (self, filename):
        for archive in self.roarchives:
            data = archive.getFileDataCaseInsensitive(filename)
            if data:
                stream = ogre.MemoryDataStream(
                    len(data),
                    freeOnClose=False,
                    readOnly=True)
                stream.setData(data)
                return stream
        return None

    def getTextureByName (self, name):
        if name == None:
            return None
        name = self.getROFilename(name)
        if not self.textures.has_key(name):
            # create texture from image file
            DEBUG(name)
            stream = self.openDataStream(name)
            assert stream, "failed to load texture %s" % name
            root,ext = os.path.splitext(filename)
            ext = ext.lower()
            image = ogre.Image()
            image.load(stream)
            if ext == '.bmp' or ext == '.jpg':
                desiredFormat = ogre.PixelFormat.PF_A1R5G5B5
            else:
                desiredFormat = ogre.PixelFormat.PF_UNKNOWN
            texture = ogre.TextureManager.getSingleton().loadImage(
                name,
                ogre.ResourceGroupManager.DEFAULT_RESOURCE_GROUP_NAME,
                image,
                desiredFormat=desiredFormat)
            self.textures[name] = texture
        return name

    def _setUpResources(self):
        sf.Application._setUpResources(self)
        ## TODO figure out how to add an archive factory...
        #self.grffactory = GrfArchiveFactory()
        #ogre.ArchiveManager.getSingleton().addArchiveFactory(self.grffactory)
        #for grf in self.grfs:
        #    ogre.ResourceGroupManager.getSingleton().addResourceLocation(grf,"Grf","General")

    def _createScene (self):
        self.sceneManager.setAmbientLight((1, 1, 1))

        self.camera.lookAt(0, 0, 0)

        self.strhandler = StrHandler(self)
        obj = self.strhandler.createObject()
        node = self.sceneManager.getRootSceneNode().createChildSceneNode("StrNode")
        node.attachObject(obj)
        self.root.addFrameListener(self.strhandler)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "Usage: " + sys.argv[0] + " file.str [file.grf ...]"
    else:
        filename = sys.argv[1]
        grfs = sys.argv[2:]
        rostr = STR(filename)
        app = None
        try:
            app = StrViewerApp(rostr, grfs)
            app.go()
        except ogre.OgreException, e:
            print e
        if app:
            del app
        if rostr:
            del rostr
