#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@SINCE: Created on Sat Dec 24 22:52:12 2011

@AUTHOR: Ripley6811

@PROGRAM: SIFT package
@VERSION: 3.0
@CHANGE: Changed algorithm to take advantage of NumPy array speed.
        Previously processed python lists when matching keys.

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
__contact__ = 'tastethejava@hotmail.com'
__copyright__ = 'none'
__license__ = 'undecided'
__date__ = 'Sat Dec 24 22:52:12 2011'
__version__ = '3.0'


from numpy import array, empty, sqrt, sum, where, delete, vstack, hstack, newaxis, arange  # IMPORTS ndarray(), arange(), zeros(), ones()
import matplotlib.pyplot as plt  # plt.plot(x,y)  plt.show()
#from matplotlib.patches import Ellipse
#from pylab import *  # IMPORTS NumPy.*, SciPy.*, and matplotlib.*
import os  # os.walk(basedir) FOR GETTING DIR STRUCTURE
#import pickle  # pickle.load(fromfile)  pickle.dump(data, tofile)
#from tkFileDialog import askopenfilename, askopenfile
from PIL import Image
import subprocess
import random
import time
import glob




# SET SIFTWIN32 LOCATION (CANNOT CONTAIN SPACES ANYWHERE IN CALL TO SIFT)
sift_fname = r'C:\Dropbox\siftWin32.exe'
if not os.path.exists(sift_fname):
    print 'siftWin32.exe not found!'





####################################################################
def SIFT( im1_fname,         im2_fname=None, 
                 im1_crop=None,  im2_crop=None, 
                 im1_band=-1,    im2_band=-1,
                 threshold=0.6, rotate=0,
                 verbose=False, show=False):
    '''Returns the key point data for a single image in two arrays (tuple)
    or if a 2nd image is passed it returns an array of matches between images.
    
    Loads a band from an image and crops it (if supplied). Then runs SIFT
    to produce key point file. Finally, returns the key point data in a two
    array tuple or returns an array of matches between two images if a 
    second image is given in the arguments.
    If crop window is given, then the returned key_point coordinates will be 
    restored to the position of the original image in the data structure (not
    the position in the cropped image).
    If the key file is made for an entire image (crop=None), then it is not 
    deleted, otherwise key files for sub-sections of images are given temp 
    names and then deleted.
    
    @arg im1_fname: (String) The filename of the 1st image to process.
    @kwarg im2_fname: (String) The filename of the 2nd image to process.
        (Default is None)
    @kwarg im1_crop: (tuple: 4 ints) The top left and bottom right of crop box
        for 1st image. (x0, y0, x1, y2) (Default is None)
    @kwarg im2_crop: (4 int tuple) The top left and bottom right of crop box
        for 2nd image. (x0, y0, x1, y2) (Default is None)
    @kwarg im1_band: (int) The band to extract from 1st image to use in SIFT. 
        Default is a conversion of the image to greyscale. (Default is -1)
    @kwarg im2_band: (int) The band to extract from 2nd image to use in SIFT. 
        Default is a conversion of the image to greyscale. (Default is -1)
    @kwarg threshold: (float) The threshold to use in the key point matching 
        algorithm. (Default is 0.6)
    @kwarg rotate: (int) Degrees of rotation to apply to images before cropping
        and SIFTing. -90 is a clockwise rotation of 90 degrees. (Default is 0)
    @kwarg verbose: (bool) Output process updates to console. (Default is False)
    @kwarg show: (bool) Output cropped images to default viewer. 
        (Default is False)
        
    @return: If only one image - (structured array). Contains the x, y, scale, 
        orientation, and 128 descriptors for each key point.
        
        If two images - (array) Matches found between images. Four columns;
        x,y of 1st image and corresponding x,y of 2nd image.
    '''
    # PROCESS THE FIRST IMAGE
    img1_band = get_image(im1_fname, band=im1_band, rotate=rotate)
    if im1_crop: img1_band = img1_band.crop( im1_crop )
    if show: img1_band.show()
    img1_keyname = create_image_key(img1_band, outfname=('' if im1_crop else im1_fname) )
    im1_crop_corner = ((0,0) if not im1_crop else (im1_crop[0],im1_crop[1]))
    img1_keypoints = read_image_key(img1_keyname, displacement=im1_crop_corner, delete=(True if im1_crop else False) )

    # PROCESS THE SECOND IMAGE IF IT EXISTS AND RETURN MATCHES
    # ELSE RETURN THE KEY DICTIONARY FROM FIRST IMAGE
    if im2_fname:
        if verbose: print 'SIFT processing and returning coordinate matches between two images.'
        img2_band = get_image(im2_fname, band=im2_band, rotate=rotate)
        if im2_crop: img2_band = img2_band.crop( im2_crop )
        if show: img2_band.show()
        img2_keyname = create_image_key(img2_band, outfname=('' if im2_crop else im2_fname) )
        im2_crop_corner = ((0,0) if not im2_crop else (im2_crop[0],im2_crop[1]))
        img2_keypoints = read_image_key(img2_keyname, displacement=im2_crop_corner, delete=(True if im2_crop else False) )
        if verbose: print 'Total key points:\n   image 1:{0}\n   image 2:{1}'.format(len(img1_keypoints[0]),len(img2_keypoints[0]))
        return match_pairs( img1_keypoints, img2_keypoints, threshold, verbose=verbose, window=im1_crop)
    else:
        if verbose: print 'SIFT returning keypoint array for single image.'
        return img1_keypoints # KEY POINTS FROM SIFT KEY FILE



    
