#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
(SUMMARY)

(DESCRIPTION)

@SINCE: Sat Apr 28 19:09:31 2012
@VERSION: 0.1
@STATUS: Nascent
@CHANGE: ...
@TODO: ...

@REQUIRES: ...
@PRECONDITION: ...
@POSTCONDITION: ...

@AUTHOR: Ripley6811
@ORGANIZATION: National Cheng Kung University, Department of Earth Sciences
@CONTACT: python at boun.cr
"""
#===============================================================================
# PROGRAM METADATA
#===============================================================================
__author__ = 'Ripley6811'
__contact__ = 'python at boun.cr'
__copyright__ = ''
__license__ = ''
__date__ = 'Sat Apr 28 19:09:31 2012'
__version__ = '0.1'




from struct import unpack
from collections import namedtuple
from ctypes import Structure, c_uint, c_float, c_double


#===============================================================================
# ENUMERATIONS CARRIED OVER FROM C++ EXAMPLES
#===============================================================================
  
  
#--- enum LadybugColorProcessingMethod
# The available color processing/destippling/de-mosaicing methods.
LadybugColorProcessingMethod = '''
   LADYBUG_DISABLE
   LADYBUG_EDGE_SENSING
   LADYBUG_NEAREST_NEIGHBOR
   LADYBUG_NEAREST_NEIGHBOR_FAST
   LADYBUG_RIGOROUS
   LADYBUG_DOWNSAMPLE4
   LADYBUG_MONO
   LADYBUG_HQLINEAR'''.split()
( 
   LADYBUG_DISABLE,
   LADYBUG_EDGE_SENSING,
   LADYBUG_NEAREST_NEIGHBOR,
   LADYBUG_NEAREST_NEIGHBOR_FAST,
   LADYBUG_RIGOROUS,
   LADYBUG_DOWNSAMPLE4,
   LADYBUG_MONO,
   LADYBUG_HQLINEAR
) = range(8)
# OR ALTERNATIVELY, MAKE ENUM FROM LIST
#for n, v in zip( LadybugColorProcessingMethod, range(8) ):
#    exec( n + ' = ' + str(v) )



#--- enum LadybugIndependentProperty
(
   LADYBUG_SUB_GAIN,
   LADYBUG_SUB_SHUTTER,
   LADYBUG_SUB_AUTO_EXPOSURE
) = range(3)
LADYBUG_SUB_FORCE_QUADLET = 0x7FFFFFFF



#--- enum LadybugSaveFileFormat
# The available color processing/destippling/de-mosaicing methods.
(
   LADYBUG_FILEFORMAT_PGM,
   LADYBUG_FILEFORMAT_PPM,
   LADYBUG_FILEFORMAT_BMP,
   LADYBUG_FILEFORMAT_JPG,
   LADYBUG_FILEFORMAT_PNG
) = range(5)
    
#--- enum LadybugOutputImage
LADYBUG_RAW_CAM0           = ( 0x1 << 0 )
LADYBUG_RAW_CAM1           = ( 0x1 << 1 )
LADYBUG_RAW_CAM2           = ( 0x1 << 2 )
LADYBUG_RAW_CAM3           = ( 0x1 << 3 )
LADYBUG_RAW_CAM4           = ( 0x1 << 4 )
LADYBUG_RAW_CAM5           = ( 0x1 << 5 )
LADYBUG_ALL_RAW_IMAGES     =  0x0000003F

LADYBUG_RECTIFIED_CAM0        = ( 0x1 << 6 )
LADYBUG_RECTIFIED_CAM1        = ( 0x1 << 7 )
LADYBUG_RECTIFIED_CAM2        = ( 0x1 << 8 )
LADYBUG_RECTIFIED_CAM3        = ( 0x1 << 9 )
LADYBUG_RECTIFIED_CAM4        = ( 0x1 << 10 )
LADYBUG_RECTIFIED_CAM5        = ( 0x1 << 11 )
LADYBUG_ALL_RECTIFIED_IMAGES  =  0x00000FC0

LADYBUG_PANORAMIC          = ( 0x1 << 12 )

LADYBUG_DOME               = ( 0x1 << 13 )

LADYBUG_SPHERICAL          = ( 0x1 << 14 )

LADYBUG_ALL_CAMERAS_VIEW   = ( 0x1 << 15 )

LADYBUG_ALL_OUTPUT_IMAGE   = 0x7FFFFFFF

#--- enum LadybugGPSFileType
(
   LADYBUG_GPS_TXT,

   LADYBUG_GPS_HTML,

   LADYBUG_GPS_KML
) = range(3)
LADYBUG_GPS_FILE_TYPE_FORCE_QUADLET = 0x7FFFFFFF,



    

# struct LadybugStreamHeadInfo
def getLadybugStreamHeadInfo( data ):
    '''Ladybug stream file header format.'''
    data = unpack('L'*30 +'I'*3 + 'L'*731, data)
    tmpdict = dict(
        ulLadybugStreamVersion = data[0],
        ulFrameRate = data[1],
        serialBase = data[2],
        serialHead = data[3],
        #reserved = data[4:29],
        ulPaddingSize = data[29],
        dataFormat = data[30],
        resolution = data[31],
        stippledFormat = data[32],
        ulConfigrationDataSize = data[33],
        ulNumberOfImages = data[34], # PER STREAM FILE (2GB)
        ulNumberOfKeyIndex = data[35],
        ulIncrement = data[36],
        ulStreamDataOffset = data[37],
        ulGPSDataOffset = data[38],
        ulGPSDataSize = data[39],
        #reservedSpace = data[40:252],
        ulOffsetTable = data[252:764] )
    return namedtuple('Structure', tmpdict.keys() )(**tmpdict)

# struct LadybugImageRenderingInfo
def getLadybugImageRenderingInfo(data ):
    data = unpack('c'*832 +'I'+ 'c'*64 +'??III' +'c'*128 +'?' +'I'*979, data)
    tmpdict = dict(
        pszDeviceDescription =      ''.join(data[0:128]).rstrip(' \t\r\n\0'),
        pszAdapterString =          ''.join(data[128:256]).rstrip(' \t\r\n\0'),
        pszBiosString =             ''.join(data[256:384]).rstrip(' \t\r\n\0'),
        pszChipType =               ''.join(data[384:512]).rstrip(' \t\r\n\0'),
        pszDacType =                ''.join(data[512:640]).rstrip(' \t\r\n\0'),
        pszInstalledDisplayDriver = ''.join(data[640:768]).rstrip(' \t\r\n\0'),
        pszDriverVersion =          ''.join(data[768:832]).rstrip(' \t\r\n\0'),
        uiMemorySize =              data[832],
        pszOpenGLVersion =          ''.join(data[833:897]).rstrip(' \t\r\n\0'),
        bPBO =                      data[897],
        bFBO =                      data[898],
        uiMaxTextureSize =          data[899],
        uiMaxViewPortWidth =        data[900],
        uiMaxViewPortHeight =       data[901],
        pszOpenGLVendor =           ''.join(data[902:966]).rstrip(' \t\r\n\0'),
        pszOpenGLRenderer =         ''.join(data[966:1030]).rstrip(' \t\r\n\0'),
        bPBuffer =                  data[1030] )
    return namedtuple('Structure', tmpdict.keys() )(**tmpdict)




# The LadybugImage structure.
def getLadybugImage(data):
    data = unpack('IIIILLLLL' +'L'*24 +'dddB?IIILLL', data)
    tmpdict = dict(
        uiCols =            data[ 0 ],
        uiRows =            data[ 1 ],
        dataFormat =        data[ 2 ],
        resolution =        data[ 3 ],
        timeStamp =         data[ 4:9 ],
        # data[ 9 ] skipped. Unimportant??

        # LadybugImageInfo structure included here
        ulFingerprint =     data[10], # 0xCAFEBABE = 3405691582L
        ulVersion =         data[11],
        ulTimeSeconds =     data[12], 
        ulTimeMicroSeconds =data[13], 
        ulSequenceId =      data[14],
        ulHRate =           data[15],
        arulGainAdjust =    [int(n%2**8) for n in data[16:22]],
        ulWhiteBalance =    data[22],
        ulBayerGain =       data[23],
        ulBayerMap =        data[24],
        ulBrightness =      data[25],
        ulGamma =           int(data[26]%2**8),
        ulSerialNum =       data[27],
        ulShutter =         [int(n%2**8) for n in data[28:33]], # The 6th appears to be missing in data!
        dGPSLatitude =      data[33], # Actually at 33, not 34!
        dGPSLongitude =     data[34],
        dGPSAltitude =      data[35],

        pData =             data[ 36 ],
        bStippled =         data[ 37 ],
        uiDataSizeBytes =   data[ 39 ],
        uiSeqNum =          data[ 39 ],
        uiBufferIndex =     data[ 40 ]#,
        #ulReserved =        data[ 41:44 ]
        )
    return namedtuple('Structure', tmpdict.keys() )(**tmpdict)
    
    
# struct LadybugProcessedImage
def getLadybugProcessedImage(data):
    data = unpack('IIBL'+'L'*8, data)
    tmpdict = dict(
        uiCols =            data[ 0 ], # 4 bytes
        uiRows =            data[ 1 ], # 4
        pData =             data[ 2 ], # 1
        pixelFormat =        data[ 3 ], # 4

        ulReserved =        data[ 4:12 ] ) # 4 * 8
    return namedtuple('Structure', tmpdict.keys() )(**tmpdict)
    
    
#  struct LadybugNMEAGPGGA
def getLadybugNMEAGPGGA(data):
    data = unpack('?BBBHddBBdddL'+'L'*14, data)
    tmpdict = dict(
        bValidData =        data[0],
        ucGGAHour =         data[1],
        ucGGAMinute =       data[2],
        ucGGASecond =       data[3],
        wGGASubSecond =     data[4],
        dGGALatitude =      data[5],
        dGGALongitude =     data[6],
        ucGGAGPSQuality =   data[7],
        ucGGANumOfSatsInUse = data[8],
        dGGAHDOP =          data[9],
        dGGAAltitude =      data[10],
        dGGAHeightOfGeoid = data[11],
        ulCount =           data[12]#,
        #ulReserved =        data[13:27]
        )
    return namedtuple('Structure', tmpdict.keys() )(**tmpdict)
    
# struct LadybugNMEAGPRMC
def getLadybugNMEAGPRMC(data):
    data = unpack('?BBBHBddddBBHdL'+'L'*14, data)
    tmpdict = dict(
        bValidData = data[0],
        ucRMCHour = data[1],
        ucRMCMinute = data[2],
        ucRMCSecond = data[3],
        wRMCSubSecond = data[4],
        ucRMCDataValid = data[5],
        dRMCLatitude = data[6],
        dRMCLongitude = data[7],
        dRMCGroundSpeed = data[8],
        dRMCCourse = data[9],
        ucRMCDay = data[10],
        ucRMCMonth = data[11],
        wRMCYear = data[12],
        dRMCMagVar = data[13],
        ulCount = data[14]#,
        #ulReserved = data[15:29]
        )
    return namedtuple('Structure', tmpdict.keys() )(**tmpdict)
    

# struct LadybugNMEAGPVTG
def getLadybugNMEAGPVTG(data):
    data = unpack('?ddddL'+'L'*16, data)
    tmpdict = dict(
       bValidData = data[0],
       dVTGTrackMadeGood = data[1],
       dVTGMagneticTrackMadeGood = data[2],
       dVTGGroundSpeedKnots = data[3],
       dVTGGroundSpeedKilometersPerHour = data[4],
       ulCount = data[5]#,
       #ulReserved = data[6:22]
       )
    return namedtuple('Structure', tmpdict.keys() )(**tmpdict)


# struct LadybugNMEAGPZDA
def getLadybugNMEAGPZDA(data):
    data = unpack('?BBBHBBHBBL'+'L'*14, data)
    tmpdict = dict(
        bValidData = data[0],
        ucZDAHour = data[1],
        ucZDAMinute = data[2],
        ucZDASecond = data[3],
        wZDASubSecond = data[4],
        ucZDADay = data[5],
        ucZDAMonth = data[6],
        wZDAYear = data[7],
        ucZDALocalZoneHour = data[8],
        ucZDALocalZoneMinute = data[9],
        ulCount = data[10]#,
        #ulReserved = data[11:25]
        )
    return namedtuple('Structure', tmpdict.keys() )(**tmpdict)


# struct LadybugNMEAGPGLL
def getLadybugNMEAGPGLL(data):
    data = unpack('?ddBBBHBL'+'L'*14, data)
    tmpdict = dict(
        bValidData = data[0],
        dGLLLatitude = data[1],
        dGLLLongitude = data[2],
        ucGLLHour = data[3],
        ucGLLMinute = data[4],
        ucGLLSecond = data[5],
        wGLLSubSecond = data[6],
        ucGLLDataValid = data[7],
        ulCount = data[8]#,
        #ulReserved = data[9:23]
        )
    return namedtuple('Structure', tmpdict.keys() )(**tmpdict)


# struct LadybugNMEAGPGSA
def getLadybugNMEAGPGSA(data):
    data = unpack('?BB'+'H'*36+'dddL'+'L'*16, data)
    tmpdict = dict(
        bValidData = data[0],
        ucGSAMode = data[1],
        ucGSAFixMode = data[2],
        wGSASatsInSolution = data[3:39],
        dGSAPDOP = data[39],
        dGSAHDOP = data[40],
        dGSAVDOP = data[41],
        ulCount = data[42]#,
        #ulReserved = data[43:59]
        )
    return namedtuple('Structure', tmpdict.keys() )(**tmpdict)


class LadybugPoint3d(Structure):
    _fields_ = [('fX', c_float),
                ('fY', c_float),
                ('fZ', c_float),
                ('fTheta', c_float),
                ('fPhi', c_float),
                ('fCylAngle', c_float),
                ('fCylHeight', c_float)]
                
class LadybugImage3d(Structure):
    _fields_ = [("uiRows", c_uint),
                ("uiCols", c_uint),
                ('dRx', c_double),
                ('dRy', c_double),
                ('dRz', c_double),
                ('dTx', c_double),
                ('dTy', c_double),
                ('dTz', c_double),
                ('fCylHeightMin', c_float),
                ('fCylHeightMax', c_float),
                ('LadybugPoint3d', LadybugPoint3d)]
                
# The LadybugImage structure.
def getLadybugImage3d(data):
    data = unpack('IIddddddfffffffff', data)
    tmpdict = dict(
        uiRows =            data[ 0 ],
        uiCols =            data[ 1 ],
        dRx =               data[ 2 ],
        dRy =               data[ 3 ],
        dRz =               data[ 4 ],
        dTx =               data[ 5 ],
        dTy =               data[ 6 ],
        dTz =               data[ 7 ],
        fCylHeightMin =     data[ 8 ],
        fCylHeightMax =     data[ 9 ],
        fX =                data[10 ],
        fY =                data[11 ],
        fZ =                data[12 ],
        fTheta =            data[13 ],
        fPhi =              data[14 ],
        fCylAngle =         data[15 ],
        fCylHeight =        data[16 ]
        )
    return namedtuple('Structure', tmpdict.keys() )(**tmpdict)
