#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Display image management class.

This class stores a full-size image and display position. It allows extraction
of a thumbnail of any size, converting points from display location to image
location.

:REQUIRES: ...
:PRECONDITION: ...
:POSTCONDITION: ...

:AUTHOR: Ripley6811
:ORGANIZATION: National Cheng Kung University, Department of Earth Sciences
:CONTACT: python@boun.cr
:SINCE: Wed Sep 19 16:52:38 2012
:VERSION: 0.1
:STATUS: Nascent
:TODO: ...
"""
#===============================================================================
# PROGRAM METADATA
#===============================================================================
__author__ = 'Ripley6811'
__contact__ = 'python@boun.cr'
__copyright__ = ''
__license__ = ''
__date__ = 'Wed Sep 19 16:52:38 2012'
__version__ = '0.1'

#===============================================================================
# IMPORT STATEMENTS
#===============================================================================
from PIL import Image, ImageDraw, ImageTk, ImageChops
from numpy import *  # IMPORTS ndarray(), arange(), zeros(), ones()


#===============================================================================
# DISPLAY_IMAGE CLASS
#===============================================================================
class DisplayImage:
    '''Structure for holding an image and info on how it is displayed on screen.
    '''
    def __init__(self, image, ID, anchor=(0,0), scale=1.0, fit=(0,0)):
        '''Accepts PIL image. 'fit' overrides 'scale' if given as a parameter.
        '''
        self.ID = ID
        self.im = image
        self.size = image.size
        self.scale = scale
        self.fit = fit # SET THE RETURN SCALING BY THE AREA IT MUST FIT INSIDE
        self.anchor = anchor # WHERE TOPLEFT OF IMAGE WILL BE PLACED IN DISPLAY AREA
        self.cropbox = (0, 0, image.size[0], image.size[1]) # See PIL crop

        self.fit_scale() # OVERRIDES SCALE PARAMETER IF FIT IS SET



    def set_box(self, box):
        '''Set the display region of image.

        Arg is a 4-tuple defining the left, upper, right, and lower pixel
        coordinate. Same as in the crop method of PIL Image class.
        '''
        assert box[0] >=0 and box[1] >= 0
        assert box[2] <= self.size[0] and box[3] <= self.size[1]
        self.cropbox = box
        self.fit_scale()



    def set_fit(self, dxdy):
        '''Set desired size in pixels of final return image.

        :PARAMETERS:
            *dxdy* --- A tuple giving the desired width and height.

        '''
        assert dxdy[0] > 0 and dxdy[1] > 0
        self.fit = tuple(dxdy)
        self.fit_scale()



    def fit_scale(self):
        if self.fit[0] > 0 and self.fit[1] > 0:
            cropsize = (self.cropbox[2] - self.cropbox[0], self.cropbox[3] - self.cropbox[1])
            self.scale = min(self.fit[0] / float(cropsize[0]), self.fit[1] / float(cropsize[1]))



    def point(self, xy):
        '''Translates the point on display window to pixel coordinate of whole
        image. Returns False if point is not within image.

        This method can be used to test if a clicked point was on this image.
        Can use this method to retrieve the image coordinate of a clicked point.
        '''
        axy = self.anchor
        cxy = (self.cropbox[0] * self.scale, self.cropbox[1] * self.scale)
        boxspan = self.box_span()
        for i in xrange(2):
            if xy[i] < self.anchor[i] or xy[i] > self.anchor[i] + boxspan[i]:
                return False
        # SUBTRACT ANCHOR COORD, REVERSE SCALING, AND ADD CROPPED DISTANCE BACK
        retval = ((xy[0] - axy[0] + cxy[0])/self.scale,
                  (xy[1] - axy[1] + cxy[1])/self.scale )
        return retval



    def box_span(self):
        return (int((self.cropbox[2] - self.cropbox[0])*self.scale),
                int((self.cropbox[3] - self.cropbox[1])*self.scale))



    def image(self, Tk=True):
        '''Retrieve a copy of the cropped and resized portion of this image.

        Default is to return a Tkinter compatible image.

        @kwarg Tk: True for Tkinter image, False for PIL
        '''
        self.imcopy = self.im.crop(self.cropbox)
        self.imcopy.thumbnail(tuple([int(each * self.scale) for each in self.size]))
        if Tk == True:  self.imcopy = ImageTk.PhotoImage(self.imcopy)
        return self.imcopy


    def to_disp_pt(self, pt):
        '''Scale down and offset image points for display. Image point -> Disp point.

        '''
        axy = self.anchor
        cxy = (self.cropbox[0], self.cropbox[1])
        return (pt[0]*self.scale - cxy[0]*self.scale + axy[0], pt[1]*self.scale - cxy[1]*self.scale + axy[1])


    def get_texture(self, poly, polydest):
        out_texture = self.im.copy()



        out_texture = perspective_transform(out_texture, poly+polydest )

        mask = Image.new('L', out_texture.size, color=0)
        draw = ImageDraw.Draw(mask)
        draw.polygon(polydest, fill=255)
        out_texture.putalpha(mask)


        out_texture = out_texture.crop(self.cropbox)
        out_texture.thumbnail(tuple([int(each * self.scale) for each in self.size]))

        out_texture = ImageTk.PhotoImage(out_texture)
        return out_texture
#        out_texture.show()

def perspective_transform(image, ptop, cam_rotate = 0, alpha=True):
    '''This method performs a perspective transform on the supplied image.
    Input: image = source image to transform
           ptop = four source and four corresponding destination coordinates
    '''
#    image = image.rotate(cam_rotate)

    # CALCULATE THE TRANSFORMATION MATRIX
    b0,b1,b2,b3,a0,a1,a2,a3 = ptop

    A = array([[a0[0], a0[1], 1,     0,     0, 0, -a0[0]*b0[0], -a0[1]*b0[0]],
               [    0,     0, 0, a0[0], a0[1], 1, -a0[0]*b0[1], -a0[1]*b0[1]],
               [a1[0], a1[1], 1,     0,     0, 0, -a1[0]*b1[0], -a1[1]*b1[0]],
               [    0,     0, 0, a1[0], a1[1], 1, -a1[0]*b1[1], -a1[1]*b1[1]],
               [a2[0], a2[1], 1,     0,     0, 0, -a2[0]*b2[0], -a2[1]*b2[0]],
               [    0,     0, 0, a2[0], a2[1], 1, -a2[0]*b2[1], -a2[1]*b2[1]],
               [a3[0], a3[1], 1,     0,     0, 0, -a3[0]*b3[0], -a3[1]*b3[0]],
               [    0,     0, 0, a3[0], a3[1], 1, -a3[0]*b3[1], -a3[1]*b3[1]]] )
    B = array([b0[0], b0[1], b1[0], b1[1], b2[0], b2[1], b3[0], b3[1]])

    transdata = linalg.solve(A,B)
    H = append(transdata,1)
    H = inv(reshape(H, (3,3))).flat


    # TRANSFORM THE IMAGE WITH SIZE BASED ON DESTINATION COORDINATES
    S = image.size
    tl = (H[2])/(1),(H[5])/(1)
    bl = (H[1]*S[1]+H[2])/(H[7]*S[1]+1),(H[4]*S[1]+H[5])/(H[7]*S[1]+1)
    tr = (H[0]*S[0]+H[2])/(H[6]*S[0]+1),(H[3]*S[0]+H[5])/(H[6]*S[0]+1)
    br = (H[0]*S[0]+H[1]*S[1]+H[2])/(H[6]*S[0]+H[7]*S[1]+1),(H[3]*S[0]+H[4]*S[1]+H[5])/(H[6]*S[0]+H[7]*S[1]+1)

    xmax = max(tl[0],bl[0],tr[0],br[0])
    xmin = min(tl[0],bl[0],tr[0],br[0])
    ymax = max(tl[1],bl[1],tr[1],br[1])
    ymin = min(tl[1],bl[1],tr[1],br[1])
    size = ( int(xmax-xmin), int(ymax-ymin)*2 )
    S = (1000,600)

    transimage = image.transform(S, Image.PERSPECTIVE, transdata)

    # RETURN TRANSFORMED IMAGE
    return transimage



def get_transform_data(pts8, backward=True ):
    '''This method returns a perspective transform 8-tuple (a,b,c,d,e,f,g,h).

    Use to transform an image:
    X = (a x + b y + c)/(g x + h y + 1)
    Y = (d x + e y + f)/(g x + h y + 1)

    Image.transform: Use 4 source coordinates, followed by 4 corresponding
        destination coordinates. Use backward=True (the default)

    To calculate the destination coordinate of a single pixel, either reverse
        the pts (4 dest, followed by 4 source, backward=True) or use the same
        pts but set backward to False.

    @arg pts8: four source and four corresponding destination coordinates
    @kwarg backward: True to return coefficients for calculating an originating
        position. False to return coefficients for calculating a destination
        coordinate. (Image.transform calculates originating position.)
    '''
    assert len(pts8) == 8, 'Requires a tuple of eight coordinate tuples (x,y)'

    b0,b1,b2,b3,a0,a1,a2,a3 = pts8 if backward else pts8[::-1]

    # CALCULATE THE COEFFICIENTS
    A = array([[a0[0], a0[1], 1,     0,     0, 0, -a0[0]*b0[0], -a0[1]*b0[0]],
               [    0,     0, 0, a0[0], a0[1], 1, -a0[0]*b0[1], -a0[1]*b0[1]],
               [a1[0], a1[1], 1,     0,     0, 0, -a1[0]*b1[0], -a1[1]*b1[0]],
               [    0,     0, 0, a1[0], a1[1], 1, -a1[0]*b1[1], -a1[1]*b1[1]],
               [a2[0], a2[1], 1,     0,     0, 0, -a2[0]*b2[0], -a2[1]*b2[0]],
               [    0,     0, 0, a2[0], a2[1], 1, -a2[0]*b2[1], -a2[1]*b2[1]],
               [a3[0], a3[1], 1,     0,     0, 0, -a3[0]*b3[0], -a3[1]*b3[0]],
               [    0,     0, 0, a3[0], a3[1], 1, -a3[0]*b3[1], -a3[1]*b3[1]]] )
    B = array([b0[0], b0[1], b1[0], b1[1], b2[0], b2[1], b3[0], b3[1]])

    return linalg.solve(A,B)