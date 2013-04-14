#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SLAM implemented with NumPy

Bundle Adjustment of subject positions and landmark positions. Based on online SLAM
introduced in Udacity's self-driving robot course. The number of dimensions handled
is chosen by the initial point passed to the constructor.

:REQUIRES: NumPy
:TODO: 

:AUTHOR: Ripley6811
:ORGANIZATION: National Cheng Kung University, Department of Earth Sciences
:CONTACT: python@boun.cr
:SINCE: Thu Mar 14 19:25:12 2013
:VERSION: 1.0
:STATUS: Working
"""
#===============================================================================
# PROGRAM METADATA
#===============================================================================
__author__ = 'Ripley6811'
__contact__ = 'python@boun.cr'
__copyright__ = ''
__license__ = ''
__date__ = 'Thu Mar 14 19:25:12 2013'
__version__ = '1.0'


#===============================================================================
# IMPORT STATEMENTS
#===============================================================================
import numpy as np  # IMPORTS ndarray(), arange(), zeros(), ones()
#set_printoptions(precision=5)
np.set_printoptions(suppress=True)


#===============================================================================
# METHODS
#===============================================================================


class SLAM:
    '''SLAM matrix management.

    :Methods:
        *add_measurement* for distance estimation to point(s).
        *add_motion* for new estimated motion from previous position.
        *get_positions* for the SLAM results of all tracked positions.
        *get_landmarks* for the SLAM results of all landmarks.
        *get_pt_hist* for all archived positions.
        *remove_pos* to remove oldest positions from matrix.

    Measurements is a list of two to four value array.
    First value is a ID number for the measured point.
    Second to fourth values are the coordinates x,y,z depending on the
    number of dimensions.
    Position is a one to three value array corresponding to x,y,z.
    '''
    def __init__(self, pos=np.zeros(3, float),
                 motion_confidence=1.0, measurement_confidence=1.0):
        '''Initialize SLAM matrices.

        Initialize with a starting position of any dimension. Defaults to
        3-dimensions with starting point of zeros.
        
        :type pos: iterable type with floats
        :arg  pos: Initial starting position. Sets dimensionality.
        :type motion_confidence: Float
        :arg  motion_confidence: Default motion reliability, smaller
            means more reliable
        :type measurement_confidence: Float
        :arg  measurement_confidence: Default measurement reliability, 
            smaller means more reliable
        '''
        self.nPts = 0 # number of correspondings points / landmarks
        self.dim = len(pos)  # number of dimensions to use (x,y,z)
        self.landmarkID = [] # Map ID name to landmark index in matrix
        self.motion_confidence = motion_confidence
        self.measurement_confidence = measurement_confidence
        self.pts_history = [] # Store positions removed from matrix

        mat_len = 1 + self.nPts

        self.Omega = []  # List of matrices, one for each dimension
        self.Xi = []
        for i, xyz in enumerate(pos):
        # make the constraint information matrix and vector
            self.Omega.append( np.asmatrix(np.zeros( (mat_len, mat_len), float ) ) )
            self.Omega[i][0,0] = 1.0

            self.Xi.append( np.asmatrix(np.zeros( (mat_len, 1), float ) ) )
            self.Xi[i][0,0] = xyz

        self.nPos = 1  # number of positions entered into matrix

        

    def add_measurement(self, pts, measurement_confidence=None):
        '''Adds measurement data to most recent motion.

        Increases the size of the array if new point ID's are found.
        New landmarks are added to end of row and column.
        ID numbers must start from zero and be managed outside of this class.
        :TODO: Manage IDs within class by mapping, this will avoid problems.
        
        :type pts: List of lists or other iterable type
        :arg  pts: List of measurements. Each like [ID, x[, y[, z]]].
        :type measurement_confidence: float
        :arg  measurement_confidence: Optional confidence score for input.
        '''
        self.updated = False
        P = self.nPos - 1
        LIDs = self.landmarkID
        
        
        if not isinstance(measurement_confidence, float):
            measurement_confidence = self.measurement_confidence

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
                    O2 = np.mat(np.zeros(np.array(O.shape)+1))
                    O2[:-1,:-1] = O[:,:]

                    X2 = np.mat(np.zeros((X.shape[0]+1, 1)))
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

                O[P,P] += 1.0 / measurement_confidence
                O[iL,iL] += 1.0 / measurement_confidence
                O[P,iL] -= 1.0 / measurement_confidence
                O[iL,P] -= 1.0 / measurement_confidence
                X[P,0] -= dist[xyz] / measurement_confidence
                X[iL,0] += dist[xyz] / measurement_confidence



    def add_motion(self, motion, motion_confidence=None):
        '''Add a motion since last position.

        Increases the size of matrix by one. New row and column inserted
        between positional and landmark sections.
        
        :type motion: Iterable type containing floating point numbers
        :arg  motion: Movement in one or more dimensions.
        :type motion_confidence: float
        :arg  motion_confidence: Optional confidence score for input.
        '''
        assert len(motion) == self.dim
        self.updated = False
        
        if not isinstance(motion_confidence, float):
            motion_confidence = self.motion_confidence

        N = self.nPos

        for xyz in range(self.dim):
            # Create shortcut to desired dimension arrays
            O = self.Omega[xyz]
            X = self.Xi[xyz]

            # Create expanded matrices and copy data
            # Insert new col and row between position and landmark sections
            O2 = np.mat(np.zeros(np.array(O.shape)+1))
            O2[:N,:N] = O[:N,:N]
            O2[:N,N+1:] = O[:N,N:]
            O2[N+1:,:N] = O[N:,:N]
            O2[N+1:,N+1:] = O[N:,N:]

            X2 = np.mat(np.zeros((X.shape[0]+1, 1)))
            X2[:N,0] = X[:N,0]
            X2[N+1:,0] = X[N:,0]

            # Insert new motion data
            O2[N-1,N-1] += 1. / motion_confidence
            O2[N  ,N  ] += 1. / motion_confidence
            O2[N-1,N  ] -= 1. / motion_confidence
            O2[N  ,N-1] -= 1. / motion_confidence
            X2[N-1,0  ] -= motion[xyz] / motion_confidence
            X2[N  ,0  ] += motion[xyz] / motion_confidence

            # Copy new matrices over global arrays
            self.Omega[xyz]= O2
            self.Xi[xyz] = X2

        self.nPos += 1



    def calculate(self):
        '''Solves the matrix to find optimal pts.
        
        Solves the equation: Omega.I * Xi = Mu
        Maintains a list of updated positions and landmarks.
        '''
        mu = []
        for O,X in zip(self.Omega, self.Xi):
            mu.append( O.I * X )

        stacked = np.hstack(mu)
        self.updated_positions = stacked[:self.nPos].copy()
        self.updated_landmarks = stacked[self.nPos:].copy()

        self.updated = True

        

    def get_positions(self):
        '''Returns the updated positions for those in the matrix.

        :rtype: NumPy array [points, dimensions]
        '''
        if not self.updated:
            self.calculate()

        return np.array(self.updated_positions)

        

    def get_landmarks(self):
        '''Returns the updated landmarks for those in the matrix.

        :rtype: NumPy array [points, dimensions]
        '''
        if not self.updated:
            self.calculate()

        return np.array(self.updated_landmarks)
        
        
        
    def get_pt_hist(self):
        '''Returns the list of archived points as a NumPy array.
        
        The archived points are stored in a list within the class.
        This method simply converts to an np.array.
        
        :rtype: NumPy array [points, dimensions]
        '''
        return np.array(self.pts_history) 


        
    def remove_pos(self, number_to_remove=1):
        '''Removes oldest positions.

        Points are removed from the matrix and added to a list. They
        are not updated after removal.
        
        :type number_to_remove: int
        :arg  number_to_remove: Number of (oldest) points to remove/archive.
        '''
        # Most recent motion cannot be removed
        if number_to_remove >= self.nPos:
            return False
            
        if not self.updated:
            self.calculate()
            
        pts = self.updated_positions[:number_to_remove]

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

        for each in np.array(pts):
            self.pts_history.append( each )
        self.updated = False
        self.nPos -= number_to_remove
