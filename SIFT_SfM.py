#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@SINCE: Created on Sat Dec 24 22:52:12 2011

@AUTHOR: Ripley6811

@PROGRAM: SIFT_SfM package
@DESCRIPTION: This version returns matches as lists of matching indices.
    An array is returned for each keyset which can be used as a mask for the
    keyset array.
    This version also can merge matchsets with the merge_matchsets or
    extend_matchset functions.

@VERSION: 3.0
@CHANGE: Corresponding point matches are returned as a mask for the original
    key lists.

@REQUIRES: siftWin32.exe. Make sure the path is correct.
@PRECONDITION: Images must be realistically orientated. Otherwise set the
    'rotate' keyword arg.
@POSTCONDITION: ...

@ABSTRACT: Methods related to SIFT
    SIFT( im1_fname : FILENAME FOR BASE (OR ONLY) IMAGE
         [im2_fname=None] : FILENAME FOR 2ND IMAGE
         [im1_crop=None] : SEARCH AREA OF BASE IMAGE
         [im2_crop=None] : SEARCH AREA OF 2ND IMAGE
         [im1_band=-1] : BAND SELECTION (0,1,2=r,g,b OR GREYSCALED)
         [im2_band=-1] : BAND SELECTION (0,1,2=r,g,b OR GREYSCALED)
         [threshold=0.6] : MATCHING THRESHOLD
         [rotate=-90] : ROTATION BEFORE APPLYING CROPPING AND SIFT
         [verbose=False] : PRINT UPDATES TO CONSOLE
         [show=False] : OUTPUT IMAGE(S) TO DEFAULT VIEWER
    SIFT returns the key point data if only one image is given, otherwise
    it returns a list of matching points between two images


@TODO: A) Add in Tk file selector to get siftWin32.exe location from user if it
    is not found in the preset location.
    B) Maybe add in check to see if key file already exists and use it, but
    maybe this should be handled within the program calling these methods.

