#!/usr/bin/python
# -*- coding: utf8 -*-
"""
Application to view a STR.
Flávio J. Saraiva @ 2011-10-24 (Python 2.7.2, ogre 1.7.2)

XXX It's in a decent state now. Dunno if this is the correct way to interpret the STR data yet.
TODO used a proper animation instead of rebuilding each frame
TODO turn magenta pixels into transparent pixels for bmp/jpg (they don't have alpha)
TODO figure out if morphing is being done correctly (ex: which keyframe's blend mode should be used)
TODO figure out coordiante system used in the STR

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


class StrHandler(ogre.FrameListener):

    def __init__ (self, app):
        ogre.FrameListener.__init__(self)
        self.app = app
        self.rostr = app.rostr
        self.mo = None
        self.layerId2keyframes = dict()
        self.layerId2material = dict()

    def getBlendFactor (self, blend):
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

    def getLayerMaterial (self, layerId, frame):
        if self.layerId2material.has_key(layerId):
            material = self.layerId2material[layerId]
        else:
            name = "StrMaterial/Layer%d" % layerId
            material = ogre.MaterialManager.getSingleton().create(
                name,
                ogre.ResourceGroupManager.DEFAULT_RESOURCE_GROUP_NAME)
            self.layerId2material[layerId] = material
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
        if frame.mtpreset == 0:
            textureunitstate.setTextureCoordSet(0)
            textureunitstate.setColourOperationEx(
                ogre.LayerBlendOperationEx.LBX_MODULATE,
                ogre.LayerBlendSource.LBS_TEXTURE)
            textureunitstate.setAlphaOperation(
                ogre.LayerBlendOperationEx.LBX_MODULATE,
                ogre.LayerBlendSource.LBS_TEXTURE)
        elif frame.mtpreset == 1 or frame.mtpreset == 2:
            textureunitstate.setTextureCoordSet(0)
            textureunitstate.setColourOperationEx(
                ogre.LayerBlendOperationEx.LBX_MODULATE,
                ogre.LayerBlendSource.LBS_TEXTURE)
            textureunitstate.setAlphaOperation(
                ogre.LayerBlendOperationEx.LBX_SOURCE1,
                ogre.LayerBlendSource.LBS_TEXTURE)
        elif frame.mtpreset == 3:
            textureunitstate.setTextureCoordSet(0)
            textureunitstate.setColourOperationEx(
                ogre.LayerBlendOperationEx.LBX_ADD,
                ogre.LayerBlendSource.LBS_TEXTURE)
            textureunitstate.setAlphaOperation(
                ogre.LayerBlendOperationEx.LBX_SOURCE2)
        elif frame.mtpreset == 4:
            textureunitstate.setTextureCoordSet(0)
            textureunitstate.setColourOperationEx(
                ogre.LayerBlendOperationEx.LBX_BLEND_TEXTURE_ALPHA,
                ogre.LayerBlendSource.LBS_TEXTURE)
            textureunitstate.setAlphaOperation(
                ogre.LayerBlendOperationEx.LBX_SOURCE2)
        else:
            DEBUG('getLayerMaterial/mtpreset', frame.mtpreset, 'TODO')
            assert False
        return material

    def getMorphedFrame (self, layerId, frameId, prevframe, nextframe):
        """Return a morphed frame."""
        if frameId <= prevframe.framenum:
            return prevframe
        if frameId >= nextframe.framenum:
            return nextframe
        framediff = nextframe.framenum - prevframe.framenum
        influence1 = float(nextframe.framenum - frameId) / framediff
        influence2 = float(frameId - prevframe.framenum) / framediff
        getValue = lambda v1, v2: v1 * influence1 + v2 * influence2
        frame = ROStrKeyFrame()
        frame.framenum = frameId
        frame.x = getValue(prevframe.x, nextframe.x)
        frame.y = getValue(prevframe.y, nextframe.y)
        frame.u = getValue(prevframe.u, nextframe.u)
        frame.v = getValue(prevframe.v, nextframe.v)
        frame.us = getValue(prevframe.us, nextframe.us)
        frame.vs = getValue(prevframe.vs, nextframe.vs)
        frame.u2 = getValue(prevframe.u2, nextframe.u2)
        frame.v2 = getValue(prevframe.v2, nextframe.v2)
        frame.us2 = getValue(prevframe.us2, nextframe.us2)
        frame.vs2 = getValue(prevframe.vs2, nextframe.vs2)
        frame.ax[0] = getValue(prevframe.ax[0], nextframe.ax[0])
        frame.ax[1] = getValue(prevframe.ax[1], nextframe.ax[1])
        frame.ax[2] = getValue(prevframe.ax[2], nextframe.ax[2])
        frame.ax[3] = getValue(prevframe.ax[3], nextframe.ax[3])
        frame.ay[0] = getValue(prevframe.ay[0], nextframe.ay[0])
        frame.ay[1] = getValue(prevframe.ay[1], nextframe.ay[1])
        frame.ay[2] = getValue(prevframe.ay[2], nextframe.ay[2])
        frame.ay[3] = getValue(prevframe.ay[3], nextframe.ay[3])
        frame.rz = getValue(prevframe.rz, nextframe.rz)
        frame.crR = getValue(prevframe.crR, nextframe.crR)
        frame.crG = getValue(prevframe.crG, nextframe.crG)
        frame.crB = getValue(prevframe.crB, nextframe.crB)
        frame.crA = getValue(prevframe.crA, nextframe.crA)
        aniframe = prevframe.aniframe # TODO check how it's morphed...
        if nextframe.anitype == 0:
            pass
        elif nextframe.anitype == 1: # add aniframe
            aniframe = getValue(aniframe, aniframe + nextframe.aniframe * framediff)
        elif nextframe.anitype == 2: # add anidelta, limit
            aniframe = getValue(aniframe, aniframe + nextframe.anidelta * framediff)
            texturecount = len(self.rostr.getTextures(layerId))
            if aniframe >= texturecount:
                aniframe = texturecount - 1
        elif nextframe.anitype == 3: # add anidelta, loop
            aniframe = getValue(aniframe, aniframe + nextframe.anidelta * framediff)
            texturecount = len(self.rostr.getTextures(layerId))
            if aniframe >= texturecount:
                aniframe = aniframe % texturecount
        elif nextframe.anitype == 4: # subtract anidelta, loop
            aniframe = getValue(aniframe, aniframe - nextframe.anidelta * framediff)
            texturecount = len(self.rostr.getTextures(layerId))
            if aniframe < 0:
                aniframe = aniframe % texturecount
        else: # TODO
            DEBUG('getLayerKeyframes','anitype', prevframe.anitype, nextframe.anitype, 'TODO')
        frame.aniframe = aniframe
        frame.srcalpha = prevframe.srcalpha # TODO which keyframe?
        frame.destalpha = prevframe.destalpha # TODO which keyframe?
        frame.mtpreset = prevframe.mtpreset # TODO which keyframe?
        return frame

    def getLayerKeyframes (self, layerId):
        keyframes = self.rostr.getKeyFrames(layerId)
        if keyframes is None:
            return None
        layer = dict() # frameId -> processed keyframes
        for keyframe in keyframes:
            if keyframe.type == 0:
                # copy data
                frame = keyframe
            else:
                # add data (x,y,u,v,us,vs,u2,v2,us2,vs2,ax,ay,rz,crR,crG,crB,crA,aniframe depends on anitype)
                frame = layer[keyframe.framenum]
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
                if keyframe.anitype == 1: # add aniframe
                    aniframe += keyframe.aniframe
                elif keyframe.anitype == 2: # add anidelta, limit
                    aniframe += keyframe.anidelta
                    texturecount = len(self.rostr.getTextures(layerId))
                    if aniframe >= texturecount:
                        aniframe = texturecount - 1
                elif keyframe.anitype == 3: # add anidelta, loop
                    aniframe += keyframe.anidelta
                    texturecount = len(self.rostr.getTextures(layerId))
                    if aniframe >= texturecount:
                        aniframe = aniframe % texturecount
                elif keyframe.anitype == 4: # subtract anidelta, loop
                    aniframe -= keyframe.anidelta
                    texturecount = len(self.rostr.getTextures(layerId))
                    if aniframe < 0:
                        aniframe = aniframe % texturecount
                else: # TODO
                    DEBUG('getLayerKeyframes','anitype', keyframe.anitype, 'TODO')
                frame.aniframe = aniframe
            layer[keyframe.framenum] = frame
        return layer

    def addGeometry (self, layerId, frame):
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
        # Frame vertices:
        # 3---2
        # |   |
        # 0---1
        mo = self.mo
        z = 0
        if frame.ax[0] < frame.ax[1]:
            x = frame.ax[:]
            u = [frame.u, frame.u + frame.us]
            u2 = [frame.u2, frame.u2 + frame.us2]
        else:
            x = frame.ax
            x = [x[1], x[0], x[3], x[2]]
            u = [frame.u + frame.us, frame.u]
            u2 = [frame.u2 + frame.us2, frame.u2]
        if -frame.ay[0] < -frame.ay[1]:
            y = frame.ay[:]
            v = [frame.v, frame.v + frame.vs]
            v2 = [frame.v2, frame.v2 + frame.vs2]
        else:
            y = frame.ay
            y = [y[1], y[0], y[3], y[2]]
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
        material = self.getLayerMaterial(layerId, frame)
        mo.begin(material.getName(), ogre.RenderOperation.OT_TRIANGLE_LIST)
        for i in range(0, 4):
            oldx, oldy = x[i], y[i]
            x[i] = oldx * cosvalue - oldy * sinvalue
            y[i] = oldy * cosvalue + oldx * sinvalue
            x[i] = x[i] + frame.x - 320
            y[i] = y[i] - frame.y + 240
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
        mo.triangle(0, 1, 2)
        mo.triangle(0, 2, 3)
        mo.end()
        
    def updateGeometry (self):
        """Update all geometry."""
        mo = self.mo
        mo.clear()
        mo.estimateVertexCount(4 * len(self.layerId2keyframes))
        mo.estimateIndexCount(6 * len(self.layerId2keyframes))
        hasFrames = False
        for layerId in sorted(self.layerId2keyframes.keys()):
            frames = self.layerId2keyframes[layerId]
            prevframe = None
            for k in sorted(frames.keys()):
                frame = frames[k]
                if frame.framenum < self.frameId:
                    prevframe = frame
                    # check next keyframe
                elif frame.framenum == self.frameId:
                    self.addGeometry(layerId, frame)
                    hasFrames = True
                    break # layer is done
                else:# frame.framenum > self.frameId:
                    if prevframe:
                        frame = self.getMorphedFrame(layerId, self.frameId, prevframe, frame)
                        self.addGeometry(layerId, frame)
                    hasFrames = True
                    break # layer is done
        if not hasFrames and self.frameId != 0:
            self.restart()

    def createObject (self):
        if self.rostr.getLayers() is None:
            return None
        mo = ogre.ManualObject("StrObject")
        mo.setDynamic(True)
        mo.setKeepDeclarationOrder(True)
        self.mo = mo

        # get layer frames
        self.layerId2keyframes = dict()
        for layerId in range(0, len(self.rostr.getLayers())):
            frames = self.getLayerKeyframes(layerId)
            if frames is None:
                continue
            self.layerId2keyframes[layerId] = frames

        # build frame
        # XXX official client behaviour: -.-'
        #   - framecount is hardcoded???
        #   - fps is ignored, it just draws the next frame each processing cycle???
        #self.framecount = self.rostr.getFrameCount()
        #self.fps = self.rostr.getFPS()
        #self.duration = float(self.framecount) / self.fps
        #DEBUG("self.framecount", self.framecount)
        #DEBUG("self.fps", self.fps)
        #DEBUG("self.duration", self.duration)
        self.fps = 30
        self.restart()
        return mo

    def restart (self):
        DEBUG("restart")
        self.frameId = 0;
        self.timeSinceStart = 0.0
        self.updateGeometry()

    def frameStarted (self, evt):
        """Called when a frame is about to begin rendering."""
        self.timeSinceStart += evt.timeSinceLastFrame
        frameId = int(self.fps * self.timeSinceStart)
        if self.frameId != frameId:
            DEBUG('frameStarted', frameId, "timeSinceStart", self.timeSinceStart)
            self.frameId = frameId
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
