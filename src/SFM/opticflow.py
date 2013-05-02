#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Class for feature detector and matching using OpenCV.


:REQUIRES: OpenCV 2.4, matplotlib

:AUTHOR: Ripley6811
:ORGANIZATION: National Cheng Kung University, Department of Earth Sciences
:SINCE: Thu Sep 13 23:01:23 2012
:VERSION: 0.1

:TODO:
    - Need a way to retrieve triplet correspondences but store pairs for future
    triplet matching

"""
#===============================================================================
# PROGRAM METADATA
#===============================================================================
__author__ = 'Ripley6811'
__copyright__ = ''
__license__ = ''
__date__ = 'Thu Sep 13 23:01:23 2012'
__version__ = '0.1'


from numpy import array, arange, int32, append, cross, zeros, where, pi, sqrt, r_, mean, std, min, max, sum
import matplotlib.pyplot as plt  # plt.plot(x,y)  plt.show()
import cv2


detector_formats = ["","Grid","Pyramid"]
detector_types = ["FAST","STAR","SIFT","SURF","ORB","MSER","GFTT","HARRIS"]
extractor_formats = ["","Opponent"]
extractor_types = ["SIFT","SURF","ORB","BRIEF"]


class FeatureMatcher:
    '''Implements OpenCV's FeatureDetector_create, Descriptor_create, and
    flann_index methods.

    Available detector and extractor formats are:
    detector_formats = ["","Grid","Pyramid"]
    detector_types = ["FAST","STAR","SIFT","SURF","ORB","MSER","GFTT","HARRIS"]
    extractor_formats = ["","Opponent"]
    extractor_types = ["SIFT","SURF","ORB","BRIEF"]

    '''
    def __init__(self,
                 detector_format='Pyramid', detector_type='FAST',
                 extractor_format='', extractor_type='SIFT',
                 roi=None):
        '''Initialize a cv2 FeatureDetector and DescriptorExtractor.

        Defaults are "PyramidFAST" for feature detecting and "SIFT" for descriptor
        extraction. FLANN is used for matching.
        '''
        detector = detector_format + detector_type
        extractor = extractor_format + extractor_type
        self.featdet = cv2.FeatureDetector_create(detector)
        self.desext = cv2.DescriptorExtractor_create(extractor)
        self.crop = roi

        self.keys = []
        self.descriptors = []
        self.matches = []



    def __call__(self, image1, image2, threshold=0.5):
        '''Returns the corresponding key points and matching indices.

        This is an independent function for finding correspondences across
        two images. For continuous tracking over multiple images use add(image).

        :PARAMETERS:
            *image1* --- Image ndarray (RGB)
            *image2* --- Image ndarray (RGB)
            **threshold** --- Threshold value for descriptor matching

        :RETURNS:
            - Key points for image 1. N by 2 array.
            - key points for image 2. N by 2 array.
            - Matching indices between images. Column 0 indices are image 1 key points.

        :TODO:
            - The image arrays must be in cv2.imread format.

        '''
        keypts1, desc1 = self.getkeys(image1)
        keypts2, desc2 = self.getkeys(image2)

        # Match descriptors between images
        matches = flann_matcher(desc1, desc2, threshold=threshold)

        return keypts1, keypts2, matches



    def add(self, image, triplet=True, threshold=0.5):
        '''Add one RGB or grayscale image at a time to the class.

        Each image: detect keypoints and descriptors.
        When adding 2nd image and beyond, finds pair correspondences.
        When adding 3rd image and beyond, finds triplet correspondences.
        If keyword 'triplet' is False, then returns pair correspondences when
        available, otherwise returns triplet correspondences when available.

        :PARAMETERS:
            *image* --- ndarray, single band
            **triplet** --- boolean, retrieve triplets (True) or pairs (False)
            **threshold** --- float, Matching threshold (Uniqueness)

        :RETURNS:
            **tuple**
                0. N by 2 point array
                1. Correspondence array (2xN or 3xN) or None

        :TODO:
            - Change to add a parameter where the user sets how many images to match.

        '''
        keys, desc = self.getkeys(image)
        self.descriptors.append( desc )
        self.keys.append( keys )

        if len(self.keys) >= 2:
            # Run matching algorithm on last two images
            self.matches.append( flann_matcher(self.descriptors[-2],
                                               self.descriptors[-1],
                                               threshold=threshold) )
            # If triplet correspondences are not wanted, return pair match
            if triplet == False:
                return self.keys[-1], self.matches[-1]
            # Return triplet correspondences if at least 3 keys
            elif len(self.matches) >= 2:
                self.matches[-2] = extend_matchset( self.matches[-2], self.matches[-1] )
                return self.keys[-1], self.matches[-2]
        # Return the keys only if only one or two images added
        return self.keys[-1], None



    def getkeys(self, image):
        '''Returns a key points and corresponding descriptors from an image
        file or ndarray.

        :PARAMETERS:
            *image* --- Image filename or an image ndarray

        :RETURNS:
            - Key points for image. N by 2 array.
            - Descriptors for key points. N-length list.
        '''
        if isinstance(image, str):
            image = cv2.imread(image, 0)
        if len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

        # Detect features in each image
        keys = self.featdet.detect(image)
        # Convert KeyPoint list to an N by 2 array of points
        # KeyPoint class: angle, class_id, octave, pt, response, size
        keyarr = array([key.pt for key in keys])
        # ANGLED WINDOW CROPPING
        if self.crop != None:
            L1 = cross(r_[self.crop[0],1],r_[self.crop[3],1]).astype(float)
            ymin = (-L1[0]/L1[1])*keyarr[:,0] - L1[2]/L1[1]
            L2 = cross(r_[self.crop[1],1],r_[self.crop[2],1]).astype(float)
            ymax = (-L2[0]/L2[1])*keyarr[:,0] - L2[2]/L2[1]
            incrop = ((keyarr[:,1] > ymin) & (keyarr[:,1] < ymax)
                     & (keyarr[:,0] > min(self.crop[:,0]))
                     & (keyarr[:,0] < max(self.crop[:,0])) )
            leankeys = [key for key, inout in zip(keys, incrop) if inout]
            keyarr = keyarr[incrop]
            assert len(leankeys) == len(keyarr), 'leankeys != keyarr'
            # Create descriptors for all found features
            desc = self.desext.compute(image, leankeys)[1]
        else:
            # Create descriptors for all found features
            desc = self.desext.compute(image, keys)[1]

        return keyarr, desc



    def imread(self, fname, flags=0):
        '''Uses cv2 to load an image and convert to grayscale (flags=0).'''
        return cv2.imread(fname, flags)



def extend_matchset(match1, match2):
    '''Returns a 3 by N ndarray of correspondences over three images.

    :PARAMETERS:
        *match1* --- Matches of images 1 and 2
        *match2* --- Matches of images 2 and 3

    :RETURNS:
        3 by N ndarray, where N is the number of matches over three images.

    '''
    # ADD A NEW ROW TO MATCH1 TO FILL
    len2 = len(match2)
    M = append(array(match1, int), zeros((len2-1,len(match1[0])),int)-1, 0)

    B1 = M[-len2]
    B2 = match2[0]
    for b1 in B1:
        if b1 in B2:
            M[-len2+1:,where(B1 == b1)] = match2[1:,where(B2 == b1)]

    return M[:,M[-1] != -1].copy()



def flann_matcher(desc1, desc2, threshold=0.6, trees=4):
    """Returns a 2 by N ndarray of matching indices.

    Column 0 are indices of first set and col 1 are corresponding indices in
    second set. Uses the KDTree algorithm in cv2.flann_index.

    :PARAMETERS:
        *desc1* --- List of descriptors for first set
        *desc2* --- List of descriptors for second set
        **threshold** --- Lower value returns fewer but better matches
        **trees** --- The number of parallel kd-trees to use. Try [1 to 16].

    :RETURNS:
        2 by N ndarray, where N is the number of matches.

    """
    flann = cv2.flann_Index(desc2, dict(algorithm=1, trees=trees))
    idx2, dist = flann.knnSearch(desc1, 2, params={})
    mask = dist[:,0] / dist[:,1] < threshold
    idx1 = arange(len(desc1))
    pairs = int32( zip(idx1, idx2[:,0]) )
    return pairs[mask].astype(int).T



def point_array(keypts1, keypts2, matches):
    '''Process the matching key points into a single array.

    Each row are the matching points [x1,y1,x2,y2].

    '''
    points = []
    for m in matches.T:
        x1,y1 = keypts1[m[0]].pt
        x2,y2 = keypts2[m[1]].pt
        points.append([x1,y1,x2,y2])
    return array(points)



def plot_flow(keypts1, keypts2, matches):
    '''Accessory method to plot point correspondences using matplotlib.pyplot.'''
    # Plot results
    plt.figure()
    for m in matches.T:
        x1,y1 = keypts1[m[0]].pt
        x2,y2 = keypts2[m[1]].pt
        plt.plot([x1,x2],[-y1,-y2],'k')
    plt.axis('equal')
    plt.show()



def test_vector_flow(a, b, c, max_angle=pi/32):
    '''Tests a contiguous set of matches. The difference in angle between a-b
    and b-c must be less than 'max_angle'. Default is difference of 5 degrees.
    '''
    try:
        ab = array([b['x'] - a['x'], b['y'] - a['y']])
        bc = array([c['x'] - b['x'], c['y'] - b['y']])
    except ValueError:
        ab = b-a
        bc = c-b

    vec = array([cv2.cartToPolar(r_[ab[0]], r_[ab[1]])[1].flatten(),
                 cv2.cartToPolar(r_[bc[0]], r_[bc[1]])[1].flatten()])
    mins = min(vec,0)
    vec -= mins
    vec = max(vec,0)
    vec[vec>pi] = 2*pi - vec[vec>pi]

    gdvecs = vec < max_angle
    divisor = sqrt(sum(ab[:2]**2,0))
    nonzero = divisor != 0.
    scalings = sqrt(sum(bc[:2]**2,0))/divisor
#    print 'scales', scalings
    meanscale = mean(sqrt(sum(bc[:2,nonzero]**2,0))/sqrt(sum(ab[:2,nonzero]**2,0)))
#    print 'scale mean', meanscale
    stdscale = std(sqrt(sum(bc[:2,nonzero]**2,0))/sqrt(sum(ab[:2,nonzero]**2,0)))
#    print 'scale std', stdscale
    gdscale = (scalings >= (meanscale-stdscale)) & (scalings <= (meanscale+stdscale))

    return gdvecs & gdscale


