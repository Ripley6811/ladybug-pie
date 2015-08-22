#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
(SUMMARY)

(DESCRIPTION)

:REQUIRES: ...
:TODO:

:SINCE: Sat Aug 04 21:45:58 2012
:VERSION: 0.1
:STATUS: Nascent
:CHANGE: ...


:AUTHOR: Ripley6811
:ORGANIZATION: National Cheng Kung University, Department of Earth Sciences
:CONTACT: jwj@boun.cr
"""
#===============================================================================
# PROGRAM METADATA
#===============================================================================
__author__ = 'Ripley6811'
__contact__ = 'jwj@boun.cr'
__copyright__ = ''
__license__ = ''
__date__ = 'Sat Aug 04 21:45:58 2012'
__version__ = '0.1'

#===============================================================================
# IMPORT STATEMENTS
#===============================================================================
import visual as vis
from numpy import *  # IMPORTS ndarray(), arange(), zeros(), ones()
set_printoptions(precision=5)
set_printoptions(suppress=True)
import cv2

import matplotlib.pyplot as plt
from SFM import FeatureMatcher, Trifocal, test_vector_flow, GAP, SLAM

#===============================================================================
# METHODS
#===============================================================================
class Ladybug_SfM:
    def __init__(self, cam_intrinsic_mat=None, ladybug_cam_proj=None,
                 forward_cam=None, rectify_method=None):
        '''
        
        :type forward_cam: int
        :arg  forward_cam: Index number of the forward facing camera.
        :type rectify_method: function
        :arg  rectify_method: Method from Ladybug API to rectify a pixel location.
        '''
        self.LPA = LadybugProjectionAssistant( cam_intrinsic_mat, ladybug_cam_proj)
        # SAVE NUMBER OF FORWARD FACING CAMERA
        self.forward_cam = forward_cam
        # STORE THE SEQUENCE ID FOR THE FRAME: USED FOR ESTIMATING SKIPPED FRAME MOTION
        self.seqid = []
        # STORE KEYS AS A LIST OF LISTS: Nx5, WHERE N IS FRAME WITH 5 CAMERA VIEWS
        self.keylist = []
        # STORE MATCHES AS A LIST OF LISTS: Nx5, WHERE N IS FRAME WITH 5 CAMERA VIEWS
        self.matches = []
        # STORAGE LIST FOR CALCULATED TRANSFORMATIONS OF THE LADYBUG CAMERA
        self.Transformation = []
        self.H_lists = []
        # LOADED FRAME TOTAL
        self.nframes = 0
        # POINT RECTIFY METHOD FROM LADYBUG
        self.rectify = rectify_method

        self.fm = [FeatureMatcher() for i in range(5)]

        self.match_B = None
        self.prev_scale = 1.



    def __call__(self, seqid, keylist, matches=None):
        '''Add new key and match data from a new frame.
        
        After three frames are added, this method begins returning
        transformation data.
        
        :type seqid: int
        :arg  seqid: Sequence ID for one video frame.
        :type keylist: list
        :arg  keylist: List of five SIFT keys.
        :type matches: list
        :arg  matches: Previous set of relavent matches.
        :returns: A tuple of latest two transformation matrices.
        '''
        print 'Adding cam keys for seqid', seqid
        self.seqid.append( seqid )
#        keylist = []
#        matches = []
        self.keylist.append( keylist )
        self.matches.append( matches )
        self.nframes += 1
        self.H_lists.append( [] ) # list of transformations
        self.Transformation.append( eye(4)[:3] ) # selected transformation placeholder

        if self.nframes >= 3:
            return self.process_keys()



    def process_keys(self, calcfr=-1):
        '''Calculate the two translations between three contiguous frames.
        
        :Steps:
            #. Finds triple correspondences (3 frames) and normalizes points.
            #. Estimates relative scaling based on sequence number (may have skipped).
            #. Create trifocal tensor and extract the two translations.
            #. 
        
        :type calcfr: int
        :arg  calcfr: Index of 3rd inputed frame to calculate. 
            Must be 2 or greater.
        '''
        assert self.nframes >= 3, 'At least three frames are required for this process'

        if calcfr == -1:
            calcfr += self.nframes

        # FIND THE TWO-MATCH AND TRI-MATCH SETS
        keylist = self.keylist
        tri_match = self.matches[-1]


        # CREATE NORMALIZED TRI-SETS OF CORRESPONDENCE POINTS
        LPA = self.LPA
        for cam, camset in enumerate( tri_match ):
            pointset = []
            for i, m in enumerate( camset ):
                if len(m) > 1:
                    print cam, m
                    pointset.append( LPA.normalize(cam,
                                               self.keylist[calcfr-2+i][cam][:,0][m],
                                               self.keylist[calcfr-2+i][cam][:,1][m]) )
            tri_match[cam] = pointset
        print 'tri_match', type(tri_match), len(tri_match)

        # GET SCALING ESTIMATE FOR THIS TRANSLATION
        scale = ((self.seqid[calcfr]-self.seqid[calcfr-1])
                    /float(self.seqid[calcfr-1]-self.seqid[calcfr-2]))
        print 'scale', scale
        
        # CALCULATE TRANSFORMATIONS
        camcol = [(1,0,0),(0,1,0),(0,0,1),(1,1,0),(1,0,1)]
        for cam, tset in enumerate(tri_match):
            print 'cam tset', cam
            try:
                a, b, c = tset
            except:
                print 'Error in tset split'
                continue
            print 'cam tset', cam
            # TEST FOR REASONABLE FLOW
            mask = test_vector_flow(a,b,c)
            print 'len gd a', sum(mask), sum(mask)/float(len(a[0])), '%'
            if sum(mask) > 24:
                a, b, c = a[:,mask], b[:,mask], c[:,mask]
            print 'Used a', len(a[0])

            print 'H_ab twice', 'a shape', a.shape

            tensor = Trifocal(a, b, c)
            H_ab, H_ac = tensor.getProjectionMat()
            H_ab = LPA.H_C2L(cam, H_ab )

            # CALCULATE INITIAL TRANSFORMATION USING GA TO REFINE THE RESULT
#            H_ab = GAP.GA_refine_single_projection(LPA, cam, a, b, front_cam=self.forward_cam, popsize=40, iters=40)
            print H_ab
            # CALCULATE WORLD 3D POINTS FROM RESULT
            F = GAP.E(GAP.encode5(H_ab))
            epiHole = GAP.mask_pts_near_epipole(a, b, F=F)
            X = cv2.triangulatePoints(LPA.P(cam), LPA.Hdot(H_ab, cam)[:3], a[:2,epiHole], b[:2,epiHole])
            X /= X[3]
            print 'points', X
            LPA.show_ladybug()
            LPA.show_points(X, radius=0.1, color=camcol[cam])
            # CALCULATE 2ND TRANSFORMATION FROM WORLD POINTS
            H_ac = H_from_Xx(LPA, cam, X, c[:,epiHole].copy())

            H_ab_gene = GAP.encode5sb( H_ab )[:6]
            print 'Hab', H_ab_gene
            print 'Hac', GAP.encode5sb( H_ac )[:6]

            # MULTIPLY BY PREVIOUS SCALE
            H_ab_gene[5] *= self.prev_scale

            # CALCULATE THE B-C TRANSLATION
            H_bc_gene = GAP.encode5sb( dot(H_ac,linalg.inv(H_ab)) )[:6]
            print 'Hbc', H_bc_gene

            # TEST IF DETECTED SCALING IS WITHIN REASON AND ADD TO LIST
            print  H_bc_gene[5], scale, abs(H_bc_gene[5] - scale), (abs(H_bc_gene[5] - scale) < 0.25)
#            raw_input('pause 2')
            if (abs(H_bc_gene[5] - scale) < 0.25):
                self.H_lists[calcfr-1].append( H_ab_gene )
                self.H_lists[calcfr].append( H_bc_gene )
                print 'len prev', len(self.H_lists[calcfr-1])
                print 'len this', len(self.H_lists[calcfr])
            else:
                print 'Not adding:', H_ab_gene
                print 'Not adding:', H_bc_gene
        self.prev_scale = scale

        # EVALUATE THE PROJECTION COLLECTIONS, RE-EVALUATE PREVIOUS
        for each in [calcfr-1, calcfr]:
            Hlist = array(self.H_lists[each])
#            print Hlist
            print '  PROCESSING H LIST'
            print 'Number in stack', len(Hlist)
            me = mean(Hlist,0)
            st = std(Hlist,0)
            print repr(me)
            try:
                above = Hlist > (me - st)
                below = Hlist < (me + st)
                res = sum(above & below, 1) == 6
                self.Transformation[each] = mean(Hlist[res],0)
                if isnan(self.Transformation[each][0]):
                    raise ValueError, 'sodo'
            except:
                self.Transformation[each] = me
            print repr(self.Transformation[each])
            print

        return self.Transformation[calcfr-1], self.Transformation[calcfr]

        
    
    def process_keys_SLAM(self, calcfr=-1):
        '''Uses SLAM to improve vehicle position.
        
        :XXX: Can use GPS coordinates for motion estimate or estimated translation
            from corresponding points (or both?).
            
        :STEPS:
            #. Collect interframe correspondences.
                - Collect current frame points of interest.
                - Store descriptors in dictionary with 1-up ID's
                    - Cannot use list indices because it will need to allow point deletion.
                - Consecutive frames match old descriptors and add new descriptors.
            #. Estimate translation from corresponding points.
                - Rotation is not used in SLAM. Re-calculate R|t after SLAM adjustment (BA).
            #. Triangulate point distances from 1st frame and add distance estimates to SLAM.
            #. Add 1st frame to 2nd frame motion estimate to SLAM.
            #. Run bundle adjustment after # frames are added.
            #. Remove old adjusted positions and # frames are added.
            
        '''
        assert self.nframes > 1, 'Requires at least two frames to start triangulation.'

        
        

#    def process_keys_GA(self, calcfr=-1):
#        assert self.nframes >= 3, 'At least three frames are required for this process'
#
#        if calcfr == -1:
#            calcfr += self.nframes
#
#        # FIND THE TWO-MATCH AND TRI-MATCH SETS
#        keylist = self.keylist
#        tri_match = self.matches[-1]
#
#
#        # CREATE NORMALIZED TRI-SETS OF CORRESPONDENCE POINTS
#        LPA = self.LPA
#        for cam, camset in enumerate( tri_match ):
#            pointset = []
#            for i, m in enumerate( camset ):
#                if len(m) > 1:
#                    print cam, m
#                    pointset.append( LPA.normalize(cam,
#                                               self.keylist[calcfr-2+i][cam][:,0][m],
#                                               self.keylist[calcfr-2+i][cam][:,1][m]) )
#            tri_match[cam] = pointset
#        print 'tri_match', type(tri_match), len(tri_match)
#
#        # GET SCALING ESTIMATE FOR THIS TRANSLATION
#        scale = ((self.seqid[calcfr]-self.seqid[calcfr-1])
#                    /float(self.seqid[calcfr-1]-self.seqid[calcfr-2]))
#        print 'scale', scale
#        # CALCULATE TRANSFORMATIONS
#        camcol = [(1,0,0),(0,1,0),(0,0,1),(1,1,0),(1,0,1)]
#        for cam, tset in enumerate(tri_match):
#            print 'cam tset', cam
#            try:
#                a, b, c = tset
#            except:
#                print 'Error in tset split'
#                continue
#            print 'cam tset', cam
#            # TEST FOR REASONABLE FLOW
#            mask = test_vector_flow(a,b,c)
#            print 'len a', len(a[0])
#            a, b, c = a[:,mask], b[:,mask], c[:,mask]
#            print 'len masked a', len(a[0])
#
#
#            # TEST TRIPLETS BY VISUALIZATION AFTER MASK
#            if False:
#                for ak,bk,ck in zip(a.T,b.T,c.T):
#                    plt.plot(ak[0],ak[1], 'ro')
#                    plt.plot(bk[0],bk[1], 'go')
#                    plt.plot(ck[0],ck[1], 'bo')
#                    plt.plot([ak[0],bk[0]],[ak[1],bk[1]], 'm')
#                    plt.plot([bk[0],ck[0]],[bk[1],ck[1]], 'k')
#                plt.show()
#            if len(a[0]) < 10:
#                continue
#            # CALCULATE INITIAL TRANSFORMATION USING GA TO REFINE THE RESULT
#            H_ab = GAP.GA_refine_single_projection(LPA, cam, a, b, front_cam=self.forward_cam, popsize=40, iters=40)
#            # CALCULATE WORLD 3D POINTS FROM RESULT
#            F = GAP.E(GAP.encode5(H_ab))
#            epiHole = GAP.mask_pts_near_epipole(a, b, F=F)
#            X = cv2.triangulatePoints(LPA.P(cam), LPA.Hdot(H_ab, cam)[:3], a[:2,epiHole], b[:2,epiHole])
#            X /= X[3]
##            LPA.show_ladybug()
##            LPA.show_points(X, radius=0.1, color=camcol[cam])
#            # CALCULATE 2ND TRANSFORMATION FROM WORLD POINTS
#            H_ac = H_from_Xx(LPA, cam, X, c[:,epiHole].copy())
#
#            H_ab_gene = GAP.encode5sb( H_ab )[:6]
#            print 'Hab', H_ab_gene
#            print 'Hac', GAP.encode5sb( H_ac )[:6]
#
#            # MULTIPLY BY PREVIOUS SCALE
#            H_ab_gene[5] *= self.prev_scale
#
#            # CALCULATE THE B-C TRANSLATION
#            H_bc_gene = GAP.encode5sb( dot(H_ac,linalg.inv(H_ab)) )[:6]
#            print 'Hbc', H_bc_gene
#
#            # TEST IF DETECTED SCALING IS WITHIN REASON AND ADD TO LIST
#            print  H_bc_gene[5], scale, abs(H_bc_gene[5] - scale), (abs(H_bc_gene[5] - scale) < 0.25)
##            raw_input('pause 2')
#            if (abs(H_bc_gene[5] - scale) < 0.25):
#                self.H_lists[calcfr-1].append( H_ab_gene )
#                self.H_lists[calcfr].append( H_bc_gene )
#                print 'len prev', len(self.H_lists[calcfr-1])
#                print 'len this', len(self.H_lists[calcfr])
#            else:
#                print 'Not adding:', H_ab_gene
#                print 'Not adding:', H_bc_gene
#        self.prev_scale = scale
#
#        # EVALUATE THE PROJECTION COLLECTIONS, RE-EVALUATE PREVIOUS
#        for each in [calcfr-1, calcfr]:
#            Hlist = array(self.H_lists[each])
##            print Hlist
#            print '  PROCESSING H LIST'
#            print 'Number in stack', len(Hlist)
#            me = mean(Hlist,0)
#            st = std(Hlist,0)
#            print repr(me)
#            try:
#                above = Hlist > (me - st)
#                below = Hlist < (me + st)
#                res = sum(above & below, 1) == 6
#                self.Transformation[each] = mean(Hlist[res],0)
#                if isnan(self.Transformation[each][0]):
#                    raise ValueError, 'sodo'
#            except:
#                self.Transformation[each] = me
#            print repr(self.Transformation[each])
#            print
#
#        return self.Transformation[calcfr-1], self.Transformation[calcfr]



class LadybugProjectionAssistant:
    '''Make it easier to use the the Ladybug3 camera's intrinsic and extrinsic
    data and projections.

    The Ladybug provides projection matrices that map points from the camera
    unit to the Ladybug coordinate system.

    Use P for the camera projection: x = dot( P, X )
    Use H for the ladybug projection: X0 = dot( H, X1 )
       ( P = inverse(H)[:3] )

    P is used to project 3D world (or Ladybug) coordinate system points to a
    camera 2D coordinate.

    H is used to translate 3D triangulated points back to previous Ladybug or
    world coordinate systems.
    '''
    def __init__(self, cam_intrinsic_mat=None, ladybug_cam_proj=None):
        self.K = self.getDefaultCIMs()
        if cam_intrinsic_mat:
            if len(cam_intrinsic_mat) in [5,6]:
                self.K = cam_intrinsic_mat



        self.LP = self.getDefaultCPMs()
        if ladybug_cam_proj:
            if len(ladybug_cam_proj) in [5,6]:
                self.LP = ladybug_cam_proj



    def __call__(self, cam_number, power=1):
        '''Get 4x4 ladybug projection.'''
        if power != 1:
            return (mat(self.LP[cam_number])**power).A
        return self.LP[cam_number]



    def H(self, cam_number, power=1):
        '''Get 4x4 ladybug projection.'''
        if power != 1:
            return (mat(self.LP[cam_number])**power).A
        return self.LP[cam_number]



    def I(self, cam_number):
        '''Get inverse of H'''
        return linalg.inv(self.LP[cam_number])



    def P(self, cam_number, power=1):
        '''Get 3x4 camera projection.'''
        if power != 1:
            return (mat(self.LP[cam_number]).I**power).A[:3]
        return linalg.inv(self.LP[cam_number])[:3]



    def PI(self, cam_number):
        return self.P(cam_number, -1)



    def getP(self, H):
        return linalg.inv( H )[:3]



    def dot(self, *args):
        '''Dot product of N matrices in the order given.

        Can pass a single list of matrices as one argument or multiple matrices
        as multiple args.'''
        H = args[0]
        if isinstance(H, list):
            args = H
            H = args[0]
        for i in range(1,len(args)):
            if H.shape[1] != len(args[i]) and args[i].shape == (3,4):
                S = eye(4)
                S[:3] = args[i]
                H = dot(H, S)
            else:
                H = dot(H, args[i])
        return H



    def Idot(self, *args):
        '''Get the inverse of a dot product.

        Inversion of the result from dot().'''
        return linalg.inv(self.dot( *args ))



    def Pdot(self, *args):
        '''Composes a list or series of H translations and returns a camera
        projection P. Last argument is a camera number.

        :args: List and integer or series of matrices and one integer.
            Example: Pdot( [A,B,C,D], 3 ) or Pdot( A, B, C, D, 3 )
        Inversion of the result from dot().'''
        return linalg.inv(self.Hdot( *args ))[:3]



    def Hdot(self, *args):
        '''Composes a list or series of H translations with a Ladybug
        projection. Last argument is a camera number.

        :args: List and integer or series of matrices and one integer.
            Example: Pdot( [A,B,C,D], 3 ) or Pdot( A, B, C, D, 3 )
        Inversion of the result from dot().'''
        if len(args) == 2:
            if isinstance(args[0], list):
                return self.Idot( (self.I(args[1]),) + args[0] )[:3]
        args = (self.I(args[-1]),) + args[:-1]
        return self.dot( *args )



    def H_C2L(self, cam_number, Hcam):
        '''Convert translation of a camera to a translation of the Ladybug.

        Cam_number can be an integer, translation of one camera over two frames
        or a list of two cameras, translation of cam1 in first frame to cam2 in
        second frame.'''
        if isinstance(cam_number, list): cam1, cam2 = cam_number
        else: cam1, cam2 = cam_number, cam_number

        if Hcam.shape != (4,4):
            Hcam = append(Hcam, array([[0,0,0,1]]), 0 )
        return self.dot( self.LP[cam1], Hcam, self.I(cam2) )



    def H_L2C(self, cam_number, Hlady):
        '''Convert translation of the Ladybug to a translation of a camera.

        Cam_number can be an integer, translation of one camera over two frames
        or a list of two cameras, translation of cam1 in first frame to cam2 in
        second frame.'''
        if isinstance(cam_number, list): cam1, cam2 = cam_number
        else: cam1, cam2 = cam_number, cam_number

        if Hlady.shape != (4,4):
            Hlady = append(Hlady, array([[0,0,0,1]]), 0 )
        return self.dot( self.I(cam1), Hlady, self.LP[cam2] )



    def normalize(self, cam_number, x, y=None):
        '''Convert a 2xN array or two N arrays (x and y) of image coordinates
        to normalized (by camera matrix) homogeneous coordinates.'''
        if y == None:
            x, y = x[0], x[1]
        xy1 = array([x, y, ones(len(x))])
        return dot(linalg.inv(self.K[cam_number]), xy1)
    norm = normalize



    def image_coord(self, cam_number, xy1):
        '''Convert a 3xN array of homogeneous normalized coordinates to image
        coordinates a camera.'''
        return dot(self.K[cam_number], xy1)[:2]



    def show_ladybug(self, H=None):
        '''Show Ladybug in Visual Python at origin or at the translated position
        if parameter is given.

        TODO: Implement an additional translation H and show at new position.'''
#        vis.ellipsoid(width=0.12, length=0.08, height=0.08,
#                      color=vis.color.red, opacity=0.2)
        vis.arrow(axis=(0.04, 0, 0), color=(1,0,0) )
        vis.arrow(axis=(0, 0.04, 0), color=(0,1,0) )
        vis.arrow(axis=(0, 0, 0.04), color=(0,0,1) )
        colors = [vis.color.red, vis.color.green, vis.color.blue,
                  vis.color.cyan, vis.color.yellow, vis.color.magenta]
        for P in self.LP:
            R = P[:3,:3]
            pos = dot(P[:3],r_[0,0,0,1])
            pos2 = dot(P[:3],r_[0,0,0.01,1])
            vis.sphere(pos=pos, radius=0.002, color=colors.pop(0))
            vis.box(pos=pos2, axis=dot(R, r_[0,0,1]).flatten(),
                    size=(0.001,0.07,0.09), color=vis.color.red,
                    opacity=0.1)
            vis.arrow(pos=pos,
                      axis=dot(R, r_[0.02,0,0]).flatten(),
                      color=(1,0,0), opacity=0.5 )
            vis.arrow(pos=pos,
                      axis=dot(R, r_[0,0.02,0]).flatten(),
                      color=(0,1,0), opacity=0.5 )
            vis.arrow(pos=pos,
                      axis=dot(R, r_[0,0,0.02]).flatten(),
                      color=(0,0,1), opacity=0.5 )



    def show_points(self, X3D, radius=0.05, color=(1,1,1)):
        for X in X3D.T:
            vis.sphere(pos=X[:3], radius=radius, color=color)



    def test_triangulation_gdpts(self, P, x0, x1, cam=None ):
        # TRIANGULATE POINTS
        if cam != None:
            X = cv2.triangulatePoints(self.PI(cam), self.Pdot(P,cam), x0[:2], x1[:2])
            X /= X[3]

            # TEST REPROJECTION TO IMAGE PLANE
            x0 = dot(self.PI(cam), X)[2] > 0.
            x1 = dot(self.Pdot(P,cam), X)[2] > 0.
        else:
            X = cv2.triangulatePoints(eye(4)[:3], I(P)[:3], x0[:2], x1[:2])
            X /= X[3]

            # TEST REPROJECTION TO IMAGE PLANE
            x0 = dot(eye(4)[:3], X)[2] > 0.
            x1 = dot(I(P)[:3], X)[2] > 0.

        infront = x0 & x1
        return (100*sum(infront))/len(infront), sum(infront), len(infront)



    def getDefaultCIMs(self):
        '''Camera Intrinsic Matrices for each camera unit on ladybug.
        Default matrices for NCKU RS Lab Ladybug3 Camera.'''
        return [array([[ 410.318832,    0.      ,  618.793136],
                          [   0.      ,  410.31856,  816.278112],
                          [   0.      ,    0.      ,    1.      ]]),
                 array([[ 412.314672,    0.      ,  635.074016],
                          [   0.      ,  412.31432,  817.876336],
                          [   0.      ,    0.      ,    1.      ]]),
                 array([[ 407.614592,    0.      ,  636.8653439999999],
                          [   0.      ,  407.613376,  792.038112],
                          [   0.      ,    0.      ,    1.      ]]),
                 array([[ 415.041088,    0.      ,  617.005504],
                          [   0.      ,  415.042128,  808.2288159999999],
                          [   0.      ,    0.      ,    1.      ]]),
                 array([[ 411.028464,    0.      ,  628.136624],
                          [   0.      ,  411.027984,  804.117712],
                          [   0.      ,    0.      ,    1.      ]]),
                 array([[ 408.35256,    0.      ,  620.6128],
                          [   0.      ,  408.351888,  816.28296],
                          [   0.      ,    0.      ,    1.      ]]) ]



    def getDefaultCPMs(self, visualize=False):
        '''The Ladybug API provides the projection matrices that map a point from
        a camera unit's coordinates to the Ladybug coordinate frame.

        Returns transformation H (4 by 4), that translates points x in camera
        coordinates to X in ladybug camera coordinates. X = H x
        Default matrices for NCKU RS Lab Ladybug3 Camera.
        '''
        #TODO: CHANGE NAME, ACTUALLY 'LADYBUG PROJECTION' NOT 'CAMERA PROJECTION'
        #CamToLadybugEulerZYX Rx Ry Rz Tx Ty Tz
        cam0 = r_[-1.560195, 1.568134, -1.563117, 0.041786, -0.001909, -0.000328]
        cam1 = r_[2.136062, 1.567502, 0.879774, 0.011587, -0.040133, -0.000543]
        cam2 = r_[0.706740, 1.568451, -1.809267, -0.035002, -0.022902, 0.000131]
        cam3 = r_[1.760194, 1.570313, -2.011164, -0.032845, 0.025595, 0.000190]
        cam4 = r_[-0.762114, 1.567740, 0.494800, 0.014474, 0.039348, 0.000549]
        cam5 = r_[0.002663, 0.004042, 0.002932, 0.001139, -0.000746, 0.062041]
        cams = cam0, cam1, cam2, cam3, cam4, cam5
        def eulerZYX_to_euclidean(arr6):
            Rx,Ry,Rz,Tx,Ty,Tz = arr6
            c, s = cos, sin
            H = array( \
[[c(Rz)*c(Ry), c(Rz)*s(Ry)*s(Rx)-s(Rz)*c(Rx), c(Rz)*s(Ry)*c(Rx)+s(Rz)*s(Rx), Tx],
 [s(Rz)*c(Ry), s(Rz)*s(Ry)*s(Rx)+c(Rz)*c(Rx), s(Rz)*s(Ry)*c(Rx)-c(Rz)*s(Rx), Ty],
 [-s(Ry),      c(Ry)*s(Rx),                   c(Ry)*c(Rx),                   Tz],
 [0,0,0,1]]
                     )

            # CORRECTION TO RECTIFIED ORIENTATION (image right side up)
            R_CtoImage = cv2.Rodrigues(r_[0.,0.,-pi/2.])[0]
            H[:3,:3] = dot(H[:3,:3], R_CtoImage)

            return H

        camPs = [eulerZYX_to_euclidean(each) for each in cams]

        return camPs



def I(M):
    '''inverts a 4x4 or 3x4 matrix.'''
    if M.shape[0] == M.shape[1]:
        return linalg.inv(M)
    if M.shape == (3,4):
        return linalg.inv(append(M, array([[0,0,0,1]]), 0 ))[:3]



def H_from_Xx(LPA, cam, X, x ):
    '''Get a ladybug translation from a camera's view of the world points.'''
    if X.shape[0] == 4:
        X /= X[3]
    r,t = cv2.solvePnP(X[:3].T, x[:2].T, eye(3), empty(0))[1:3]
#    r = cv2.Rodrigues(linalg.inv(cv2.Rodrigues(r)[0]))[0]
    r,t = r.flatten(), t.flatten()
    H = LPA.dot( LPA(cam), GAP.decode6(r_[r,t]) )
    return H
