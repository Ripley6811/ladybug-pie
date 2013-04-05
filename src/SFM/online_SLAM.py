#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
(SUMMARY)

(DESCRIPTION)

:REQUIRES: ...
:PRECONDITION: ...
:POSTCONDITION: ...

:AUTHOR: Ripley6811
:ORGANIZATION: National Cheng Kung University, Department of Earth Sciences
:CONTACT: python@boun.cr
:SINCE: Thu Mar 14 19:25:12 2013
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
__date__ = 'Thu Mar 14 19:25:12 2013'
__version__ = '0.1'

#__package__ = 'SFM'

#===============================================================================
# IMPORT STATEMENTS
#===============================================================================
from numpy import *  # IMPORTS ndarray(), arange(), zeros(), ones()
#set_printoptions(precision=5)
set_printoptions(suppress=True)
#from visual import *  # IMPORTS NumPy.*, SciPy.*, and Visual objects (sphere, box, etc.)
#import matplotlib.pyplot as plt  # plt.plot(x,y)  plt.show()
#from pylab import *  # IMPORTS NumPy.*, SciPy.*, and matplotlib.*
#import os  # os.walk(basedir) FOR GETTING DIR STRUCTURE
#import pickle  # pickle.load(fromfile)  pickle.dump(data, tofile)
#from tkFileDialog import askopenfilename, askopenfile
#from collections import namedtuple
#from ctypes import *
#import glob
#import random
#import cv2

#===============================================================================
# METHODS
#===============================================================================


class SLAM:
    '''SLAM matrix management.

    Methods:
        add_measurement for distance estimation to point(s).
        add_motion for new estimated motion from previous position.
        get_positions for the SLAM results of all available positions and pts.

    Measurements is a list of two to four value array.
    First value is a ID number for the measured point.
    Second to fourth values are the coordinates x,y,z depending on the
    number of dimensions.
    Position is a one to three value array corresponding to x,y,z.
    '''
    def __init__(self, pos=zeros(3, float),
                 motion_confidence=1.0, measurement_confidence=1.0):
        '''Initialize SLAM matrices.

        Initialize with a starting position of any dimension. Defaults to
        3-dimensions with starting point of zeros.
        '''
        self.nPts = 0 # number of correspondings points / landmarks
        self.dim = len(pos)  # number of dimensions to use (x,y,z)
        self.landmarkID = [] # number of landmarks entered into matrix
        self.motion_confidence = motion_confidence
        self.measurement_confidence = measurement_confidence

        mat_len = 1 + self.nPts

        self.Omega = []  # List of matrices, one for each dimension
        self.Xi = []
        for i, xyz in enumerate(pos):
        # make the constraint information matrix and vector
            self.Omega.append( asmatrix(zeros( (mat_len, mat_len), float ) ) )
            self.Omega[i][0,0] = 1.0

            self.Xi.append( asmatrix(zeros( (mat_len, 1), float ) ) )
            self.Xi[i][0,0] = xyz

        self.nPos = 1  # number of positions entered into matrix


    def add_measurement(self, pts):
        '''Adds measurement data to most recent motion.

        Format: List of tuples/lists: [[ID, x, y, z], [ID, x, y, z],...].
        Can be 1 or more dimensions.
        Increases the size of the array for new point ID's.
        New landmarks are added to end of row and column.
        '''
        P = self.nPos - 1
        LIDs = self.landmarkID

        for pt in pts:
            LID = pt[0]
            dist = pt[1:]

            # Check if landmark ID already exists
            if LID not in LIDs:
                self.landmarkID.append(LID)
                LIDs = self.landmarkID # Not necessary but just to be sure

                # Expand matrix for new landmark row and column
                for xyz in range(self.dim):
                    # Create shortcut to desired dimension arrays
                    O = self.Omega[xyz]
                    X = self.Xi[xyz]
                    O2 = mat(zeros(array(O.shape)+1))
                    O2[:-1,:-1] = O[:,:]

                    X2 = mat(zeros((X.shape[0]+1, 1)))
                    X2[:-1,0] = X[:,0]

                    # Copy new matrices over global arrays
                    self.Omega[xyz]= O2
                    self.Xi[xyz] = X2

            # Get index position of landmark in array
            iL = P + LIDs.index(LID) +1
            # Add landmark data to each dimensional array
            for xyz in range(self.dim):
                print 'Adding landmark', LID, 'to position', P, iL
                # Create shortcut to desired dimension arrays
                O = self.Omega[xyz]
                X = self.Xi[xyz]

                O[P,P] += 1.0 / self.measurement_confidence
                O[iL,iL] += 1.0 / self.measurement_confidence
                O[P,iL] -= 1.0 / self.measurement_confidence
                O[iL,P] -= 1.0 / self.measurement_confidence
                X[P,0] -= dist[xyz] / self.measurement_confidence
                X[iL,0] += dist[xyz] / self.measurement_confidence





    def add_motion(self, motion):
        '''Adds motion from last position.

        Motion format: Single tuple/list: [x, y, z].
        Can be 1 or more dimensions.
        Increases the size of each array by one. New row and column inserted
        between positional and landmark sections.
        '''
        assert len(motion) == self.dim

        N = self.nPos

        for xyz in range(self.dim):
            # Create shortcut to desired dimension arrays
            O = self.Omega[xyz]
            X = self.Xi[xyz]

            # Create expanded matrices and copy data
            # Insert new col and row between position and landmark sections
            O2 = mat(zeros(array(O.shape)+1))
            O2[:N,:N] = O[:N,:N]
            O2[:N,N+1:] = O[:N,N:]
            O2[N+1:,:N] = O[N:,:N]
            O2[N+1:,N+1:] = O[N:,N:]

            X2 = mat(zeros((X.shape[0]+1, 1)))
            X2[:N,0] = X[:N,0]
            X2[N+1:,0] = X[N:,0]

            # Insert new motion data
            O2[N-1,N-1] += 1. / self.motion_confidence
            O2[N  ,N  ] += 1. / self.motion_confidence
            O2[N-1,N  ] -= 1. / self.motion_confidence
            O2[N  ,N-1] -= 1. / self.motion_confidence
            X2[N-1,0  ] -= motion[xyz] / self.motion_confidence
            X2[N  ,0  ] += motion[xyz] / self.motion_confidence

            # Copy new matrices over global arrays
            self.Omega[xyz]= O2
            self.Xi[xyz] = X2

        self.nPos += 1







    def get_positions(self):
        '''Returns the updated positions for available positions and points.

        '''
        mu = []
        for O,X in zip(self.Omega, self.Xi):
            mu.append( O.I * X )

        return hstack(mu)



    def remove_pos(self, number_to_remove=1):
        '''Removes oldest positions.

        '''
        # Most recent motion cannot be removed
        if number_to_remove >= self.nPos:
            return False

        for xyz in range(self.dim):
            n = number_to_remove
            O = self.Omega[xyz]
            X = self.Xi[xyz]

            A = O[:n,n:]
            B = O[:n,:n]
            O_ = O[n:,n:]
            C = X[:n,:]
            X_ = X[n:,:]

            print O.shape, X.shape
            print A.shape, B.shape, O_.shape, C.shape, X_.shape
            O = O_ - A.T * B.I * A
            X = X_ - A.T * B.I * C
            print O.shape, X.shape

            self.Omega[xyz] = O
            self.Xi[xyz] = X

        self.nPos -= number_to_remove


if __name__ == "__main__" and __package__ is None:
    __package__ = "online_SLAM"




