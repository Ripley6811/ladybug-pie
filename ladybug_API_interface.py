#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Ladybug video stream interface.

Contains all methods for managing a Ladybug3 *.pgr video stream. Retrieving
images from stream.

@SINCE: Sun Jan 29 16:33:32 2012
@VERSION: 1.0
@STATUS: In progress
@CHANGE: ...
@TODO: ...


@REQUIRES: ladybug.dll
@PRECONDITION: ...
@POSTCONDITION: ...


@AUTHOR: Ripley6811
@ORGANIZATION: National Cheng Kung University, Department of Earth Sciences
@COPYRIGHT: ...
@LICENSE: ...
@CONTACT: tastethejava@hotmail.com
"""
##### PROGRAM METADATA
__author__ = 'Ripley6811'   #: A pseudonym.
__contact__ = 'tastethejava@hotmail.com'
__copyright__ = 'none'
__license__ = 'undecided'
__date__ = 'Sun Jan 29 16:33:32 2012'
__version__ = '.0'

##### IMPORT STATEMENTS
#from numpy import *  # IMPORTS ndarray(), arange(), zeros(), ones()
#from visual import *  # IMPORTS NumPy.*, SciPy.*, and Visual objects (sphere, box, etc.)
#import matplotlib.pyplot as plt  # plt.plot(x,y)  plt.show()
#from pylab import *  # IMPORTS NumPy.*, SciPy.*, and matplotlib.*
#import os  # os.walk(basedir) FOR GETTING DIR STRUCTURE
#import pickle  # pickle.load(fromfile)  pickle.dump(data, tofile)
#from tkFileDialog import askopenfilename, askopenfile

from PIL import Image, ImageChops
from collections import namedtuple
import os
import time
import ladybug_PyAPI as lady
from ladybug_PyAPI import *
from tracking_pack import ShiTomasiTracking
from datetime import datetime
import pexif
from numpy import array

#===============================================================================
# ENUMERATIONS CARRIED OVER FROM C++ EXAMPLES
#===============================================================================

#===============================================================================
#-----LADYBUG3STREAM CLASS AND METHODS-----
#===============================================================================


class Ladybug3stream:
    '''Methods used by the Ladybug3D GUI application.

    This is a class wrapper around the wrapper functions to include methods
    required by the Ladybug3D application. This includes a method
    to create PGM L-mode files for SIFT processing.
    '''
    # PRESET VALUES
    DISP_COLOR_PROCESSING = LADYBUG_EDGE_SENSING
#    DISP_COLOR_PROCESSING = LADYBUG_DOWNSAMPLE4
    SIFT_COLOR_PROCESSING = LADYBUG_RIGOROUS
#    DISP_COLOR_PROCESSING = LADYBUG_NEAREST_NEIGHBOR_FAST
    # POINTER BUFFERS
    next_frame = 0


    def __init__(self, ladybug_PGR_fname):
        self.ladybug = LadybugAPI( ladybug_PGR_fname )

    def __del__(self):
        del self.ladybug



    def loadframe(self, goto, *args, **kwargs ):
        '''Loads images at pointer position into buffers.

        Moves stream pointer to frame given as an argument. The API method
        auto forwards pointer to be ready for the next image. Add the string
        'SIFT' as a second argument

        @arg goto: (int) The position to move to in the stream file.
            If the string 'SIFT' is in arg list, creates *.SIFTpgm images.
        @return: (bool) True if successful, False if there was an error.
        '''
        # CHECK IF ALREADY POINTING TO DESIRED FRAME. ELSE MOVE POINTER.
        if goto != self.next_frame:
            assert goto >= 0, 'frame is not a positive integer.'
            assert goto < self.ladybug.total_frames, 'frame out of bounds.'
            # MOVE TO NEW POSITION
            self.ladybug.GoToImage( goto )
            self.next_frame = goto

        # READ ONE FRAME FROM STREAM
        self.ladybug.ReadImageFromStream()
        self.next_frame += 1



        # CREATE IMAGES FOR SIFT IF REQUESTED
        if 'SIFT' in args:
            okay = self.create_SIFT_image_set()
            if not okay:
                self.create_display_image_set()
        else:
            self.create_display_image_set()

#        if 'FLOW' in kwargs:
#            print 'FLOW', kwargs['FLOW']
#            tempimg1 = self.image(kwargs['FLOW'])
#            self.ladybug.ReadImageFromStream()
#            tempimg2 = self.image(kwargs['FLOW'])
#
#            width, height = tempimg1.size
#            STTracking = ShiTomasiTracking( height, width )
#            vectors = STTracking.getVectors(tempimg1, tempimg2 )
#            print vectors



        # RETURN TRUE IF THERE WERE NO ERRORS
        return True


    def create_display_image_set(self):
        # SET COLOR PROCESSING METHOD
        self.ladybug.SetColorProcessingMethod( self.DISP_COLOR_PROCESSING )
        # CONVERT THE IMAGE TO BRGU FORMAT TEXTURE BUFFERS
        self.ladybug.ConvertToMultipleBGRU32()


    def create_SIFT_image_set(self):
        '''Creates *.SIFTpgm image files for SIFT to process.

        Checks if *.key or *.SIFTpgm files have been created. Returns False
        if they are already completed.
        '''
        # GET IMAGE INFORMATION
        imCols = self.ladybug.ladybugImage.uiCols
        imRows = self.ladybug.ladybugImage.uiRows
        # CHECK IF *.SIFTppm or *.key EXISTS ALREADY FOR EACH IMAGE
        create_these = []
        for cam in range(5): # IGNORE SIXTH CAMERA
            basename = 'ladybug_raw{0}x{1}_Frame{2:0>8}_Cam{3}'.format(
                            imCols, imRows, self.next_frame-1, cam )
            if (not os.path.exists( basename + '.key' ) and
                not os.path.exists( basename + '.SIFTpgm' ) ):
                create_these.append( cam )
        if len(create_these) == 0:
            print 'Files already created:', self.next_frame-1
            return False

        # SET COLOR PROCESSING METHOD FOR SIFT IMAGES
        self.ladybug.SetColorProcessingMethod( self.SIFT_COLOR_PROCESSING )

        # TRANSFER FRAME FROM STREAM TO IMAGE BUFFERS
        self.ladybug.ConvertToMultipleBGRU32()

        # RETRIEVE AND SAVE IMAGE SET
        for cam in create_these:
            outimage = self.image(cam).convert('L')
            savename = 'ladybug_raw{0}x{1}_Frame{2:0>8}_Cam{3}.SIFTpgm'.format(
                            imCols, imRows, self.next_frame-1, cam )
            print 'SAVED:', savename
            outimage.save( savename, "PPM" )



    def image(self, cam):
        '''Retrieve a single camera's image from set loaded into buffer.

        @PRECONDITION: run the load() method to retrieve image
        set from stream file and place into image buffers.

        @arg cam: (int) The camera position that recorded the image.
        @return: (Image) A PIL Image class 3-band image.
        '''
        return self.ladybug.GetImageFromBuffer(cam).rotate(-90).convert('RGB')


    def getGPSdata(self, *args):
        '''Retrieve the GPS data for one frame or all frames.

        Default is to return the GPS data for the frame currently loaded into
        image buffers. If 'ALL' is given as an argument, a complete listing
        of GPS data for all frames will be returned.

        @param args: Only acceptable param is the string 'ALL'.
        '''
        pass

    def getNumberOfFrames(self):
        return self.ladybug.total_frames

    def getFrameInfo(self):
        frameInfo = namedtuple('frameInfo', 'frame seqid lat lon alt time microsec' )
        return frameInfo(self.next_frame-1,
                         self.ladybug.ladybugImage.ulSequenceId,
                         self.ladybug.ladybugImage.dGPSLatitude,
                         self.ladybug.ladybugImage.dGPSLongitude,
                         self.ladybug.ladybugImage.dGPSAltitude,
                         time.ctime(self.ladybug.ladybugImage.ulTimeSeconds),
                         self.ladybug.ladybugImage.ulTimeMicroSeconds ), \
                         self.ladybug.GetGPSNMEADataFromImage()

    def getVideoGPSlog(self):
        log = self.get_frame_gps_log()
        # MOVE POINTER BACK TO PREVIOUS POSITION AND RELOAD
        self.ladybug.GoToImage( self.next_frame - 1 )
        self.ladybug.ReadImageFromStream()
        return log

    def save_panorama(self, savename='C:/', carfront=None, heading=None, addGPS=True ):
        '''

        @kwarg savename: str - save location for image file
        @kwarg offset: tuple(int,int) - shift image in the (x, y) direction
        '''

        print 'loaded', self.ladybug.isConfigFileLoaded

        self.ladybug.SetAlphaMasking(True)
        self.ladybug.InitializeAlphaMasks()
#        self.ladybug.SetOffScreenImageSize()
        self.ladybug.SetColorProcessingMethod(LADYBUG_RIGOROUS)

        self.ladybug.GoToImage( self.next_frame - 1 )
        self.ladybug.ReadImageFromStream()

        self.ladybug.ConvertToMultipleBGRU32()
        self.ladybug.UpdateTextures()
        self.ladybug.RenderOffScreenImage(LADYBUG_PANORAMIC)

        # SAVE IMAGE
        savename += str(self.next_frame-1) + '.jpg'
        self.ladybug.SaveImage(savename, LADYBUG_FILEFORMAT_JPG)

        # OFFSET IMAGE HORIZONTALLY (WRAPS AROUND)
        if carfront:
            im = Image.open(savename)
            sizex = im.size[0]
            if heading:
                xoffset = int((3/4.)*sizex - carfront - heading*sizex/360.)
            else:
                xoffset = sizex/2 - int(carfront)
            im = ImageChops.offset(im, xoffset, 0 )
            im.save(savename, "JPEG")

        # ADD GPS DATA TO IMAGE FILE
        if addGPS:
            self.addGPStoJPEG(savename )

        return savename



    def closeStream(self):
        del self.ladybug


    def rectifyPixel(self, cam, x_arr, y_arr):
        '''Retrieves the rectified pixel position in an upright image.
        (API is sideways. This will handle the rotation.)
        '''
        if isinstance(x_arr, (int,list)):
            x_arr = array(list(x_arr))
        if isinstance(y_arr, (int,list)):
            y_arr = array(list(y_arr))
        if len(x_arr) != len(y_arr):
            print 'Array lengths are not equal'
            return
        rx = 1231 - x_arr.copy().astype(int) # AXIS ROTATED IN API
        ry = y_arr.copy().astype(int)
#        if isConfigLoaded() == False:
#            self.ladybug.LoadConfig()
#            self.ladybug.SetRectifyResolution()

        for i, (x, y) in enumerate(zip(rx, ry)):
            x, y = self.ladybug.RectifyPixel( cam, x, y )
            rx[i], ry[i] = x, y
        rx = 1231 - rx
        return rx, ry

    def unrectifyPixel(self, cam, xx, yy):
        '''Retrieves the rectified pixel position in an upright image.
        (API is sideways. This will handle the rotation.)
        '''
        try:
            rx = 1231 - xx.copy().astype(int) # AXIS ROTATED IN API
            ry = yy.copy().astype(int)

            for i, (x, y) in enumerate(zip(rx, ry)):
                x, y = self.ladybug.UnrectifyPixel( cam, x, y )
                rx[i], ry[i] = x, y
            rx = 1231 - rx
            return rx, ry
        except:
            pass

        rx = 1231 - xx # AXIS ROTATED IN API
        ry = yy
#        if isConfigLoaded() == False:
#            self.ladybug.LoadConfig()
#            self.ladybug.SetRectifyResolution()

        rx, ry = self.ladybug.UnrectifyPixel( cam, rx, ry )
        rx = 1231 - rx
        return rx, ry

    def getExtrinsics(self):
        edata = self.ladybug.GetCameraUnitExtrinsics( 3)
        print repr(edata)


    def get_frame_gps_log(self):
        dt = [('frame', int), ('seqid', int), ('skipped', int),
              ('valid', bool),
              ('lat', float), ('lon', float), ('alt', float),
              ('gpsUTC', datetime), ('imageUTC', datetime)]
        table = zeros(self.ladybug.total_frames, dtype=dt)


        self.ladybug.GoToImage( 0 )
        last_seq = -1
        for i in xrange( self.ladybug.total_frames ):
            if i%100 == 0: print i,
            LImage = self.ladybug.ReadImageFromStream()

            skipped = 0
            if last_seq == -1:
                last_seq = LImage.ulSequenceId
            else:
                skipped = LImage.ulSequenceId - last_seq - 1
                last_seq = LImage.ulSequenceId


            try:
                gpsdata = self.ladybug.GetGPSNMEADataFromImage("GPRMC")
                dt = datetime( year=gpsdata.wRMCYear,
                                  month=gpsdata.ucRMCMonth,
                                  day=gpsdata.ucRMCDay,
                                  hour=gpsdata.ucRMCHour,
                                  minute=gpsdata.ucRMCMinute,
                                  second=gpsdata.ucRMCSecond,
                                  microsecond=gpsdata.wRMCSubSecond)
                valid = True if gpsdata.ucRMCDataValid == 65 else False
            except:
                dt = datetime.min
                valid = False

            table[i] = (i, # FRAME NUMBER
                        LImage.ulSequenceId,
                        skipped,
                        valid,
                        LImage.dGPSLatitude,
                        LImage.dGPSLongitude,
                        LImage.dGPSAltitude,
                        dt,
                        datetime.utcfromtimestamp(LImage.ulTimeSeconds).replace(microsecond=LImage.ulTimeMicroSeconds)
                        )
        print table.nbytes
        print table.dtype
        return table

    def addGPStoJPEG(self, pszPath ):
        '''This method adds GPS data to a JPEG file. Use after ladybugSaveImage
        if data is not saved in image.

        '''
        jpeg = pexif.JpegFile.fromFile( pszPath )
        jpeg.set_geo(self.ladybug.ladybugImage.dGPSLatitude,
                     self.ladybug.ladybugImage.dGPSLongitude )
        jpeg.exif.primary.GPS.GPSAltitude = \
            [pexif.Rational(self.ladybug.ladybugImage.dGPSAltitude * 10, 10)]
        jpeg.writeFile( pszPath )


    def test(self):
        print self.ladybug.GetImageRenderingInfo()
        flen = self.ladybug.GetCameraUnitFocalLength
        imcen = self.ladybug.GetCameraUnitImageCenter
        print flen(0), flen(1), flen(2), flen(3), flen(4), flen(5)
        print imcen(0), imcen(1), imcen(2), imcen(3), imcen(4), imcen(5)