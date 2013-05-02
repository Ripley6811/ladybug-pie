#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
summary

description

:REQUIRES:

:TODO:

:AUTHOR: Ripley6811
:ORGANIZATION: National Cheng Kung University, Department of Earth Sciences
:CONTACT: python@boun.cr
:SINCE: Sat Apr 27 18:37:36 2013
:VERSION: 0.1
"""
#===============================================================================
# PROGRAM METADATA
#===============================================================================
__author__ = 'Ripley6811'
__contact__ = 'python@boun.cr'
__copyright__ = ''
__license__ = ''
__date__ = 'Sat Apr 27 18:37:36 2013'
__version__ = '0.1'

#===============================================================================
# IMPORT STATEMENTS
#===============================================================================
import numpy as np  # IMPORTS ndarray(), arange(), zeros(), ones()
np.set_printoptions(precision=5)
np.set_printoptions(suppress=True)
import sys
sys.path.append("..") # Access modules that are one level up
from interface import Ladybug3stream


#===============================================================================
# METHODS
#===============================================================================






#===============================================================================
# MAIN METHOD AND TESTING AREA
#===============================================================================
def main():
    """Description of main()"""
    filename = r'E:\Ladybug3 Video\20101210 - Suhua - PGR original\Ladybug-Retrun-000000.pgr'
    ladybug = Ladybug3stream(filename)
    for i in range(100):
        ladybug.loadframe(65*i)
#        print ladybug.getFrameInfo()
        gps = ladybug.getGPSdata()
        print 65*i, 'HDOP', gps['dGGAHDOP'], '#Sats', gps['ucGGANumOfSatsInUse'], 'Quality', gps['ucGGAGPSQuality'],
        print 'Lat', gps['dRMCLatitude'], 'Lon', gps['dRMCLongitude'], 'Alt', gps['dGGAAltitude']
    #    log = ladybug.getVideoGPSlog()
    #    print log


    del ladybug



if __name__ == '__main__':
    main()