@ACKNOWLEDGEMENTS:
"""
# EPYDOC RECOGNIZED
__author__ = 'Ripley6811'
__contact__ = 'python at boun.cr'
__copyright__ = 'none'
__license__ = 'undecided'
__date__ = 'Sat Dec 24 22:52:12 2011'
__version__ = '3.0'


from numpy import sort, array, empty, r_, pi, sqrt, sum, where, delete, vstack, hstack, newaxis, arange  # IMPORTS ndarray(), arange(), zeros(), ones()
import matplotlib.pyplot as plt  # plt.plot(x,y)  plt.show()
import os  # os.walk(basedir) FOR GETTING DIR STRUCTURE
from PIL import Image
import subprocess
import random
import time
import glob
from cv2 import cartToPolar




# SET SIFTWIN32 LOCATION (CANNOT CONTAIN SPACES ANYWHERE IN CALL TO SIFT)
sift_fname = r'C:\Dropbox\siftWin32.exe'
if not os.path.exists(sift_fname):
    print 'siftWin32.exe not found!'


####################################################################
def SIFTkeys(image, window=None):
    # LOAD FILE
    if isinstance(image, str):
        im = Image.open(image)
    else:
        im = image.copy()

    # CONVERT TO SINGLE BAND
    im = im.convert('L')

    # CROP IMAGE TO WINDOW
    if window != None:
        cx,cy = window[:2]
        im = im.crop(window)
    else:
        cx,cy = 0,0

    # RUN SIFT AND GET KEY DATA
    kdata = PIL2keys(im)

    # CROP CORRECTION (BACK TO UNCROPPED IMAGE COORDINATES)
    kdata['x'] += cx
    kdata['y'] += cy

    # SORT BY Y
    kdata = sort(kdata, order=['y'], kind='quicksort')

    # RETURN KEY DATA
    return kdata




def match_pairs(aKeys, bKeys,
                      threshold=0.8, scale_diff=2.0, orientation_diff=2.0,
                      verbose=False, window=None, ptlimit=None):
    '''Finds matches between sets of SIFT keypoints.

    Returns a list of tuples describing the positions of corresponding
    points in each image along with the difference in scale and orientation.
    (ax,ay,bx,by,ds,do). (Window can have negative values.)

    @arg aKeys: (struct array) See read_image_key method for details.
    @arg bKeys: (struct array) See read_image_key method for details.
    @kwarg threshold: (float) Matching parameter. (Uniqueness of match?)
    @kwarg scale_diff: (float) Matching parameter. Upper limit of difference.
    @kwarg orientation_diff: (float) Matching parameter. Upper limit of diff.
    @kwarg verbose: (bool) Show information while running method.
    @kwarg window: (tuple: 4 floats) Top left and bottom right of match window
        in first image (aKeys).
    @return: List of tuples
    '''
    print 'Finding matches... ( threshold', threshold, ')'

    # LIMIT THE NUMBER OF POINTS IN ORDER TO RUN FASTER
    if ptlimit != None:
        assert isinstance(ptlimit, int), 'Point Limit must be an integer'
        alen = len(aKeys)
        if ptlimit < alen:
            aKeys = aKeys[random.sample(range(alen), ptlimit)]
        blen = len(bKeys)
        if ptlimit < blen:
            bKeys = bKeys[random.sample(range(blen), ptlimit)]


    # CHECK IF THERE ARE ANY KEY POINTS IN 'A'
    if len(aKeys['x']) == 0 or len(bKeys) < 2:
        print 'No keys or insufficient keys in the two sets.'
        return []

    # SELECT KEY POINTS IN 'A' BASED ON WINDOW
    if window:
        xarr, yarr = aKeys['x'], aKeys['y']
        selectA = (where(xarr > window[0], True, False) &
                   where(yarr > window[1], True, False) &
                   where(xarr < window[2], True, False) &
                   where(yarr < window[3], True, False))
        aKeys = aKeys[selectA]

        # CHECK AGAIN IF THERE ARE ANY KEY POINTS IN 'A'
        if len(aKeys['x']) == 0:
            print 'No keys in set A are within window.',
            print 'Check if window is scaled up properly.'
            return []

    # COMPARE WITH 'B'
    MAX_ARRAY_SIZE = 4e7
    inc = int( MAX_ARRAY_SIZE / 128 / len(bKeys['descriptors']) )
#    inc = 50
    sections = []
    print 'Matching', len(aKeys), 'from A with', len(bKeys), 'in B'
    for i in xrange(0, len(aKeys), inc):
        # CHANGED TO SPAN THE MIDDLE 5000 OF BOTH A AND B KEYS
        dif = aKeys['descriptors'][:,newaxis][i:i+inc] - bKeys['descriptors']
        dsq = sqrt(sum(dif**2, axis=2))
        del dif
        sections.append(dsq)
        del dsq
    dsqfull = vstack(sections)

    # FIND THE INDICES OF THE TWO SMALLEST DSQ THAT SATISFY THE MATCH THRESHOLD
    Aorder = dsqfull.argsort(axis=1)
    Aord0 = Aorder[:,0]
    Aord1 = Aorder[:,1]
    z0 = arange(len(dsqfull))
    Aind = where(dsqfull[z0,Aord0]/dsqfull[z0,Aord1] < threshold)[0]

    ds = abs(aKeys[Aind]['scale']-bKeys[Aord0[Aind]]['scale'])
    do = abs(aKeys[Aind]['orientation']-bKeys[Aord0[Aind]]['orientation'])

    # FIND THE INDICES WITHIN SCALE AND ORIENTATION LIMITS
    SOind = (ds < scale_diff) & (do < orientation_diff)

    print sum(SOind), 'matches found.'
    return array([Aind[SOind],Aord0[Aind][SOind]])





def create_image_key(imArr, outfname=''):
    '''Accepts an image (Numpy 2D array).
    Runs SIFT on each image giving an arbitrary name.
    Returns the filename for the key points in the image (*.key).
    (Creates and deletes a temporary PGM files used in SIFT).
    '''
    global sift_fname # GET LOCATION OF SIFTWIN32.EXE
    assert os.path.exists(sift_fname)
    # REMOVE ANY EXTENSION FROM FILENAME
    outfname = os.path.splitext(outfname)[0]

    # DETERMINE OUTPUT NAME FOR KEYPOINT DATA FILE
    if not outfname:
        outfname = 'tmp' + str(time.time()) + str(random.randint(1000,9999))

    # CONVERT IMAGE ARRAY TO PGM
    imArr.save( outfname + '.pgm', 'PPM')

    # RUN SIFTWIN32.EXE FROM HIDDEN CMD
    assert os.path.exists(outfname + '.pgm')
    subprocess.call( sift_fname+'<'+outfname+'.pgm>'+outfname+'.key', shell=True)

    # DELETE THE TEMP PGM FILE
    while True:
        if os.path.exists(outfname+'.pgm'):
            try:
                os.remove(outfname+'.pgm')
            except WindowsError:
                print 'pgm deletion failed. trying again...'
                continue
        else:
            break

    # RETURN NAME OF SAVED KEY FILE
    return outfname + '.key'


def pgm2key(PGMfilename):
    '''Creates *.key from arg filename. Nothing returned.

    @arg PGMfilename: Name of file to process with SIFT
    '''
    global sift_fname # GET LOCATION OF SIFTWIN32.EXE
    assert os.path.exists(sift_fname)

    # REMOVE ANY EXTENSION FROM FILENAME
    outfname = os.path.splitext(PGMfilename)[0]

    # RUN SIFTWIN32.EXE FROM HIDDEN CMD
    assert os.path.exists(PGMfilename)
    subprocess.call( sift_fname+'<'+PGMfilename+'>'+outfname+'.key', shell=True)



def get_image(imfilename, band=-1, rotate=0, show=False):
    '''Opens and returns an IDL like image array where the first index is the
    band, i.e. 0=Red, 1=Green, 2=Blue. If error occurs in unpacking the three
    bands then it assumes there is only one band and returns it.
    Default return is a greyscale conversion to single band.
    '''
    # OPEN FILE
    im = Image.open(imfilename)
#    im = Image.open(os.path.splitext(imfilename)[0] + '.thumbnail')
    im = im.rotate(rotate)
    # ROTATE AND DISPLAY IN WINDOWS PHOTO VIEWER
    if show: im.show()
    # PUT EACH BAND IN SEPARATE ARRAY AFTER TRANSPOSE
    try: imBands = im.split()
    except: return im
    # CONVERT TO GREY SCALE SINGLE BAND (DEFAULT)
    if band not in (0,1,2): return im.convert('L')
    # RETURN SINGLE BAND
    return imBands[band]


def PIL2keys(image):
    '''Pass a single band PIL image.
    Pre-crop and store crop displacement separately.

    @arg image: PIL (cropped) single-band image
    @return: (structured array) SIFT key data for image
    '''
    global sift_fname # GET LOCATION OF SIFTWIN32.EXE
    assert os.path.exists(sift_fname)
    # CREATE TEMPORARY FILE NAME
    tmpfname = 'tmp' + str(time.time()) + str(random.randint(1000,9999))
    # SAVE PGM FILE FOR SIFT PROCESSING
    image.save( tmpfname + '.pgm', "PPM" )
    # RUN SIFTWIN32.EXE FROM HIDDEN CMD
    subprocess.call( sift_fname+'<'+tmpfname+'.pgm>'+tmpfname+'.key', shell=True)
    # READ KEY FILE (AND DELETE IT)
    key_data = read_image_key(tmpfname+'.key', delete=True)
    # DELETE THE TEMP PGM FILE
    delete_file(tmpfname+'.pgm')
    # RETURN KEY DATA
    return key_data


def matchMapping(set1, set2):
    mapping = [[],[]]
    for i1 in range(len(set1)):
        for i2 in range(len(set2)):
            if tuple(set1[i1,2:]) == tuple(set2[i2,:2]):
                mapping[0] = i1
                mapping[1] = i2
    return mapping


def merge_matchsets(match1, match2):
        mm = [[],[],[]]
        A = match1[0]
        B1 = match1[1]
        B2 = match2[0]
        C = match2[1]
        for b1 in B1:
            if b1 in B2:
                mm[0].append(A[where(B1 == b1)][0])
                mm[1].append(b1)
                mm[2].append(C[where(B2 == b1)][0])
        mm = array([array(m) for m in mm])
        return mm

def extend_matchset(match1, match2):
    # ADD A NEW ROW TO MATCH1 TO FILL
    len2 = len(match2)
    M = append(array(match1), zeros((len2-1,len(match1[0])))-1, 0)

    B1 = M[-len2]
    B2 = match2[0]
    for b1 in B1:
        if b1 in B2:
            M[-len2+1:,where(B1 == b1)] = match2[1:,where(B2 == b1)]

    return M[:,M[-1] != -1].copy()



def read_image_key(key_fname, delete=False):
    '''Read key point data from file into a NumPy structured array.

    @arg key_fname: The name of the file to open that contains SIFT key data.
    @kwarg delete: (bool) Option to delete the key file after it is read into
        the arrays. (Default is False)
    @return: (structured array). Contains the x, y, scale, orientation, and
        128 descriptors for each key point.
    @rtype: dtype=[('x','float'), ('y','float'), ('scale','float'),
        ('orientation','float'), ('descriptors','int',(descriptorTotal,))]
    '''
    print 'READ_IMAGE_KEY:', key_fname
    with open(key_fname, 'r') as rfile:
        count = -1
        descList = []
        for ln, line in enumerate(rfile):
            if ln == 0:
                # FIRST LINE OF KEYPOINT FILE IS NUMBER OF KEYPOINTS
                keyTotal, descriptorTotal = [int(n) for n in line.split(' ')]
                keys = empty(keyTotal,
                             dtype=[('y','float'),
                                    ('x','float'),
                                    ('scale','float'),
                                    ('orientation','float'),
                                    ('descriptors','int',(descriptorTotal,))])
            elif line[0] == ' ':
                # DESCRIPTOR LINES BEGIN WITH A SPACE
                descList.extend( line.split(' ')[1:] )
                if len(descList) == descriptorTotal:
                    keys['descriptors'][count] = array(descList, int)
                    descList = []
                assert len(descList) < descriptorTotal   # make sure does not go over total
            else:
                # BEGIN NEW KEYPOINT IN DICTIONARY
                count = count + 1   # index of this key in array
                yxso = array(line.split(' ')).astype(float)
                keys[count] = (yxso[0],
                               yxso[1],
                               yxso[2],
                               yxso[3],
                               empty(descriptorTotal, int) )
    rfile.close()

    # DELETE THE TEMP KEY FILE
    if delete:
        delete_file(key_fname)

    # RETURN KEY DATA
    return keys


def delete_file(fname):
    while True:
        if os.path.exists(fname):
            try:
                os.remove(fname)
            except WindowsError:
                print 'File deletion failed:', fname
                continue
        else:
            break


#===============================================================================
# MAIN IS USED FOR TESTING FUNCTIONS
#===============================================================================

def main():
    """Testing area for these methods"""
    os.chdir(r'C:\Ladybug3Data\20101210 - Suhua - PGR original\20101210 - Suhua - NonRectified BMP')

#    read_image_key(r'C:\Users\tutu\Documents\Ladybug3 Video\20101210 - Suhua - NonRectified BMP\ladybug_Color_00003344_Cam4.bmp.key')

    # TWO IMAGES TO COMPARE
    imRfile = r'ladybug_Color_00003344_Cam0.bmp'
    imLfile = r'ladybug_Color_00003344_Cam0.bmp'

    # GET A SINGLE BAND (SIFT ONLY ACCEPTS SINGLE BAND IMAGES)
    Lim = get_image(imLfile, 1, rotate=-90)
    Rim = get_image(imRfile, 3, rotate=-90)
    size = Lim.size
    print size


    # SEND KEY DATA TO FIND MATCHES METHOD
    print 'start'
    t0 = time.time()
    data = SIFT(imLfile,im2_fname=imRfile,
                   im1_crop=(size[0]-400,0,size[0],size[1]),
                   im2_crop=(0,0,400,size[1]),
                   verbose=False, rotate=-90, im1_band=1, im2_band=3 )
    print 'done', time.time()-t0
    print len(data)
    for each in data: print each
#    data = SIFT(imLfile, im2_fname=imRfile,
#                   im1_crop=(size[0]*0/4,668,size[0]*3/4,848),
#                   im2_crop=(size[0]*0/4,668,size[0]*3/4,848),
#                   verbose=True, show=False )

    # PLOT IMAGES WITH MATCHES
    plt.figure()
    plt.title('Left View' + str(Lim.size))
    plt.imshow(Lim.transpose(Image.FLIP_TOP_BOTTOM), cmap='bone')
    plt.colorbar()
    for mset in data:
        plt.text(mset[0], mset[1], 'x', color='r')

    plt.figure()
    plt.title('Right View' + str(Rim.size))
    plt.imshow(Rim.transpose(Image.FLIP_TOP_BOTTOM), cmap='bone')
    plt.colorbar()
    for mset in data:
        plt.text(mset[2], mset[3], 'x', color='r')
    plt.show()


if __name__ == '__main__':
    main()

