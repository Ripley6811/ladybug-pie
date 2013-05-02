#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Analyze Ladybug 3 PGR video GPS data and returned SLAM enhanced data.

This module takes a Ladybug recording and returns an enhanced list of GPS
positions. Uses SFM and SLAM to improve the recorded GPS data.

:ALGORITHM:
    FOR each frame:
        get 2D pts with descriptors
        IF frame # > 0:
            calculate distances to previous frames (overwrite, not accumulate)
            IF not done and distance > min dist:
                calculate 3D pts from correspondences
                add 3D pt measurements and estimated motion to SLAM
        update motion from solving SLAM matrix


:REQUIRES: PGR Video must include GPS data.

:TODO:

:AUTHOR: Ripley6811
:ORGANIZATION: National Cheng Kung University, Department of Earth Sciences
:CONTACT: python@boun.cr
:SINCE: Tue Apr 30 12:01:05 2013
:VERSION: 0.1
"""
#===============================================================================
# PROGRAM METADATA
#===============================================================================
__author__ = 'Ripley6811'
__contact__ = 'python@boun.cr'
__copyright__ = ''
__license__ = ''
__date__ = 'Tue Apr 30 12:01:05 2013'
__version__ = '0.1'

#===============================================================================
# IMPORT STATEMENTS
#===============================================================================
from numpy import *  # IMPORTS ndarray(), arange(), zeros(), ones()
set_printoptions(precision=5)
set_printoptions(suppress=True)
#from visual import *  # IMPORTS NumPy.*, SciPy.*, and Visual objects (sphere, box, etc.)
import matplotlib.pyplot as plt  # plt.plot(x,y)  plt.show()
#from pylab import *  # IMPORTS NumPy.*, SciPy.*, and matplotlib.*
#import os  # os.walk(basedir) FOR GETTING DIR STRUCTURE
#import pickle  # pickle.load(fromfile)  pickle.dump(data, tofile)
#from tkFileDialog import askopenfilename, askopenfile
#from collections import namedtuple
#from ctypes import *
#import glob
#import random
#import cv2
from Ladybug.interface import Ladybug3stream
from SFM.online_SLAM import SLAM
from SFM.opticflow import FeatureMatcher, flann_matcher
from UI.gpsmath import calc_dist_haver, calc_dist_cos

#===============================================================================
# METHODS
#===============================================================================






#===============================================================================
# MAIN METHOD AND TESTING AREA
#===============================================================================
def main(filename = r'E:\Ladybug3 Video\20101210 - Suhua - PGR original\Ladybug-Retrun-000000.pgr'):
    """Run program on a *.PGR file."""

    ladybug = Ladybug3stream(filename)
    total_frames = ladybug.getNumberOfFrames()
    print 'Total frames:', total_frames

    # Frames to calculate
    cam = 3
    MIN_DIST = 2. # meters
    start, end = 0, 20 #, total_frames
    end = end if end < total_frames else total_frames - 1

    # Track completed 3D pt calculations and frame distances
    triangulated = [] # False when 2D-image pts acquired, True if 3D-world pts.
    positions = [] # Store GPS or updated coordinates.
    fm = {} # Dictionary of feature matchers keyed by frame number
    keys = []
    desc = []

    # Iterate through frames
    for fn in range(start, end):
        ladybug.loadframe(fn)

        gps = ladybug.getGPSdata()

        if True: # Print debug data
            print 'F', fn, 'HDOP', gps['dGGAHDOP'], '#Sats', gps['ucGGANumOfSatsInUse'], 'Quality', gps['ucGGAGPSQuality'],
            print 'Lat', gps['dRMCLatitude'], 'Lon', gps['dRMCLongitude'], 'Alt', gps['dGGAAltitude']

        fm[0] = FeatureMatcher()
        image = ladybug.image( cam )
#        image.show()
        k, d = fm[0].getkeys( asarray(image) )
#        k, d = fm[0].add( asarray(image) )
        keys.append(k)
        desc.append(d)

        if False:
            print 'F', i, 'keys:', len(keys[-1])
            plt.plot(keys[-1][:,0], -keys[-1][:,1], 'k+')
            plt.show()

        if len(keys) > 1:
            for i, p in enumerate(positions):
                if not triangulated[i]:
                    mdist = calc_dist_haver(gps['dRMCLatitude'], gps['dRMCLongitude'],
                                            p[0], p[1])
                    if mdist > MIN_DIST:
                        #Calculate 3D points
                        mm = flann_matcher( desc[i], desc[-1], threshold=0.4 )
                        print mm

                        plt.plot(keys[i][:,0], -keys[i][:,1], 'r+')
                        plt.plot(keys[-1][:,0], -keys[-1][:,1], 'b+')
                        for ii in range(len(mm[0])-1):
                            plt.plot( (keys[i][mm[0][ii],0],keys[-1][mm[1][ii],0]),
                                      (-keys[i][mm[0][ii],1],-keys[-1][mm[1][ii],1]),
                                      'k')
                        print i, 'and', len(keys)-1
                        plt.show()


        triangulated.append( False )
        positions.append( (gps['dRMCLatitude'], gps['dRMCLongitude'], gps['dGGAAltitude']) )
        if True:
            print triangulated
            print positions

    del ladybug





if __name__ == '__main__':
    main()



#===============================================================================
# QUICK REFERENCE
#===============================================================================
'''Templates and markup notes

>>SPYDER Note markers
    #XXX: !
    #TODO: ?
    #FIXME: ?
    #HINT: !
    #TIP: !


>>SPHINX markup
    :Any words between colons: Description following.
        Indent any continuation and it will be concatenated.
    .. warning:: ...
    .. note:: ...
    .. todo:: ...

    - List items with - or +
    - List item 2

    For a long hyphen use ---

    Start colored formatted code with >>> and ...

    **bold** and *italic* inline emphasis


>>SPHINX Method simple doc template (DIY formatting):
    """ summary

    description

    - **param** --- desc
    - *return* --- desc
    """

>>SPHINX Method longer template (with Sphinx keywords):
    """ summary

    description

    :type name: type optional
    :arg name: desc
    :returns: desc

    (optional intro to block)::

        Skip line and indent monospace block

    >>> python colored code example
    ... more code
    """

See http://scienceoss.com/use-sphinx-for-documentation/ for more details on
running Sphinx
'''
