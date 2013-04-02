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
:SINCE: Mon Apr 01 11:47:53 2013
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
__date__ = 'Mon Apr 01 11:47:53 2013'
__version__ = '0.1'

#__package__  = 'SFM'

#export PYTHONPATH=..
import sys
sys.path.append("..") # Access modules that are one level up

from online_SLAM import SLAM




def test_data1():

    measurements =   [[[0, 12.637647070797396, 17.45189715769647], [1, 10.432982633935133, -25.49437383412288]],
                      [[0, -4.104607680013634, 11.41471295488775], [1, -2.6421937245699176, -30.500310738397154]],
                      [[0, -27.157759429499166, -1.9907376178358271], [1, -23.19841267128686, -43.2248146183254]],
                      [[0, -200.7880265859173763, -16.41914969572965], [1, -3.6771540967943794, -54.29943770172535]],
                      [[0, 10.844236516370763, -27.19190207903398], [1, 14.728670653019343, -63.53743222490458]]]

    motions =        [[17.232472057089492, 10.150955955063045],
                      [17.232472057089492, 10.150955955063045],
                      [-17.10510363812527, 10.364141523975523],
                      [-17.10510363812527, 10.364141523975523],
                      [14.192077112147086, -14.09201714598981]]

    return motions, measurements



def test_data2():
        # Actual motion from starting point of (0,0,0)
    motions = [[1.,-1.,0.],
               [1.,1.,1.],
               [1.,1.,-1.],
               [1.,-1.,-.5],
               [1.,-.5,0.6]]

    # Actual landmark positions relative to starting point
    landmarks = [[0.,8.,0.2],
                 [6.,10.2,-0.1]]

    # Real distances as measurements
    curr_position = [0.,0.,0.]
    measurements = []
    for each in motions:
        landmark_distances = []
        for l, landmark in enumerate(landmarks):
            landmark_distances.append([l,
                                       landmark[0]-curr_position[0],
                                       landmark[1]-curr_position[1],
                                       landmark[2]-curr_position[2]])
        measurements.append(landmark_distances)
        curr_position = [curr_position[0] + each[0],
                         curr_position[1] + each[1],
                         curr_position[2] + each[2]]

    # Delete a few measurements
    del measurements[0][1]
    del measurements[1][0]
    del measurements[2][1]
    del measurements[3][0]
    del measurements[4][0]
    # Add error to a few measurements
    measurements[3][0][2] += 0.001
    measurements[2][0][3] += 0.001


    return motions, measurements

#===============================================================================
# MAIN METHOD AND TESTING AREA
#===============================================================================
def main():
    """Description of main()"""
    motions, measurements = test_data1()

    slam = SLAM((50.,50.), 3.0, 5.0)
    slam.add_measurement(measurements[0])
    slam.add_motion(motions[0])
    slam.add_measurement(measurements[1])
    slam.add_motion(motions[1])
    slam.add_measurement(measurements[2])
    slam.add_motion(motions[2])
    print slam.Omega
    print slam.Xi
    slam.add_measurement(measurements[3])
    slam.add_motion(motions[3])
    slam.add_measurement(measurements[4])
    slam.add_motion(motions[4])
    print slam.Omega
    print slam.Xi
    print slam.get_positions()


    motions, measurements = test_data2()
    slam = SLAM()
    slam.add_measurement(measurements[0])
    slam.add_motion(motions[0])
    slam.add_measurement(measurements[1])
    slam.add_motion(motions[1])
    slam.add_measurement(measurements[2])
    slam.add_motion(motions[2])
    slam.add_measurement(measurements[3])
    slam.add_motion(motions[3])
    slam.add_measurement(measurements[4])
    slam.add_motion(motions[4])
    print slam.Omega[0]
    print slam.Xi[0]
    print slam.get_positions()


if __name__ == '__main__':
    main()