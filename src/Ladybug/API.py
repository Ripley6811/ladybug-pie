#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Python wrapper class for ladybug.dll methods. 

Import LadybugAPI as ladybug.
Access methods with ladybug.method()
    - For example, the dll method called:
        ladybugGetStreamNumOfImages( LadybugStreamContext *context*, unsigned int *puiImages* )
    is accessed through this module with:
        ladybug.GetStreamNumOfImages()

The API is implemented as a class so that multiple videos can be separately initialized
and managed. The 'ladybug context', 'ladybug stream context', and image buffer are managed
by the class (hidden from the user). In other words, when reading about a method in the 
Ladybug SDK Help, you can omit the context, readContext, and all empty pointers when
calling the Python version. Methods return the expected data instead of an error value.
Errors returned from API are changed to raised warnings and return strings.

:AUTHOR: Ripley6811
:ORGANIZATION: National Cheng Kung University, Department of Earth Sciences
:CONTACT: jwj@boun.cr
:SINCE: Tue May 08 09:17:43 2012
:TODO: ...
"""
#===============================================================================
# PROGRAM METADATA
#===============================================================================
__author__ = 'Ripley6811'
__contact__ = 'jwj@boun.cr'
__copyright__ = ''
__license__ = ''
__date__ = 'Tue May 08 09:17:43 2012'
__version__ = '0.1'

#===============================================================================
# IMPORT
#===============================================================================
from ctypes import CDLL, create_string_buffer, POINTER, c_char, c_int, byref, c_uint, c_double, string_at
from PIL import Image
import os
from struct import unpack
from structures import *
from enums import *



c = CDLL('ladybug')

class LadybugAPI:
    """Instantiate with a Ladybug3 stream file. This class maintains the local
    variables"""
    def __init__(self, stream_fname):
        # STORE REFERENCE VARIABLES
        self.next_frame = None # INDEX OF NEXT FRAME TO READ
        self.isConfigFileLoaded = False
        self.dirname = os.path.dirname(stream_fname)
        self.ladybugImage = None
        self.total_frames = None

        # SET UP INTERNAL ctypes VARIABLES AND pointers
        self.context = c_int()
        self.readContext = create_string_buffer(4)

        self.pLadybugImage = create_string_buffer(188)
        self.pLadybugProcessedImage = create_string_buffer(45)
        self.arpBGRU32Images = (POINTER(c_char) * 6)()
        self.arpBGRU32Images[:] = [create_string_buffer(1616 * 1232 * 4) for i in xrange(6)]
        self.pszConfigFileName = os.path.join(self.dirname, 'config.txt')

        # RUN INITIAL METHODS FOR SETTING UP READING STREAM
        self.CreateContext()
        self.CreateStreamContext()
        self.InitializeStreamForReading( stream_fname )
        self.GetStreamNumOfImages()
        self.SetColorTileFormat( self.GetStreamHeader().stippledFormat )
        self.LoadConfig()
        self.ConfigureOutputImages(LADYBUG_PANORAMIC) # MAY NEED TO ADD OTHER TYPES LATER

    def __del__(self):
        self.StopStream()
        self.DestroyStreamContext()
        self.DestroyContext()


    def CreateContext(self):
        '''Creates a new context for accessing the camera-specific functions of
        the library.

        This method must be called before all other methods that require 'context'.
        '''
        e = c.ladybugCreateContext( byref(self.context) )
        check(e)


    def DestroyContext(self):
        '''Frees memory associated with the LadybugContext.

        '''
        e = c.ladybugDestroyContext( self.context )
        check(e)


    def CreateStreamContext(self):
        '''Creates a new Ladybug stream context.

        This method must be called before all other methods that require 'readContext'.
        '''
        e = c.ladybugCreateStreamContext( self.readContext )
        check(e)



    def DestroyStreamContext(self):
        '''Destroys a Ladybug stream context.

        '''
        e = c.ladybugDestroyStreamContext( self.readContext )
        check(e)



    def GetStreamConfigFile(self):
        '''Reads the configuration data from the stream and writes it to a
        configuration file.

        '''
        e = c.ladybugGetStreamConfigFile(self.readContext,
                                            self.pszConfigFileName )
        check(e)



    def GetStreamHeader(self):
        '''Initializes the context and opens the stream file(s) for reading. Sets
        the current reading position to the first image in the stream.

        '''
        pStreamHeaderInfo = create_string_buffer(3056)

        e = c.ladybugGetStreamHeader(self.readContext,
                                        pStreamHeaderInfo,
                                        None)
        check(e)
        self.next_frame = 0
        return getLadybugStreamHeadInfo( pStreamHeaderInfo )



    def GetStreamNumOfImages(self):
        '''Gets the total number of images in a stream.

        :return: (int) Total number of frames in all associated stream files.
        '''
        totalFrames = c_int()
        e = c.ladybugGetStreamNumOfImages(self.readContext,
                                             byref(totalFrames) )
        check(e)
        self.total_frames = totalFrames.value
        return self.total_frames



    def GoToImage(self, gotoframe ):
        '''Sets the current reading position to the specified position in the stream.

        '''
        e = c.ladybugGoToImage( self.readContext, gotoframe )
        check(e)
        self.next_frame = gotoframe



    def InitializeStreamForReading(self, ladybug_PGR_filename ):
        '''Initializes the context and opens the stream file(s) for reading. Sets
        the current reading position to the first image in the stream.

        '''
        e = c.ladybugInitializeStreamForReading(self.readContext,
                                                   ladybug_PGR_filename)
        check(e)
        self.next_frame = 0



    def ReadImageFromStream(self):
        '''Reads the image that is located at the current reading position of the
        stream and sets the reading position to the next image.

        Loads ladybug image data into buffer and returns the image data as namedtuple.
        '''
        e = c.ladybugReadImageFromStream(self.readContext,
                                            self.pLadybugImage )  # WRITABLE BUFFER
        check(e)

        self.next_frame += 1
        self.ladybugImage = getLadybugImage( self.pLadybugImage )
        return self.ladybugImage



    def WriteGPSSummaryDataToFile(self, gps_filename=None,
                                  LadybugGPSFileType=LADYBUG_GPS_TXT ):
        '''Writes the GPS summary data from a stream to a specified file.

        '''
        if gps_filename:
            pszTxtFileName = create_string_buffer( gps_filename )
        else:
            pszTxtFileName = create_string_buffer( os.path.join(self.dirname,
                                                                'GPSsummary.txt') )

        e = c.ladybugWriteGPSSummaryDataToFile(self.readContext,
                                                  pszTxtFileName,
                                                  LadybugGPSFileType )
        check(e)



    def SetColorTileFormat(self, LadybugStippledFormat_selection ):
        '''Sets the current color tile format.
        Selecting LadybugStippledFormat.LADYBUG_BGGR is recommended.
        '''
        e = c.ladybugSetColorTileFormat(self.context,
                                           LadybugStippledFormat_selection)
        check(e)



    def SetColorProcessingMethod(self, color_processing_method ):
        '''Sets the color processing method to use.

        '''
        e = c.ladybugSetColorProcessingMethod(self.context,
                                                 color_processing_method )
        check(e)



    def SetRectifyResolution(self, uiDestCols=1616, uiDestRows=1232):
        '''Sets the resolution of inputted raw images and outputted rectified images.

        :PRECONDITION: Required calls before this method.
            - Call ladybugLoadConfig()
        '''
        e = c.ladybugSetRectifyResolution(self.context,
                                c_uint(uiDestCols),
                                c_uint(uiDestRows),
                                c_uint(self.ladybugImage.uiCols),
                                c_uint(self.ladybugImage.uiRows)   )
        check(e)



    def RectifyPixel(self, uiCamera, dDistortedRow, dDistortedCol ):
        '''Maps a distorted (raw) pixel location to its corresponding point in the
        rectified image.

        :PRECONDITION: Required calls before this method.
            - ladybugLoadConfig()
            - ladybugSetRectifyResolution()
        '''
        pdRectifiedRow = create_string_buffer(8)
        pdRectifiedCol = create_string_buffer(8)
        e = c.ladybugRectifyPixel(self.context, uiCamera,
                                     c_double(dDistortedRow),
                                     c_double(dDistortedCol),
                                     pdRectifiedRow, pdRectifiedCol )
        check(e)
        return (unpack( 'd', pdRectifiedRow )[0], unpack( 'd', pdRectifiedCol )[0])



    def UnrectifyPixel(self, uiCamera, dRectifiedRow, dRectifiedCol ):
        '''Maps a rectified pixel location to its corresponding point in the
        distorted (raw) image.

        :PRECONDITION: Required calls before this method.
            ladybugLoadConfig()
            ladybugSetRectifyResolution()
        '''
        pdDistortedRow = create_string_buffer(8)
        pdDistortedCol = create_string_buffer(8)
        e = c.ladybugUnrectifyPixel(self.context, uiCamera,
                                       c_double(dRectifiedRow),
                                       c_double(dRectifiedCol),
                                       pdDistortedRow, pdDistortedCol )
        check(e)
        return (unpack( 'd', pdDistortedRow )[0], unpack( 'd', pdDistortedCol )[0])


    def SetAlphaMasking(self, bMasking ):
        '''If set to true, invokes the alpha masks to be copied to color images on
        the next call to ladybugConvertToMultipleBGRU32 . As long as you use the
        same color image buffers, you do not have to set this to true every time.

        '''
        e = c.ladybugSetAlphaMasking(self.context, bMasking )
        check(e)


    def GetColorProcessingMethod(self):
        '''Gets the current color processing method.

        '''
        currmethod = c_int()
        e = c.ladybugGetColorProcessingMethod(self.context, byref(currmethod) )
        check(e)
        return currmethod.value



    def ConvertToMultipleBGRU32(self):
        '''Parses the 6 images in a LadybugImage into 6 BGRU32 buffers.

        :PRECONDITION: Required calls before this method.
            ladybugSetColorProcessingMethod() (OPTIONAL)
        '''
        e = c.ladybugConvertToMultipleBGRU32(self.context,
                                                self.pLadybugImage,
                                                self.arpBGRU32Images,
                                                None )
        check(e)



    def ExtractLadybugImageToFilesBGRU32(self, filenames,
                                         saveFileFormat=LADYBUG_FILEFORMAT_BMP):
        '''Converts a LadybugImage to a set of color-processed images.

        :PARAMETERS:
            *filenames* --- A list of six filenames to save each image in camera order.
            **saveformat** --- Save image format. Default is BMP.
        '''
        arpszFilenames = (POINTER(c_char) * 6)()
        arpszFilenames[:] = [create_string_buffer(each) for each in filenames]
        e = c.ladybugExtractLadybugImageToFilesBGRU32(self.context,
                                                         self.pLadybugImage,
                                                         arpszFilenames,
                                                         None,
                                                         saveFileFormat )
        check(e)



    def GetGPSNMEADataFromImage(self, NMEAsentenceID="GPGGA"):
        '''Gets the GPS data for the specified NMEA sentences from a Ladybug image.

        GPS info can also be conveniently retrieved from LadybugImageInfo.

        TODO: GPVTG, GPZDA, GPGLL not available to test
        '''
        if NMEAsentenceID == "GPGGA": buffer_size = 116
        if NMEAsentenceID == "GPRMC": buffer_size = 116
        if NMEAsentenceID == "GPVTG": buffer_size = 108
        if NMEAsentenceID == "GPZDA": buffer_size = 72
        if NMEAsentenceID == "GPGLL": buffer_size = 92
        if NMEAsentenceID == "GPGSA": buffer_size = 172

        if not buffer_size: return

        gpsData = create_string_buffer(buffer_size)

        e = c.ladybugGetGPSNMEADataFromImage(self.pLadybugImage,
                                                NMEAsentenceID,
                                                gpsData)
        check(e)

        if NMEAsentenceID == "GPGGA": return getLadybugNMEAGPGGA(gpsData)
        if NMEAsentenceID == "GPRMC": return getLadybugNMEAGPRMC(gpsData)
        if NMEAsentenceID == "GPVTG": return getLadybugNMEAGPVTG(gpsData)
        if NMEAsentenceID == "GPZDA": return getLadybugNMEAGPZDA(gpsData)
        if NMEAsentenceID == "GPGLL": return getLadybugNMEAGPGLL(gpsData)
        if NMEAsentenceID == "GPGSA": return getLadybugNMEAGPGSA(gpsData)




    def LoadConfig(self):
        '''Loads a configuration file containing intrinsic and extrinsic camera
        properties.

        This function must be called once before any calls involving 3D mapping and
        rectification are performed. An error occurs if called a second time.

        :PRECONDITION: Required calls before this method.
            ladybugGetStreamConfigFile() (IF CONFIG FILE DOES NOT EXIST)
        '''
        # CHECK IF ALREADY LOADED. ONLY LOAD ONCE.
        if self.isConfigFileLoaded: return

        # CHECK IF CONFIG FILE EXISTS ELSE CREATE IT
        if not os.path.exists( self.pszConfigFileName ):
            self.GetStreamConfigFile()

        # RUN API METHOD
        e = c.ladybugLoadConfig(self.context, self.pszConfigFileName )
        check(e)
        self.isConfigFileLoaded = True



    def ConfigureOutputImages(self, LadybugOutputImage_SELECTION):
        '''Configures the Ladybug library for generating Ladybug output images for
        on-screen and off-screen rendering.

        Can be a combination of types in enum LadybugOutputImage

        :PRECONDITION: Required calls before this method.
            ladybugLoadConfig()
        Call this function before:
            ladybugSetDisplayWindow()
            ladybugDisplayImage()
            ladybugRenderOffScreenImage()
            ladybugGetOpenGLTextureID()

        '''
        e = c.ladybugConfigureOutputImages(self.context,
                                              LadybugOutputImage_SELECTION )
        check(e)



    def UpdateTextures(self):
        '''Moves images from buffers to the graphics card for rendering.

        :PRECONDITION:
        '''
        e = c.ladybugUpdateTextures(self.context,
                                       6, # NUMBER OF CAMERAS
                                       self.arpBGRU32Images ) # POSSIBLE PROBLEM: REQUIRES BGRA
        check(e)



    def InitializeAlphaMasks(self):
        '''Moves images from buffers to the graphics card for rendering.
        Assumes image size of 1616x1232.

        :PRECONDITION:
            ladybugSetRectifyResolution()
        '''
        e = c.ladybugInitializeAlphaMasks(self.context,
                                             self.ladybugImage.uiCols,
                                             self.ladybugImage.uiRows )
        check(e)


    def SetOffScreenImageSize(self, imageType=LADYBUG_PANORAMIC,
                              uiCols=2048, uiRows=1024 ):
        e = c.ladybugSetOffScreenImageSize(self.context,
                                              imageType,
                                              uiCols,
                                              uiRows )
        check(e)


    def RenderOffScreenImage(self, LadybugOutputImage_selection):
        '''Renders an off-screen image and gets the image from the off-screen
        buffer.

        The size of the image will be defined by the default value or can
        be set by ladybugSetOffScreenImageSize() beforehand.

        :PRECONDITION: Required calls before this method.
            ladybugConfigureOutputImages()
            ladybugSetOffScreenImageSize() (OPTIONAL)
        '''
        e = c.ladybugRenderOffScreenImage(self.context,
                                         LadybugOutputImage_selection,
                                         self.pLadybugProcessedImage ) # BUFFER
        check(e)


    def GetImageRenderingInfo(self ):
        '''Returns information about the graphics card and OpenGL implementation.

        '''
        pRenderingInfo = create_string_buffer(4964)
        e = c.ladybugGetImageRenderingInfo(self.context,
                                              pRenderingInfo )
        check(e)
        return getLadybugImageRenderingInfo(pRenderingInfo )


    def ReleaseOffScreenImage(self, imageTypes=LADYBUG_PANORAMIC ):
        '''If not release with this method, they will be released when context
        is destroyed.
        '''
        e = c.ladybugReleaseOffScreenImage(self.context,
                                             imageTypes )
        check(e)




    def GetCameraUnitExtrinsics(self, uiCamera ):

        ardEulerZYX = create_string_buffer(48)

        e = c.ladybugGetCameraUnitExtrinsics(self.context, uiCamera,
                                                ardEulerZYX ) # WRITABLE BUFFER
        check(e)

        data = unpack('dddddd', ardEulerZYX)
        name = ('Rx','Ry','Rz','Tx','Ty','Tz')
        return dict(zip(name,data))


    def GetCameraUnitFocalLength(self, uiCamera ):
        '''Gets the focal length (in pixels) for the specified camera unit.

        '''
        pdFocalLength = create_string_buffer(8)

        e = c.ladybugGetCameraUnitFocalLength(self.context,
                                                 uiCamera, pdFocalLength  )
        check(e)

        return unpack('d', pdFocalLength )[0]



    def GetCameraUnitImageCenter(self, uiCamera ):
        '''Gets the rectified image center for the specified camera unit.

        '''
        pdCenterX = create_string_buffer(8)
        pdCenterY = create_string_buffer(8)

        e = c.ladybugGetCameraUnitImageCenter(self.context, uiCamera,
                                                 pdCenterX, pdCenterY )

        check(e)

        return unpack('d', pdCenterX )[0], unpack('d', pdCenterY )[0]




    def SaveImage(self, pszPath, LadybugSaveFileFormat=LADYBUG_FILEFORMAT_JPG):
        '''Saves off screen image to file.
        Use LadybugSaveFileFormat.LADYBUG_FILEFORMAT_JPG as a default

        :PRECONDITION:
            pLadybugProcessedImage buffer must be overwritten with data using the
            ladybugRenderOffScreenImage method
        '''
        e = c.ladybugSaveImage(self.context,
                                  self.pLadybugProcessedImage,
                                  pszPath,
                                  LadybugSaveFileFormat )
        check(e)


    def SetImageSavingJpegQuality(self, iQuality):
        '''Sets the JPEG compression save quality.

        Value from 1 to 100. Default is 85
        '''
        e = c.ladybugSetImageSavingJpegQuality(self.context,
                                                  iQuality)
        check(e)



    def StopStream(self):
        e = c.ladybugStopStream(self.readContext )
        check(e)


    def Get3dMap(self, uiCamera ):
        '''Test this again...
        '''
        uiGridCols = c_uint(32)
        uiGridRows = c_uint(24)
        uiSrcCols = c_uint(1616)
        uiSrcRows = c_uint(1232)
        pLadybugImage3d = create_string_buffer(1000)
        e = c.ladybugGet3dMap(self.context, uiCamera,
                                   uiGridCols,
                                   uiGridRows,
                                   uiSrcCols,
                                   uiSrcRows,
                                   False,
                                   pLadybugImage3d )
        check(e)
        return getLadybugImage3d(pLadybugImage3d)


    def GetImageFromBuffer(self, cam ):
        '''(Not from API) Retrieve a single camera's image from the image buffer.
        
        The ladybug class manages the image buffer. Call ladybug.ConvertToMultipleBGRU32
        then retrieve a single camera's image with this method.

        :PRECONDITION:
            **ladybugConvertToMultipleBGRU32** must be called first.

        :PARAMETERS:
            *cam* --- (int) The camera position that recorded the image.
        
        :RETURNS: (Image) A PIL Image class 4-band image.
        '''
        assert cam in range(6)
        LadybugImage = getLadybugImage( self.pLadybugImage )
        imCols, imRows = LadybugImage.uiCols, LadybugImage.uiRows
        if self.GetColorProcessingMethod() == LADYBUG_DOWNSAMPLE4:
            imCols /= 2
            imRows /= 2

        # RETURN A PIL IMAGE
        b,g,r,a = Image.frombuffer('RGB', (imCols,imRows),
                                self.arpBGRU32Images[cam][:imCols * imRows * 4],
                                'raw', 'RGBX', 0, 1).split()
        return Image.merge("RGBA", (r,g,b,a) )



def check(error, stopOnError=True):
    if error:
        if stopOnError:
            raise Warning, string_at( c.ladybugErrorToString( error ) )
        else:
            print 'Warning:', string_at( c.ladybugErrorToString( error ) )
