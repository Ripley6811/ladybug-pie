#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Sat Dec 31 19:29:23 2011

@AUTHOR: Ripley6811

@PROGRAM: Polygon Object
@VERSION: 2.2

@ABSTRACT:

@INPUT: none
@OUTPUT: none

@TODO: A) Maybe next version can have a 5-tuple of points for each frame (5 cameras)
    instead of one point for each frame/camera ID.
    B) Get skipped frame data from log
    C) Right a method to produce complete key files for each image, maybe do
    this in the main program
    D) The point lists can be converted to arrays if we need to do math on them.

@ACKNOWLEDGEMENTS:
"""
from numpy import array, zeros, sqrt, where, vstack  # IMPORTS ndarray(), arange(), zeros(), ones()
#from visual import *  # IMPORTS NumPy.*, SciPy.*, and Visual objects (sphere, box, etc.)
#import matplotlib.pyplot as plt  # plt.plot(x,y)  plt.show()
#from pylab import *  # IMPORTS NumPy.*, SciPy.*, and matplotlib.*
#import os  # os.walk(basedir) FOR GETTING DIR STRUCTURE
#import pickle  # pickle.load(fromfile)  pickle.dump(data, tofile)
#from tkFileDialog import askopenfilename, askopenfile
import thread
#import SIFT
import time
import os
from collections import namedtuple


class Polygon_Obj():
    """Description of main()"""
    def __init__(self, name='unnamed'):
        # LOL = LIST OF LISTS
        self.name = name  # NAME OF POLYGON
        self.ptcount = 0    # NUMBER OF PTS REGISTERED

        # THE IDs MATCH THE ORDER OF pt AND qc
        self.IDlist = []   # LIST OF FRAME/CAM ID NUMBERS CORRESPONDING TO PTs

        # THE FOLLOWING SHOULD HAVE THE SAME LENGTH
        self.PTlist = []   # LOL, EACH LIST CORRESPONDS TO A SET OF POINT IN DIFFERENT IMAGES
        self.KDlist = []    # (LOL), KEY DESCRIPTORS, CORRESPONDS TO EACH PT IN PTs
            # AT LEAST ONE. ADDS NEW KEYPOINTS IF USER UPDATES A PT'S POSITION
        self.LNlist = []    # LOL, LINE DRAWING MATRIX FOR ALL POINTS (SAME FOR ALL FRAMES)
            # TRIANGULAR MATRIX WHERE EACH ADDITIONAL PT IS ONE LONGER THAN THE LAST

        # NOT USED AT THIS TIME
        self.camPos = []    # STORES THE ESTIMATED CAMERA POSITION (X,Y,Z)

        # DEFAULTS USED WHEN EXPANDING LISTS
        self.defaultLN = False
        self.defaultKD = []



        # DATA STRUCTURES FOR THIS MODULE
        self.IDdtypes = [('framecamID', 'int'),
                         ('skip_next',  'int')]
        self.ID = namedtuple('ID', [f[0] for f in self.IDdtypes])
        '''Storage tuple for frame data.

        framecamID = (int) The frame + cam number ID for the image.
        skip_next = (int) The number of frames skipped to the next recorded frame. Use as
            multiplier for point flow estimation.
        '''
        self.defaultID = self.ID(0, 0)


        self.PTdtypes = [('x', 'float'), ('y', 'float'),
                         ('qc', 'bool'),
                         ('vx', 'float'), ('vy', 'float'),
                         ('depth', 'float'),
                         ('r', 'int'), ('g', 'int'), ('b', 'int')]
        self.PT = namedtuple('PT', [f[0] for f in self.PTdtypes]) # ADD RGB? # K_ ARE THE SIFT KEY FIELDS
        '''Storage tuple for point data.

        x = (float) Horizontal pixel position in image.
        y = (float) Vertical pixel position in image.
        qc = (bool) Distinguish a user defined point (True) or estimated point (False).
        vx = (float) Horizontal pixel flow velocity to next frame.
        vy = (float) Vertical pixel flow velocity to next frame.
        depth = (float) Distance of pixel light source from camera (distance to object).
        r = (int) Red of pixel
        g = (int) Green of pixel
        b = (int) Blue of pixel
        '''
        self.defaultPT = self.PT(-1., -1., False, 0., 0., -1., -1, -1, -1)


        # START AN UPDATE THREAD TO CREATE KEY FILES WHEN NECESSARY
        # AND MATCH KEY DATA TO USER DEFINED POINTS
        # AND SEARCH FOR MATCHING POINTS IN OTHER IMAGES
#        thread.start_new_thread( self.SIFTing_thread, (3,) )


    def add_ID(self, ID):
        if ID not in [each.framecamID for each in self.IDlist]:
            self.IDlist.append( self.ID(ID, 0) )
            self.PTlist.append( [self.defaultPT]*self.ptcount )


    def add(self, ID, pt):
        # ADD FRAME/CAM ID IF IT DOESN'T EXIST AND FILL WITH DEFAULT POINTS
        if ID not in [each.framecamID for each in self.IDlist]:
            self.add_ID( ID )

        # GET INDEX OF FRAME/CAM ID
        nID = [each.framecamID for each in self.IDlist].index(ID)

        # ADD DEFAULT PT TO ALL LISTS THEN OVERWRITE THE USER INDICATED PT
        nPT = self.ptcount
        self.ptcount = self.ptcount + 1
        for ptl in self.PTlist:
            ptl.append( self.defaultPT )
        self.PTlist[nID][nPT] = self.defaultPT._replace(x=pt[0], y=pt[1], qc=True)
#        self.KDlist.append( self.retrieve_best_key(pt, filename) )

        self.LNlist.append( [self.defaultLN]*nPT )
        if len(self.LNlist) > 1: self.LNlist[-1][-1] = True
        if len(self.LNlist) > 2: self.LNlist[-1][0] = True
        if len(self.LNlist) > 3: self.LNlist[-2][0] = False

#        self.KDs.append( self.defaultKD )
        print 'PT ADDED:', self.PTlist[nID][nPT], 'in', self.IDlist[nID]
        print self.PTlist[nID][nPT].x
#        if filename:
#            thread.start_new_thread( self.run_pt_SIFT, (filename, pt, nPT) )
#            print 'KD SPACE:', self.KDs[nPT]
#        self.SIFTing_thread(5)

#    def retrieve_best_key(self, pt, filename):
#        try:
#            print 'Retrieving key from', filename + '.key'
#            keys = SIFT.read_image_key(filename + '.key')
#
#            dx = keys['x'] - pt[0]
#            dy = keys['y'] - pt[1]
#            dist = sqrt(dx**2 + dy**2)
#            i = where( dist == min(dist) )
#
##            print type(keys[i]), keys[i]
#            return keys[i]
#        except IOError:
#            print 'IOError in retrieve_best_key():', filename
#            return array([])


    def get_PTarray(self, ID):
        try:
            nID = [each.framecamID for each in self.IDlist].index(ID)
            pt_array = array(self.PTlist[nID], dtype=self.PTdtypes)
        except ValueError:
            pt_array = []

        return pt_array



    def get_LNlist(self, ID):
        '''Can change this to return a LOL where each item is a polygon.
        '''
        draw_order = [] # OUTPUT
        if self.ptcount > 0:
            if ID in [each.framecamID for each in self.IDlist]:
                nID = [each.framecamID for each in self.IDlist].index(ID)
                for nPT in xrange( self.ptcount ):
                    # GET STARTING POINT FOR LINE
                    px, py = self.PTlist[nID][nPT].x, self.PTlist[nID][nPT].y
                    # ADD LINES TO ALL CONNECTED END POINTS
                    for jPT in xrange(nPT):
                        if self.LNlist[nPT][jPT]:
                            jx, jy = self.PTlist[nID][jPT].x, self.PTlist[nID][jPT].y
                            if -1 not in (px, py, jx, jy): # NEG 1 IS NO POINT DATA
                                draw_order.append( (nPT, jPT) )
        return draw_order





    def remove(self, ID, pt):
        nPT = self.get_pt_index( ID, pt, 1 )

        self.ptcount = self.ptcount - 1
        # DELETE THE INDEX OF pt FROM RECORDS
        del self.PTs[nPT]
        del self.QCs[nPT]
        del self.KDs[nPT]
        # DELETE FROM END OF LINES LIST AND CONNECT THE ENDS
        del self.LNs[-1]
        if len(self.LNs) > 2: self.LNs[-1][0] = True





    def move_pt(self, ID, nPT, pt):
        nID = [each.framecamID for each in self.IDlist].index(ID)
        self.PTlist[nID][nPT] = self.PTlist[nID][nPT]._replace(x=pt[0], y=pt[1])




    def undueAdd(self):
        # REMOVES THE LAST POINT ADDED
        if self.ptcount > 0:
            self.remove( self.IDs[0], self.PTs[-1][0] )



    def sort_IDs(self):
        for i,l in enumerate(self.PTs):
            self.PTs[i] = [pt[1] for pt in sorted(zip(self.IDs,l))]
        for i,l in enumerate(self.QCs):
            self.QCs[i] = [qc[1] for qc in sorted(zip(self.IDs,l))]
        # FINALLY SORT IDS
        self.IDfname = [fname[1] for fname in sorted(zip(self.IDs,self.IDfname))]
        self.IDs = sorted(self.IDs)



    def print_links(self):
        for nLN in xrange(self.ptcount):
            print nLN, self.LNs[nLN]



#    def SIFTing_thread(self, delay):
#        '''Creates key files for each image in IDs and finds matching points.
#
#        Step 1 - Create a complete SIFT key file if it doesn't already exist.
#            Convert *.SIFTpgm files to *.key.
#        Step 2 - Add velocity estimate to user selected points.
#            Do a SIFT match for estimate. Update if points moved by user.
#            Check if points are qc'd then ensure the vx vy are in accordance.
#        Step 3 - Find estimated points in contiguous images.
#        '''
#        print 'thread started'
#        while True:
#            # PROCESS AND DELETE ANY *.SIFTpgm FILES IN DIRECTORY
#            dirList = os.listdir(os.getcwd())
#            for fname in dirList:
#                fname = os.path.splitext(fname)
#                if fname[1] == '.SIFTpgm':
#                    if not os.path.exists(fname[0]+'.key'):
#                        try:
#                            SIFT.pgm2key( fname[0] + fname[1] )
#                        except AssertionError:
#                            continue
#                    try:
#                        os.remove(fname[0] + fname[1])
#                    except WindowsError:
#                        pass

            # REDUCE THE KEYS BY COMPARING CONSECUTIVE IMAGES
                # but those excluded may be needed for edge matching between
                # cameras... Maybe create separate key match files for matches
                # forward in time from each image and between cameras















#            for ID in self.IDlist:
#                if not os.path.exists(ID.filename + '.key'):
#                    print 'SIFTing_thread: Creating key file for', ID
#                    try:
#                        SIFT( ID.filename, rotate=-90 )
#                    except:
#                        print 'SIFTing_thread: Problem creating SIFT key file.',
#                        print 'Possibly bad image filename.'


            #!! Ensure that no changes are made while an update is processed
#            if self.ptcount > 0:
#                do_reverse = True if self.defaultPT in self.PTlist[0] else False
#                for nID in xrange(1, len(self.IDlist)):
#                    if self.defaultPT in self.PTlist[nID]:
#                        matches = array(SIFT.match_pairs(
#                                SIFT.read_image_key(self.IDlist[nID-1].filename + '.key'),
#                                SIFT.read_image_key(self.IDlist[nID].filename + '.key') ))
#                        for i, pt1 in enumerate(self.PTlist[nID]):
#                            if pt1 == self.defaultPT and self.PTlist[nID-1][i] != pt1:
#                                pt0 = self.PTlist[nID-1][i]
#                                dx = matches[:,0] - pt0.x
#                                print 'dx', dx
#                                dy = matches[:,1] - pt0.y
#                                distarr = sqrt(dx**2 + dy**2)
#                                imatch = where(distarr == min(distarr))
#                                self.PTlist[nID][i] = self.PTlist[nID][i]._replace(x=matches[imatch,2],y=matches[imatch,3])




#                        if self.PTlist[nID][nPT] == self.defaultPT:
#                            if self.PTlist[nID-1][nPT] != self.defaultPT:
#                                # TEMPORARY OUTPUT UNTIL METHOD IS WRITTEN
#                                print 'SIFTing_thread: Run SIFT on', self.IDlist[nID], 'pt{0}'.format(nPT)
#                    if do_reverse:
#                        for nID in reversed(xrange(len(self.IDlist)-1)):
#                            pass
#
#            time.sleep(delay)
#        print "SIFTing_thread: Polygon manager's update thread exited!"
#        except:
#            print 'SIFTing_thread: ERROR OCCURRED IN THREAD'
#            # restart thread??


    def check_KDs(self):
        boolout = []
        for kd in self.KDs:
            if kd:
                boolout.append( True )
            else:
                boolout.append( False )
        print boolout


    def polygon_region(self, ID):
        if ID in self.pts.keys():
            x = [10000,-1]
            y = [10000,-1]
            for (px, py) in self.pts[ID]:
                if px < x[0]: x[0] = px
                if px > x[1]: x[1] = px
                if py < y[0]: y[0] = py
                if py > y[1]: y[1] = py
            return [x[0], y[0], x[1], y[1]]
        else:
            print 'Can not find polygon data for', ID
            return None






def main():
    po = Polygon_Obj()
    po.name = 'sara'
    print po.LNlist, po.name
    po.add( 0, [1.0,2.1], 'asdfg')
    po.add( 0, [3.2,4.3])
    print po.LNlist, po.name
    po.add( 0, [5.2,6.3])
    po.add( 0, [7.2,8.3])
    po.add( 1243, [3.2,4.3])
    po.add( 2543, [5.1,6.3])
    po.add( 3768, [3.2,4.3])

#    po.sort_IDs()
    ddd = [('x', 'int'),
                         ('y', 'int'),
                         ('depth', 'float'),
                         ('qc', 'bool'),
                         ('r', 'int'),
                         ('g', 'int'),
                         ('b', 'int')]
    PTarr = array(po.PTlist, dtype=ddd)
    print '\n\n\n',PTarr.dtype
#    PTarr = array([array(ptl, dtype=[('x', 'int'),
#                         ('y', 'int'),
#                         ('depth', 'float'),
#                         ('qc', 'bool'),
#                         ('r', 'int'),
#                         ('g', 'int'),
#                         ('b', 'int')]))
    print PTarr.shape



#    po.print_links()
#    po.undueAdd()
#    po.undueAdd()
#    po.undueAdd()
#    po.undueAdd()
#    po.undueAdd()
#    po.print_links()
    print '\n\n\n'

    while True:
        pass

if __name__ == '__main__':
    main()