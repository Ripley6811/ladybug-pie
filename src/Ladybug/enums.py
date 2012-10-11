#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Enumerations used with the Ladybug3 API.

Enumerations (all-caps 'constant' values) for use in interacting with the Ladybug3 API.

:SINCE: Sat Apr 28 19:09:31 2012
:NOTE: Incomplete. Can add the remaining enums from API.

:AUTHOR: Ripley6811
:ORGANIZATION: National Cheng Kung University, Department of Earth Sciences
:CONTACT: python@boun.cr
"""


#===============================================================================
# ENUMERATIONS CARRIED OVER FROM C++ EXAMPLES
#===============================================================================
  
  
#--- enum LadybugColorProcessingMethod
# The available color processing/destippling/de-mosaicing methods.
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
#LadybugColorProcessingMethod = '''
#   LADYBUG_DISABLE
#   LADYBUG_EDGE_SENSING
#   LADYBUG_NEAREST_NEIGHBOR
#   LADYBUG_NEAREST_NEIGHBOR_FAST
#   LADYBUG_RIGOROUS
#   LADYBUG_DOWNSAMPLE4
#   LADYBUG_MONO
#   LADYBUG_HQLINEAR'''.split()
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