def match_pairs(aKeys, bKeys, 
                      threshold=0.6, scale_diff=2.0, orientation_diff=2.0, 
                      verbose=False, window=None):
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
    MAX_ARRAY_SIZE = 5e7
    inc = int( MAX_ARRAY_SIZE / 128 / len(bKeys['descriptors']) )
    sections = []
    for i in xrange(0, len(aKeys['descriptors']), inc):
        dif = aKeys['descriptors'][:,newaxis][i:i+inc] - bKeys['descriptors']
        dsq = sqrt(sum(dif**2, axis=2))
        sections.append(dsq)
    dsqfull = vstack(sections)
#    print dsqfull.shape
    
    # FIND THE INDICES OF THE TWO SMALLEST DSQ THAT SATISFY THE MATCH THRESHOLD
    Aorder = dsqfull.argsort(axis=1)
    Aord0 = Aorder[:,0]
    Aord1 = Aorder[:,1]
    z0 = arange(len(dsqfull))
    Aind = where(dsqfull[z0,Aord0]/dsqfull[z0,Aord1] < threshold)[0]

    ds = abs(aKeys[Aind]['scale']-bKeys[Aord0[Aind]]['scale'])
    do = abs(aKeys[Aind]['orientation']-bKeys[Aord0[Aind]]['orientation'])
#    print type(ds), type(do)
    
    # FIND THE INDICES WITHIN SCALE AND ORIENTATION LIMITS
    SOind = (where(ds < scale_diff, True, False) & 
             where(do < orientation_diff, True, False) )
    
    # CREATE OUTPUT LIST OF MATCHES
    matches = zip( aKeys[Aind]['x'][SOind], aKeys[Aind]['y'][SOind], 
         bKeys[Aord0[Aind]]['x'][SOind], bKeys[Aord0[Aind]]['y'][SOind],
         abs(aKeys[Aind]['scale'][SOind] - 
             bKeys[Aord0[Aind]]['scale'][SOind]),
         abs(aKeys[Aind]['orientation'][SOind] - 
             bKeys[Aord0[Aind]]['orientation'][SOind]) )
    matches = sorted(list(set(matches)))
         
    return matches
    
    




def read_image_key(key_fname, displacement=(0,0), delete=False):
    '''Read key point data from file into a NumPy structured array.
    
    @arg key_fname: The name of the file to open that contains SIFT key data.
    @kwarg displacement: (tuple: 2 ints) The offset of the crop from original 
        image. This gets added back to the key data x,y pair to show the 
        location in the original full image. (Default is (0,0))
    @kwarg delete: (bool) Option to delete the key file after it is read into
        the arrays. (Default is False)
        
    @return: (structured array). Contains the x, y, scale, orientation, and 
        128 descriptors for each key point.
    @rtype: dtype=[('x','float'), ('y','float'), ('scale','float'),
        ('orientation','float'), ('descriptors','int',(descriptorTotal,))]
    '''
    keys = None
    outfname = os.path.splitext(key_fname)
    if outfname[1] == '.key':
        key_fname = outfname[0] # DROP ENDING
    key_fname = glob.glob('*' + key_fname + '.key')
    if not key_fname:
        return None
    key_fname = key_fname[0]
    print 'READ_IMAGE_KEY:', key_fname
    with open(key_fname, 'r') as rfile:
        count = -1
        descList = []
        for ln, line in enumerate(rfile):
            if ln == 0:
                # FIRST LINE OF KEYPOINT FILE IS NUMBER OF KEYPOINTS
                keyTotal, descriptorTotal = [int(n) for n in line.split(' ')]
                keys = empty(keyTotal,
                             dtype=[('x','float'),
                                    ('y','float'),
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
                keys[count] = (yxso[1] + displacement[0], 
                               yxso[0] + displacement[1], 
                               yxso[2], 
                               yxso[3],
                               empty(descriptorTotal, int) )
    rfile.close()

    # DELETE THE TEMP KEY FILE
    while delete:
        if os.path.exists(key_fname):
            try:
                os.remove(key_fname)
                delete = False
            except WindowsError:
                print 'key deletion failed. trying again...'
                continue
        else:
            delete = False
            
    # RETURN KEY DATA
    return keys

    

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
    # READ KEY FILE
    key_data = read_image_key(tmpfname+'.key', delete=True)
    
    # DELETE THE TEMP PGM FILE
    while True:
        if os.path.exists(tmpfname+'.pgm'):
            try:
                os.remove(tmpfname+'.pgm')
            except WindowsError:
                print 'pgm deletion failed. trying again...'
                continue
        else:
            break
        
    return key_data
    
    
    
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

