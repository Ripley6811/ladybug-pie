#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
(SUMMARY)

(DESCRIPTION)

@SINCE: Tue May 08 09:50:30 2012
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
__date__ = 'Tue May 08 09:50:30 2012'
__version__ = '0.1'

#===============================================================================
# IMPORT STATEMENTS
#===============================================================================
import cv2.cv as cv
from collections import namedtuple

#===============================================================================
# METHODS
#===============================================================================

cv.Size = namedtuple('CvSize', 'width height')
cv.TermCriteria = namedtuple('CvTermCriteria', 'type max_iter epsilon')
cv.Point = namedtuple('CvPoint', 'x y')
cv.Point2D32f = namedtuple('CvPoint2D32f', 'x y')
stderr = 'ERROR'





#===============================================================================
# MAIN METHOD AND TESTING AREA
#===============================================================================
class ShiTomasiTracking:
    def __init__(self, height, width):
        self.frame_size = cv.Size( height=int( height ),
                                   width=int( width )      )
        self.eig_image = cv.CreateImage( self.frame_size, cv.IPL_DEPTH_32F, 1 )
        self.temp_image = cv.CreateImage( self.frame_size, cv.IPL_DEPTH_32F, 1 )

    def getVectors(self, img1, img2, number_of_features = 800):
#        print type(img1), img1.size, img1.__dict__
        img1 = img1.convert('L')
        img2 = img2.convert('L')
        cv_img1 = cv.CreateImageHeader(img1.size, cv.IPL_DEPTH_8U, 1)
        cv.SetData(cv_img1, img1.tostring(), self.frame_size.width)
        cv_img2 = cv.CreateImageHeader(img2.size, cv.IPL_DEPTH_8U, 1)
        cv.SetData(cv_img2, img2.tostring(), self.frame_size.width)
        
#        print type(cv_img1)
#        cv.NamedWindow("Optical Flow", cv.CV_WINDOW_AUTOSIZE)
#        cv.ShowImage("Optical Flow", cv_img1)
        
        img1_features = [cv.Point2D32f(x, y) 
                     for x,y in cv.GoodFeaturesToTrack(cv_img1, self.eig_image, 
                                                       self.temp_image, 
                                                       number_of_features, 
                                                       .01, .01, useHarris = True)]

        optical_flow_window = cv.Size(3,3)
        optical_flow_termination_criteria = cv.TermCriteria( 
                            cv.CV_TERMCRIT_ITER | cv.CV_TERMCRIT_EPS, 20, .3 )
        pyramid1 = cv.CreateImage( self.frame_size, cv.IPL_DEPTH_8U, 1 )
        pyramid2 = cv.CreateImage( self.frame_size, cv.IPL_DEPTH_8U, 1 )

        ret_tuple = cv.CalcOpticalFlowPyrLK(cv_img1, cv_img2, 
                         pyramid1, pyramid2, img1_features, #number_of_features, 
                         optical_flow_window, 5,
                         optical_flow_termination_criteria, 0 )
        img2_features, optical_flow_found_feature, optical_flow_feature_error = ret_tuple
        img2_features = [cv.Point2D32f(x, y) for x,y in img2_features]
#        for each in zip(optical_flow_found_feature,optical_flow_feature_error):
#            print each
        
        matches = []
        for i, feature in enumerate( optical_flow_found_feature ):
            if feature == 0 or optical_flow_feature_error[i] >= 100:
                continue
            
            matches.append( (img1_features[i].x, img1_features[i].y,
                             img2_features[i].x, img2_features[i].y) )
                             
#        findstereocorrespondence(cv_img1, cv_img2 )
        return matches

def findstereocorrespondence(image_left, image_right):
    # image_left and image_right are the input 8-bit single-channel images
    # from the left and the right cameras, respectively
    (r, c) = (image_left.height, image_left.width)
    disparity_left = cv.CreateMat(r, c, cv.CV_16S)
    disparity_right = cv.CreateMat(r, c, cv.CV_16S)
    state = cv.CreateStereoGCState(16, 2)
    cv.FindStereoCorrespondenceGC(image_left, image_right, disparity_left, disparity_right, state, 0)
#    return (disparity_left, disparity_right)
    
    disparity_left_visual = cv.CreateMat(r, c, cv.CV_8U)
    cv.ConvertScale(disparity_left, disparity_left_visual, -16)
    cv.SaveImage("C:/disparity.bmp", disparity_left_visual)
    
    