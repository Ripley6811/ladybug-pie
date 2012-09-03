#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 27 13:37:38 2011

@AUTHOR: Ripley6811

@PROGRAM:
@VERSION: 3.8
        - Changed GUI organization
        - Switching to the new Polygon_Obj_v2 class
        - Using a new, hopefully faster, method of matching points
            - Only get closest matching keypoint from SIFT for each clicked point
            - Then later, when polygon is finalized, do a single SIFT and find all
                best matching points in new frame
        - Switched to using a class called PolygonObj for managing all polygons

@ABSTRACT:

@INPUT: none
@OUTPUT: none

@TODO: Fix the cropping and scaling of thumbs
        Create a scroll_list of objects
        *Create button to SIFT and locate object in adjacent frames
            Turn SIFT into an option, not integral part
        Add polygon shaping/shifting
        Try running SIFT on a thread and see if it crashes.
            If crashes, then create a SIFT button
        Apply correction to polygon: See if all vectors are similar
        Change to having one thread do all the SIFTing for neighboring images
            -I will probably need other threads later on to do other things

        !Add the GASfM package
        !User delimits the SIFTing area for each camera. Include defaults.


@ACKNOWLEDGEMENTS:
"""

from pylab import *  # IMPORTS NumPy.*, SciPy.*, and matplotlib.*
import os  # os.walk(basedir) FOR GETTING DIR STRUCTURE
#from Tkinter import *
import Tkinter
from tkFileDialog import askopenfilename, asksaveasfilename, askdirectory
from tkSimpleDialog import askstring
from PIL import Image, ImageTk, ImageDraw, ImageChops
#import thread
import time
from Polygon_Obj_v2 import Polygon_Obj as PO
from ladybug_API_interface import Ladybug3stream
#import subprocess
import SIFT
import SIFT_SfM
import glob
from collections import namedtuple
import pickle
#from ladybug_image_series_selector import ladybug_interp_data
from tracking_pack import ShiTomasiTracking, findstereocorrespondence
from scipy import interpolate
import cv2
import random
from Ladybug_SfM import *




class ladybug3D_app(Tkinter.Tk):
    run_location = os.getcwd()
    # 'settings' HOLDS DATA THAT NEEDS TO PERSIST BETWEEN SESSIONS. SAVE AND LOAD.
    default_settings = dict( # DEFAULT SETTINGS
                dir_work=r'C:\Users\tutu\Documents\Ladybug3 Video\20101210 - Suhua - NonRectified BMP',
                dir_stream=r'C:\Users\tutu\Documents\Ladybug3 Video\20101210 - Suhua - Original PGR\Ladybug-Retrun-000005.pgr',
                polyObjs=[PO()],
                imNumStrVar='0',
                camNumStrVar='0',
                totalStrVar='unknown',
                mode=0,
                SIFTit=False,
                geometry='1000x800+100+100',
                maxWidth = 1000,
                maxHeight = 800,
                # (x left, y ltop, y lbottom, x right, y rtop, y rbottom)
                )
    settings = default_settings.copy()
    # TEMPORARY DATA
    disp_images=[None for i in xrange(6)]
    mouseDrag = [False, -1]
    polyRef = 0
    disp_points=[[] for i in xrange(6)]
    disp_lines=[[] for i in xrange(6)]
    modes = ('2 Cameras',
             'Road View',
             '3 Cameras' )

    def __init__(self, parent):
        Tkinter.Tk.__init__(self, parent)
        self.parent = parent

        self.initialize()

    def initialize(self):
        try:
            os.chdir( self.settings['dir_work'] )
        except WindowsError:
            self.set_work_dir()

        self.settings['maxWidth'] = 1000
        self.settings['maxHeight'] = 800
        self.imagesize = (616,808)

        # CREATE THE MENU BAR
        self.create_menu()

        # LEFT HAND SIDE CONTROLS
        self.create_left_controls()

        # MAIN SCREEN CANVAS BINDINGS
        self.create_image_canvas()

        try:
            self.load_last_session()
        except:
            self.settings = self.default_settings.copy()

        try:
            self.geometry( self.settings['geometry'] ) # INITIAL POSITION OF TK WINDOW
        except KeyError:
            self.geometry( self.default_settings['geometry'] ) # INITIAL POSITION OF TK WINDOW

        self.update()
        self.canvas.bind('<Configure>', self.resize )

        self.print_settings( 'Settings on initialization' )



    def create_menu(self):
        # MAIN MENU BAR
        menubar = Tkinter.Menu(self)

        # FILE MENU OPTIONS: LOAD, SAVE, EXIT...
        filemenu = Tkinter.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Open PGR Stream", command=self.open_PGR_stream)
        filemenu.add_command(label="Load last Session", command=self.load_last_session)
        filemenu.add_command(label="Save Session", command=self.save_session)
        filemenu.add_command(label="Load Session", command=self.load_session)
        filemenu.add_command(label="Close PGR Stream", command=self.close_PGR_stream)
        filemenu.add_separator()

        filemenu.add_command(label="Get Calibration Data", command=self.deriveCalibrationData)

        filemenu.add_separator()
        filemenu.add_command(label="Exit (Closes Stream)", command=self.endsession)
        menubar.add_cascade(label="File", menu=filemenu)

        # VIEW MENU OPTIONS
        modemenu = Tkinter.Menu(menubar, tearoff=0)
        self.mode = Tkinter.StringVar()
        self.mode.set(self.modes[self.settings['mode']])
        for m in self.modes:
            modemenu.add_radiobutton(label=m, variable=self.mode, command=self.change_mode)
        menubar.add_cascade(label="View", menu=modemenu)

        # SIFT MENU OPTIONS
        siftmenu = Tkinter.Menu(menubar, tearoff=0)
        siftmenu.add_command(label="Run Calibration Process", command=self.deriveCalibrationData)
        self.SIFTit = Tkinter.BooleanVar()
        try:
            self.SIFTit.set(self.settings['SIFTit'])
        except KeyError:
            self.SIFTit.set(False)
        self.FLOWit = Tkinter.BooleanVar()
        try:
            self.FLOWit.set(self.settings['FLOWit'])
        except KeyError:
            self.FLOWit.set(False)
        siftmenu.add_checkbutton(label="Auto-create SIFT key files", onvalue=True, offvalue=False, variable=self.SIFTit)
        siftmenu.add_checkbutton(label="Show Flow", onvalue=True, offvalue=False, variable=self.FLOWit)
        siftmenu.add_command(label="Delete all temp pgm files (*.SIFTpgm)", command=self.deleteSIFTpgms)
        menubar.add_cascade(label="Flow", menu=siftmenu)

        # HELP MENU OPTIONS: OPEN LADYBUG API HELP, OPEN WORKING DIRECTORY
        helpmenu = Tkinter.Menu(menubar, tearoff=0)
        helpmenu.add_command(label="About", command=hello)
        helpmenu.add_cascade(label="Open Ladybug SDK Help", command=self.loadLadybugSDKhelp)
        helpmenu.add_cascade(label="Open Working Directory", command=self.openWorkingDir)
        menubar.add_cascade(label="Help", menu=helpmenu)

        # SET AND SHOW MENU
        self.config(menu=menubar)



    def create_left_controls(self):
        controls = Tkinter.Frame(self)

        MODES = [
                "Window Selection",
                "Heading Selection",
                "Object Selection",
                "Measure Distance",
                "Off",
                ]

        self.rb = Tkinter.StringVar()
        self.rb.set("L") # initialize

        for mode in MODES:
            b = Tkinter.Radiobutton(controls, text=mode,
                            variable=self.rb, value=mode, command=self.change_click_mode)
            b.pack(anchor=Tkinter.W)
            b.select()


        Tkinter.Label(controls, text='Image Number').pack(side=Tkinter.TOP,padx=10,pady=10)
        self.imNumStrVar = Tkinter.StringVar()
        self.imNumStrVar.set(self.settings.get('imNumStrVar') )
        imNumEntry = Tkinter.Entry(controls, textvariable=self.imNumStrVar, width=10)
        imNumEntry.pack(side=Tkinter.TOP,padx=10,pady=10)
        imNumEntry.bind('<Return>', self.change_view)

        self.totalStrVar = Tkinter.StringVar()
        self.totalStrVar.set(self.settings.get('totalStrVar') )
        Tkinter.Label(controls, textvariable=self.totalStrVar).pack(side=Tkinter.TOP,padx=10,pady=10)

        Tkinter.Label(controls, text='Camera Number').pack(side=Tkinter.TOP,padx=10,pady=10)
        self.camNumStrVar = Tkinter.StringVar()
        self.camNumStrVar.set(self.settings.get('camNumStrVar') )
        camNumEntry = Tkinter.Entry(controls, textvariable=self.camNumStrVar, width=10)
        camNumEntry.pack(side=Tkinter.TOP,padx=10,pady=10)
        camNumEntry.bind('<Return>', self.change_view)

        makePanButton = Tkinter.Button(controls, text='Save Panorama', command=self.save_panorama)
        makePanButton.pack(side=Tkinter.TOP,padx=10,pady=10)

        state = Tkinter.NORMAL if self.settings.get('panorama_forward') else Tkinter.DISABLED
        state = Tkinter.NORMAL
        self.estVidButton = Tkinter.Button(controls, text='Estimate video motion', command=self.estimate_motion, state=state)
        self.estVidButton.pack(side=Tkinter.TOP,padx=10,pady=10)

        self.forwardStrVar = Tkinter.StringVar()
        cfor = str(self.settings.get('im_forward')) if self.settings.get('im_forward') else ''
        pfor = str(self.settings.get('panorama_forward')) if self.settings.get('panorama_forward') else ''
        self.forwardStrVar.set( cfor + ' ' + pfor )
        Tkinter.Label(controls, textvariable=self.forwardStrVar).pack(side=Tkinter.TOP,padx=10,pady=10)

        self.testButton = Tkinter.Button(controls, text='Test func', command=self.test)
        self.testButton.pack(side=Tkinter.TOP,padx=10,pady=10)


        controls.pack(side=Tkinter.LEFT)



    def create_image_canvas(self):
        self.canvas = Tkinter.Canvas(self, width=self.settings['maxWidth'], height=self.settings['maxHeight'])
        self.canvas.bind("<ButtonPress-1>", self.grab_pt) # DETERMINE NEW POINT OR GRAB EXISTING
        self.canvas.bind("<ButtonRelease-1>", self.drawOnCanvas) # FINALIZE BUTTON ACTION
        self.canvas.bind("<ButtonRelease-3>", self.drawOnCanvas)
        self.canvas.bind("<B1-Motion>", self.movePoint)

        self.canvas.bind_all("<MouseWheel>", self.rollWheel)

        self.canvas.pack(side=Tkinter.RIGHT, expand=Tkinter.YES, fill=Tkinter.BOTH)



    def change_mode(self):
        self.get_thumbs()
        self.refresh_display()

    def change_click_mode(self):
        if self.rb.get() == "Window Selection":
            print "Window Selection"
        if self.rb.get() == "Heading Selection":
            print "Heading Selection"
        if self.rb.get() == "Object Selection":
            print "Object Selection"
        if self.rb.get() == "Measure Distance":
            print "Measure Distance"
        if self.rb.get() == "Off":
            print "Off"

        self.refresh_display()

    def change_view(self, event):
        self.image_manager()
        self.get_thumbs()
        self.refresh_display()



    def resize(self, event):
        self.settings['maxWidth'] = event.width
        self.settings['maxHeight'] = event.height
        self.canvas.config(width = event.width, height = event.height)

        # REFIT IMAGES TO CANVAS AND RESET ANCHORING
        imlist = self.disp_images
        if self.mode.get() == self.modes[0]: # 2 camera mode
            for i, dimage in enumerate(imlist[:2]):
                if dimage:
                    dimage.set_fit((event.width/2, event.height ))
                else:
                    break
            if i == 1:
                imlist[1].anchor = (imlist[0].box_span()[0], 0)
        elif self.mode.get() == self.modes[1] : # Road View mode
            for i, dimage in enumerate(imlist[:3]):
                if dimage:
                    dimage.set_fit((event.width, event.height/3 ))
                else:
                    break
            if i == 2:
                imlist[1].anchor = (0,imlist[0].box_span()[1])
                imlist[2].anchor = (0,imlist[0].box_span()[1]*2)
        elif self.mode.get() == self.modes[2]: # 3 Cameras mode
            for i, dimage in enumerate(imlist[:3]):
                if dimage:
                    dimage.set_fit((event.width/3, event.height ))
                else:
                    break
            if i == 2:
                imlist[1].anchor = (imlist[0].box_span()[0], 0)
                imlist[2].anchor = (imlist[0].box_span()[0]*2, 0)

        self.refresh_display()



    def grab_pt(self, event):
        if event.widget == self.canvas:
            # GET ASSOCIATED IMAGE
            for imN, im in enumerate(self.disp_images):
                if im != None:
                    if im.point( (event.x, event.y) ):
                        break
            else:
                return # IF NO ASSOCIATED IMAGE IS FOUND

            if self.rb.get() == "Heading Selection":
                dpx, dpy = im.point( (event.x, event.y) )
                self.settings['im_forward'] = (im.ID % 10, dpx)
                self.settings['car_boundary'] = dpy
                self.print_settings( 'Settings after choose front' )
                self.locate_front_in_panorama()

#            elif self.rb.get() == "Window Selection":
#                points = self.settings['subwindows'][imN].T
#                dif = sqrt((points[0]-event.x)**2 + (points[1]-event.y)**2)
#                i = dif <


            else:
                print 'Drawing on image {0}.'.format(imN)
                refc = self.disp_points[imN]
                dpx, dpy = im.point( (event.x, event.y) )
                if len(refc) > 0:
                    dx = refc['x'] - dpx
                    dy = refc['y'] - dpy
                    dif = sqrt(dx**2 + dy**2)
                    i = dif < 10
                    selectedPT = where(i == True)
                    print 'grabbed', selectedPT[0]
                    if len(selectedPT[0]) > 0:
                        self.mouseDrag[1] = selectedPT[0][0]
                        self.mouseDrag[0] = True






    def rollWheel(self, event):
#        print event.state
        self.canvas.delete(Tkinter.ALL)
        # IF WHEEL TURNED, NOT HELD DOWN
        if event.state == 8 or event.state == 10: # 10 is with caps lock
            try:
                if event.delta > 0:
                    self.image_manager('next')
                elif event.delta < 0:
                    self.image_manager('prev')
            except Warning:
                return
        # IF WHEEL BUTTON DOWN AND TURNED
        if event.state == 520 or event.state == 522:
            n = self.camera()
            if event.delta > 0:
                self.camera( (n+1) % 5 )
            elif event.delta < 0:
                self.camera( (n+4) % 5 )

        self.get_thumbs()
        self.refresh_display()



    def refresh_display(self):
        #print 'Refreshing'
        self.refreshImage()
        self.display_mask()
#        if not polyObjs:
#            polyObjs.append( PO() )
#        polyObjs[polyRef].add_ID( frameID(), filename(frameID()) )
#        polyObjs[polyRef].add_ID( frameID('R'), filename(frameID('R')) )
        self.get_drawing()
        self.refreshPolygon()
        self.refreshText()
#        self.showSIFTvectors()
        if self.FLOWit.get():
            self.showFLOW()

    def display_mask(self):
        if self.rb.get() == "Window Selection":
            if not self.settings.get('subwindows'):
                w,h = self.disp_images[0].size
                self.settings['subwindows'] = \
                    [array([(0,int(h*.3)),(0,int(h*.6)),(w,int(h*.6)),(w,int(h*.3))])
                        for i in range(5)]

            mask = Image.new('RGBA', [int(each) for each in self.geometry().split('+')[0].split('x')])

            alpha = Image.new('L', mask.size, 100)
            draw_alpha = ImageDraw.Draw(alpha)
            for dimage in self.disp_images:
                if dimage == None:
                    break
                cam = dimage.ID % 10
                draw_alpha.polygon([dimage.to_disp_pt(xy) for xy in self.settings['subwindows'][cam]],
                                    fill=0)
            mask.putalpha( alpha )
            self.mask = ImageTk.PhotoImage( mask )
            self.canvas.create_image((0,0), image=self.mask, anchor=Tkinter.NW, tags='image' )
        elif self.rb.get() == "Heading Selection":
            mask = Image.new('RGBA', [int(each) for each in self.geometry().split('+')[0].split('x')])

            alpha = Image.new('L', mask.size, 100)
            draw_alpha = ImageDraw.Draw(alpha)
            for dimage in self.disp_images:
                if dimage == None:
                    break
                cam = dimage.ID % 10
                if self.settings.get('im_forward'):
                    fcam, xpos = self.settings.get('im_forward')
                    if cam == fcam:
                        draw_alpha.polygon([dimage.to_disp_pt((xpos-10,0)),
                                            dimage.to_disp_pt((xpos-10,dimage.size[1])),
                                            dimage.to_disp_pt((xpos+10,dimage.size[1])),
                                            dimage.to_disp_pt((xpos+10,0))],
                                            fill=0)
            mask.putalpha( alpha )
            self.mask = ImageTk.PhotoImage( mask )
            self.canvas.create_image((0,0), image=self.mask, anchor=Tkinter.NW, tags='image' )


#    def animate_box(self):
#        if self.disp_images[0]:
#            im = self.disp_images[0]
#            trantime = 80
#            for i in xrange(trantime):
#                polyshape = [(520, 770), (587, 751), (610, 1000), (537, 964)]
#                polyshape2 = [[ 588,  751],[ 988,  732],[ 999,  910],[ 611,  1000]]
#
#                polydest = [(300, 700), (700, 600), (746, 1200), (340, 1180)]
##                polydest = [(520-i, 770-i), (587+i, 751-i), (610+i, 1000+i), (537-i, 964+i)]
#                polydest = [(296, 660), (714, 591), (742, 1221), (344, 1119)]
#                polydest2 = [[714, 591],[1027, 674],[1032, 938],[742, 1221]]
#
#                ptrans = (float(i)/trantime)*array(polydest)+(trantime-float(i))/trantime*array(polyshape)
#                ptrans = [tuple(s) for s in ptrans]
#                ptrans2 = (float(i)/trantime)*array(polydest2)+(trantime-float(i))/trantime*array(polyshape2)
#                ptrans2 = [tuple(s) for s in ptrans2]
#
#                self.texture = self.disp_images[0].get_texture(polyshape, ptrans)
#                self.texture2 = self.disp_images[0].get_texture(polyshape2, ptrans2)
#
#                self.canvas.delete('texture')
#                self.canvas.create_image((0,0), image=self.texture, anchor=Tkinter.NW, tags='texture')
#                self.canvas.create_image((0,0), image=self.texture2, anchor=Tkinter.NW, tags='texture')
#                self.update()



    def refreshImage(self):
#        try:
            mode = self.mode.get()
            self.canvas.delete('image')
            if mode == '2 Cameras':
                nImage = 2
            elif mode == 'Road View':
                nImage = 3
            elif mode == '3 Cameras':
                nImage = 3
            else: return

            for dimage in self.disp_images[:nImage]:
                if dimage:
                    imref = dimage.image()
                    self.canvas.create_image(dimage.anchor, image=imref, anchor=Tkinter.NW, tags='image' )
#        except Tkinter.TclError:
#            print 'TclError caught'



    def movePoint(self, event):
        if self.mouseDrag[1] >= 0:
            print event.x
            if event.widget == self.canvas:
                # GET ASSOCIATED IMAGE
                for imN, im in enumerate(self.disp_images):
                    if not im == None:
                        if im.point( (event.x, event.y) ):
                            break
                else:
                    return # IF NO ASSOCIATED IMAGE IS FOUND
                print 'Drawing on image {0}.'.format(imN)

                refc = self.disp_points[imN]
                refc['x'][self.mouseDrag[1]], refc['y'][self.mouseDrag[1]] = im.point( (event.x, event.y) )
                print refc[['x','y']][self.mouseDrag[1]], self.disp_points[imN][['x','y']][self.mouseDrag[1]]
        self.mouseDrag[0] = True
        self.refreshPolygon()




    def get_drawing(self):
        for imN, im in enumerate( self.disp_images ):
            if im == None:
                break

            self.disp_lines[imN] = []
            try:
                for line in self.settings['polyObjs'][self.polyRef].get_LNlist( im.ID ):
                    self.disp_lines[imN].append(line)
                self.disp_points[imN] = self.settings['polyObjs'][self.polyRef].get_PTarray( im.ID )
            except IndexError:
                print 'GET_DRAWING: IndexError'




    def refreshPolygon(self):
        self.canvas.delete('points','lines')


        if self.rb.get() == "Window Selection":
            for dimage in self.disp_images:
                if dimage == None:
                    break
                cam = dimage.ID % 10
                dpts = [dimage.to_disp_pt(xy)
                        for xy in self.settings['subwindows'][cam]]
                dpts += dpts[:1]
                for i in range(len(dpts)-1):
                    self.canvas.create_line( [dpts[i], dpts[i+1]],
                                            tags='lines',  fill="yellow" )
        if self.rb.get() == "Heading Selection":
            for dimage in self.disp_images:
                if dimage == None:
                    break
                retval = self.settings.get('im_forward')
                if retval != None:
                    fcam, xpt = retval
                    print fcam, xpt
                    ypt = dimage.size[1]
                    print ypt
                    if dimage.ID % 10 == fcam:
                        self.canvas.create_line( [dimage.to_disp_pt((xpt,0)),
                                                  dimage.to_disp_pt((xpt,ypt))],
                                                tags='lines',  fill="yellow" )

        def drawlines(canv, points, lines, d_im):
            pr = 2  # POINT RADIUS FOR DRAWING DOTS
            for pt in points:
                px, py = d_im.to_disp_pt( pt )
                canv.create_oval( [px-pr,py-pr,px+pr,py+pr],
                                  outline='yellow', fill="yellow",
                                  tags='points', activefill='blue')
            for pt0i, pt1i in lines:
                px0, py0 = d_im.to_disp_pt( points[['x','y']][pt0i] )
                px1, py1 = d_im.to_disp_pt( points[['x','y']][pt1i] )
                canv.create_line( [px0, py0, px1, py1],
                                  tags='lines',  fill="yellow" )

        if self.settings['polyObjs']:
            for imN, im in enumerate(self.disp_images):
                if im == None:
                    break
                drawlines(self.canvas, self.disp_points[imN], self.disp_lines[imN], im )

    def showFLOW(self):

        im = self.disp_images[0]
#        if not self.STTracking:
        width, height = self.old_image.size
        self.STTracking = ShiTomasiTracking( height, width )
        vectors = self.STTracking.getVectors(self.old_image, self.new_image )
#        print vectors
        for pt in vectors:
            x0, y0 = pt[0:2]
            x1, y1 = pt[2:4]
            self.canvas.create_line( [x0,y0,x1,y1], fill="yellow")


    #-----SIFT related methods-----
    def showSIFTvectors(self):
        im = self.disp_images[0]
        kQian = SIFT.read_image_key( filename(self.frame()+1, self.camera()) ) # Qian = Forward
        kCurr = SIFT.read_image_key( filename(self.frame(), self.camera()) )
#        kBack = SIFT.read_image_key( filename(self.frame()-1, self.camera()) )
#        kBackback = SIFT.read_image_key( filename(self.frame()-2, self.camera()) )
        if kCurr != None:
            for pt in kCurr:
    #            wc.create_text((sdown(pt['x']),sdown(pt['y'])), text='.', anchor=NW, fill="yellow")
                px, py = im.to_disp_pt( (pt['x'], pt['y']) )
                pr = 1
                self.canvas.create_oval( [px-pr,py-pr,px+pr,py+pr], outline='magenta', fill="red" )
        t1 = time.time()
#        if kCurr != None and kQian != None:
#            vCurr = SIFT.match_pairs(kCurr, kQian, threshold=0.6 )
#            print 'threshold=0.6 fast', len(vCurr), 'matches'
#            for pt in vCurr:
#                x0, y0 = im.to_disp_pt( pt[0:2] )
#                x1, y1 = im.to_disp_pt( pt[2:4] )
#                self.canvas.create_line( [x0,y0,x1,y1], fill="yellow")
#        print 'Time for fast:', time.time() - t1
    #    t1 = time.time()
    #    if kCurr != None and kBackback != None:
    #        vCurr = SIFT.match_pairs(kCurr, kBackback, threshold=0.6)
    #        print 'threshold=0.6 fast', len(vCurr), 'matches'
    #        for pt in vCurr:
    #            wc.create_line( sdown(list(pt[0:4])), fill="magenta")
    #    print 'Time for fast:', time.time() - t1
    #    t1 = time.time()
    #    if kCurr != None and kBack != None:
    #        vCurr = SIFT.match_pairs(kCurr, kBack, threshold=0.6)
    #        print 'threshold=0.6 fast', len(vCurr), 'matches'
    #        for pt in vCurr:
    #            wc.create_line( sdown(list(pt[0:4])), fill="cyan")
    #    print 'Time for fast:', time.time() - t1


    def locate_front_in_panorama(self):
        pan_fname = self.PGRstream.save_panorama()
        im = SIFT.get_image( pan_fname )
        key_fname = SIFT.create_image_key( im )
        pano_keys = SIFT.read_image_key( key_fname, delete=True )

        imID, xpixel = self.settings['im_forward']
        xpixel = int(xpixel)
        for dim in self.disp_images:
            if dim != None and dim.ID % 10 == imID:
                w,h = dim.im.size
                im_keys = SIFT_SfM.PIL2keys( dim.im.convert('L').crop(
                                                    (xpixel-50,0,xpixel+50,h)) )

        print len(pano_keys), len(im_keys)
        matches = SIFT_SfM.match_pairs(im_keys, pano_keys)

        closest = pano_keys[matches[1]]
#        second_closest = None
#        for each in matches:
#            if abs(xpixel - each[0]) < abs(xpixel - closest[0]):
#                second_closest = closest
#                closest = each
#        print ''
#        print xpixel, closest, second_closest
        m,s = mean(closest['x']), std(closest['x'])
        self.settings['panorama_forward'] = mean(closest[((closest['x'] < m+s) & (closest['x'] > m-s))]['x'])
#        self.settings['panorama_forward'] = closest[2]
        self.forwardStrVar.set( str(self.settings.get('im_forward')) +
                                ' ' + str(self.settings.get('panorama_forward')))
#        self.pickFront.set(False)
        self.estVidButton['state'] = Tkinter.NORMAL

        # SHOW OFFSET IMAGE FOR DEBUGGING (SET TRUE)
        if False:
            draw = ImageDraw.Draw(im)
            draw.line( [(closest[2],0), (closest[2],h)] )
            draw.line( [(second_closest[2],20), (second_closest[2],h-20)] )
            draw.rectangle( [closest[2:4], second_closest[2:4]] )
            im = ImageChops.offset(im, int(im.size[0]/2 - closest[2]), 0)
            im.show()
        self.refresh_display()

    def estimate_motion(self):
        print os.getcwd()

        rangestring = askstring('Calculate Motion', 'Enter Range')
        rangestring = rangestring.split()
        if len(rangestring) == 1:
            rangestring = rangestring[0].split('-,.')
        start, stopat = [int(rs) for rs in rangestring]

        if self.settings.get('translation') == None:
            self.settings['translation'] = [None]*self.PGRstream.getNumberOfFrames()

        translation = self.settings['translation']

        arr_len = self.PGRstream.getNumberOfFrames()
        # y-AXIS SEARCH SPACE LOWER BOUND (ABOVE CAR)
        yLB = self.settings.get('car_boundary') if self.settings.get('car_boundary') else None
        # x-AXIS CENTERED WITH FRONT OF VEHICLE (camera, pixel)
        xC = self.settings.get('im_forward') if self.settings.get('im_forward') else None
        if not yLB or not xC:
            return
        xpixel = int(xC[1])


        SfM = Ladybug_SfM(forward_cam=xC[0])

        # LOAD FIRST FRAME
        prev_im = [self.PGRstream.image(i).convert('L') for i in range(5)]

        # SET REGION OF INTEREST (CROPPING WINDOW)
        w,h = prev_im[0].size
        crop = 200, 700, w-200, int(yLB)
#        crop_w = crop[2] - crop[0]
#        crop_h = crop[3] - crop[1]
#        print crop_w, crop_h

        rectifyPixel = self.PGRstream.rectifyPixel

        for frameN in xrange(start, stopat ):
            # LOAD NEXT FRAME SET
            self.image_manager(frameN)

            # REFRESH DISPLAY
            self.get_thumbs()
            self.refresh_display()

            # CONVERT IMAGES FOR SIFT PROCESSING
            print 'Processing Frame', frameN
            image_keys = []
            for i in range(5):
                crop = self.settings['subwindows'][i]
                cropsquare = (min(crop[:,0]),min(crop[:,1]),
                              max(crop[:,0]),max(crop[:,1]))
                image = self.PGRstream.image( i ).convert('L')
                # GET KEYS FOR CROPPED IMAGES
                image_key = SIFT.PIL2keys( image.crop(cropsquare) )
                # CORRECT TO PRE-CROP POSITIONS
                image_key['x'] += cropsquare[0]
                image_key['y'] += cropsquare[1]
                # ANGLED CROPPING
                L1 = cross(r_[crop[0],1],r_[crop[3],1]).astype(float)
                ymin = (-L1[0]/L1[1])*image_key['x'] - L1[2]/L1[1]
                L2 = cross(r_[crop[1],1],r_[crop[2],1]).astype(float)
                ymax = (-L2[0]/L2[1])*image_key['x'] - L2[2]/L2[1]
                incrop = (image_key['y'] > ymin) & (image_key['y'] < ymax)
                image_key = image_key[incrop]
                # RECTIFY POSITIONS USING LADYBUG API
                XY = rectifyPixel( i, image_key['x'], image_key['y'] )
                image_key['x'], image_key['y'] = XY
                image_keys.append(image_key)

            Tr_code = SfM(self.log['seqid'][frameN], image_keys)
            print repr( Tr_code )
            if Tr_code != None:
                translation[frameN-1], translation[frameN] = Tr_code
        print 'Translation', start, 'to', stopat
        print repr(translation[start:stopat])



    def estimate_motion_2(self):
        '''For testing trifocal matrix method'''
        print os.getcwd()

        rangestring = askstring('Calculate Motion', 'Enter Range')
        rangestring = rangestring.split()
        if len(rangestring) == 1:
            rangestring = rangestring[0].split('-,.')
        start, stopat = [int(rs) for rs in rangestring]

        if self.settings.get('translation') == None:
            self.settings['translation'] = [None]*self.PGRstream.getNumberOfFrames()

        translation = self.settings['translation']

        arr_len = self.PGRstream.getNumberOfFrames()
        # y-AXIS SEARCH SPACE LOWER BOUND (ABOVE CAR)
        yLB = self.settings.get('car_boundary') if self.settings.get('car_boundary') else None
        # x-AXIS CENTERED WITH FRONT OF VEHICLE (camera, pixel)
        xC = self.settings.get('im_forward') if self.settings.get('im_forward') else None
        if not yLB or not xC:
            return
        xpixel = int(xC[1])


        SfM = Ladybug_SfM(forward_cam=xC[0])

        # LOAD FIRST FRAME
        prev_im = [self.PGRstream.image(i).convert('L') for i in range(5)]

        # SET REGION OF INTEREST (CROPPING WINDOW)
        w,h = prev_im[0].size
        crop = 200, 700, w-200, int(yLB)
#        crop_w = crop[2] - crop[0]
#        crop_h = crop[3] - crop[1]
#        print crop_w, crop_h

        rectifyPixel = self.PGRstream.rectifyPixel

        for frameN in xrange(start, stopat ):
            # LOAD NEXT FRAME SET
            self.image_manager(frameN)

            # REFRESH DISPLAY
            self.get_thumbs()
            self.refresh_display()

            # CONVERT IMAGES FOR SIFT PROCESSING
            print 'Processing Frame', frameN
            image_keys = []
            for i in range(5):
                crop = self.settings['subwindows'][i]
                cropsquare = (min(crop[:,0]),min(crop[:,1]),
                              max(crop[:,0]),max(crop[:,1]))
                image = self.PGRstream.image( i ).convert('L')
                # GET KEYS FOR CROPPED IMAGES
                image_key = SIFT.PIL2keys( image.crop(cropsquare) )
                # CORRECT TO PRE-CROP POSITIONS
                image_key['x'] += cropsquare[0]
                image_key['y'] += cropsquare[1]
                # ANGLED CROPPING
                L1 = cross(r_[crop[0],1],r_[crop[3],1]).astype(float)
                ymin = (-L1[0]/L1[1])*image_key['x'] - L1[2]/L1[1]
                L2 = cross(r_[crop[1],1],r_[crop[2],1]).astype(float)
                ymax = (-L2[0]/L2[1])*image_key['x'] - L2[2]/L2[1]
                incrop = (image_key['y'] > ymin) & (image_key['y'] < ymax)
                image_key = image_key[incrop]
                # RECTIFY POSITIONS USING LADYBUG API
                XY = rectifyPixel( i, image_key['x'], image_key['y'] )
                image_key['x'], image_key['y'] = XY
                image_keys.append(image_key)







#    def estimate_motion_old(self):
#        '''Processes all images in stream and finds relative movement between
#        frames.
#
#        @PRECONDITION: Run locate_front_in_panorama() first
#        '''
##        self.PGRstream.testerror()
##        return
#
#        print os.getcwd()
#
#
#        arr_len = self.PGRstream.getNumberOfFrames()
#        # y-AXIS SEARCH SPACE LOWER BOUND (ABOVE CAR)
#        yLB = self.settings.get('car_boundary') if self.settings.get('car_boundary') else None
#        # x-AXIS CENTERED WITH FRONT OF VEHICLE (camera, pixel)
#        xC = self.settings.get('im_forward') if self.settings.get('im_forward') else None
#        if not yLB or not xC:
#            return
#        xpixel = int(xC[1])
#
#        # LOAD FIRST FRAME
#        self.image_manager(0)
#        prev_im = self.PGRstream.image(xC[0]).convert('L')
#
#        # SET REGION OF INTEREST (CROPPING WINDOW)
#        w,h = prev_im.size
#        wspan = int(min( (abs(xC[1]-0), abs(w-xC[1])) ))
#        crop = (int(xC[1]-wspan), int(h*.48), int(xC[1]+wspan), int(yLB))
#        crop_w = crop[2] - crop[0]
#        crop_h = crop[3] - crop[1]
#        print crop_w, crop_h
#
#        # SHOW IMAGE FOR DEBUGGING
#        if False:
#            draw = ImageDraw.Draw(prev_im)
#            draw.rectangle( crop )
#            prev_im.show()
#
#        # LOOP THROUGH ALL IMAGES AND GATHER DATA
#        dy_est = zeros( arr_len )
#        vpy = zeros( arr_len )
#        vpx = zeros( arr_len )
#        horizon_est = zeros( arr_len )
##        vanishx_est = zeros( arr_len )
#        bear_est = zeros( arr_len )
#        dist_est = zeros( arr_len )
##        qual_est = zeros( arr_len, bool )
#        print '0',
#        prev_im_keys = SIFT.PIL2keys( prev_im.crop(crop) )
##        for i in xrange( 1, arr_len ):
#
#
#        rectifyPixel = self.PGRstream.rectifyPixel
#
#        stopat = 100
#        for frameN in xrange( 1, stopat ):
#            self.image_manager(frameN)
#            self.get_thumbs()
#            self.refresh_display()
#
#            next_im = self.PGRstream.image( xC[0] ).convert('L')
#
#            # GET KEYS FOR CROPPED IMAGES
#            print frameN,
#            next_im_keys = SIFT.PIL2keys( next_im.crop(crop) )
#
#            # FIND MATCHES
#            matches = SIFT.match_pairs( prev_im_keys, next_im_keys )
##            dtype = [('x1',float),('y1',float),('x2',float),('y2',float),('s',float),('o',float)]
##            matches = array(matches, dtype=dtype)
#
#            # CONVERT TO ARRAY AND ADD VIEWS
#            matches = array([array(tup) for tup in matches])
#            x1 = matches[:,0] # source (image1)
#            y1 = matches[:,1]
#            x2 = matches[:,2] # destination (image2)
#            y2 = matches[:,3]
#
#
#            # SAVE NEW IMAGE KEYS TO OLD REFERENCE, READY FOR NEXT LOOP
#            prev_im_keys = next_im_keys
#
#
#            # CONVERT TO RECTIFIED IMAGE COORDINATES
##            matches['x1'] += crop[0]
##            matches['y1'] += crop[1]
##            matches['x2'] += crop[0]
##            matches['y2'] += crop[1]
#            x1 += crop[0]
#            y1 += crop[1]
#            x2 += crop[0]
#            y2 += crop[1]
#
#            # DISPLAY THE UNRECTIFIED FLOW VECTORS
#            for each in matches:
#                p1,p2 = self.disp_images[0].to_disp_pt( [each[0],each[1]] )
#                p3,p4 = self.disp_images[0].to_disp_pt( [each[2],each[3]] )
#                self.canvas.create_line( [p1,p2,p3,p4],
#                                  tags='lines',  fill="yellow" )
#
##            matches['x1'], matches['y1'] = rectifyPixel(xC[0], matches['x1'], matches['y1'])
##            matches['x2'], matches['y2'] = rectifyPixel(xC[0], matches['x2'], matches['y2'])
##            crx, cry = rectifyPixel(xC[0], r_[crop[0],crop[2]], r_[crop[1],crop[3]] )
#            x1[:], y1[:] = rectifyPixel(xC[0], x1, y1)
#            x2[:], y2[:] = rectifyPixel(xC[0], x2, y2)
#            crx, cry = rectifyPixel(xC[0], r_[crop[0],crop[2]], r_[crop[1],crop[3]] )
#
##            matches['x1'], matches['y1'] = self.PGRstream.unrectifyPixel(xC[0],
##                                    matches['x1'], matches['y1'])
##            matches['x2'], matches['y2'] = self.PGRstream.unrectifyPixel(xC[0],
##                                    matches['x2'], matches['y2'])
#
#            # DISPLAY THE RECTIFIED FLOW VECTORS
##            for each in matches:
##                p1,p2 = self.PGRstream.unrectifyPixel(xC[0],p1,p2)
##                p3,p4 = self.PGRstream.unrectifyPixel(xC[0],p3,p4)
##                p1,p2 = self.disp_images[0].to_disp_pt( [each['x1'],each['y1']] )
##                p3,p4 = self.disp_images[0].to_disp_pt( [each['x2'],each['y2']] )
##                self.canvas.create_line( [p1,p2,p3,p4],
##                                  tags='lines',  fill="yellow" )
#            self.canvas.update()
#
#            # FIND VERTICAL SHIFT (STABILIZE CAMERA)
#            for s in xrange(cry[0], cry[0] + crop_h/2):
#                horizon_matches = where(y1 < s)[0]
#                if len(horizon_matches) > 30:
#                    break
#            # REMOVE OUTLIERS
##            dy = matches[horizon_matches]['y2'] - matches[horizon_matches]['y1']
##            m,s = mean(dy), std(dy)
##            dy = dy[where(dy > m-s*2)]
##            dy = dy[where(dy < m+s*2)]
#            dy = y2[horizon_matches] - y1[horizon_matches]
#            m,s = mean(dy), std(dy)
#            dy = dy[where(dy > m-s*2)]
#            dy = dy[where(dy < m+s*2)]
#
#
#
#            # STORE MEAN
#            dy_est[frameN-1] = mean(dy)
#            print 'dy-shift', mean(dy)
#
#
#
#            # FIND APPROXIMATED DISTANCE MOVED
#            for s in xrange(cry[1], cry[1] - crop_h/2, -1):
#                bottom_matches = where(y1 > s)[0]
#                if len(bottom_matches) > 100:
#                    break
#
#
##            print 'array', random.sample(range(len(bottom_matches)), 8), len(bottom_matches)
##
##            s = cv2.cv.CreateMat(8,2,cv2.CV_32F)
##            d = cv2.cv.CreateMat(8,2,cv2.CV_32F)
##            p = cv2.cv.CreateMat(3,3,cv2.CV_32F)
##            for indm, match in enumerate(random.sample(range(len(bottom_matches)), 8)):
##                s[indm,0] = matches[bottom_matches]['x1'][match]
##                s[indm,1] = matches[bottom_matches]['y1'][match]
##
##                d[indm,0] = matches[bottom_matches]['x2'][match]
##                d[indm,1] = matches[bottom_matches]['y2'][match]
##            cv2.cv.FindFundamentalMat(s,d,p,cv2.cv.CV_FM_RANSAC)
#
#
#            x1bot = matches[bottom_matches][:,0] # source (image1)
#            y1bot = matches[bottom_matches][:,1]
#            x2bot = matches[bottom_matches][:,2] # destination (image2)
#            y2bot = matches[bottom_matches][:,3]
#            botmatches = matches[bottom_matches]
#
#            # GET HOMOGRAPHY MATRIX (cv)
#            s = cv2.cv.CreateMat(len(bottom_matches),2,cv2.CV_32F)
#            d = cv2.cv.CreateMat(len(bottom_matches),2,cv2.CV_32F)
#            for match in range(len(bottom_matches)):
#                s[match,0] = x1bot[match]
#                s[match,1] = y1bot[match]
#
#                d[match,0] = x2bot[match]
#                d[match,1] = y2bot[match]
#            H = cv2.cv.CreateMat(3,3,cv2.CV_32F) # BUFFER
#            cv2.cv.FindHomography(s,d,H,cv2.cv.CV_RANSAC)
#
#
#            # GET HOMOGRAPHY MATRIX (cv2)
#            # CONVERT STRUCTURED ARRAY TO SOURCE AND DESTINATION ARRAYS
##            source = hstack((atleast_2d(botmatches['x1']).T,atleast_2d(botmatches['y1']).T))
##            destin = array([array([a,b]) for a,b in botmatches[['x2','y2']]])
##            HH, mask = cv2.findHomography(source, destin, cv2.RANSAC)
#            source = matches[bottom_matches][:,0:2].copy()
#            destin = matches[bottom_matches][:,2:4].copy()
#            HH, mask = cv2.findHomography(source, destin, cv2.RANSAC)
#
#
#
##            print H
##            HH = zeros((H.rows,H.cols))
##            for ii in range(H.rows):
##                for j in range(H.cols):
##                    HH[ii,j] = H[ii,j]
##            print xpixel, HH
#            s_pt = array([[xpixel],[1400],[1]])
##            print HH, s_pt, dot(HH,s_pt)
#            d_pt = dot(HH,s_pt)
##            print 'x'
#            moved = d_pt
##            print 'homopoint', moved
##            for thistest in range(5):
##                tmatch = matches[bottom_matches][thistest]
##                print 'match test', tmatch
##                s_pt = array([[tmatch[0]],[tmatch[1]],[1]])
##                print 'source pt', s_pt
##                d_pt = dot(HH, s_pt )
##                print 'dest pt', d_pt/d_pt[2,0]
##                print ''
##            return
#            for ii in xrange(300, 900, 20):
#                for jj in xrange(800, 1300, 20):
#                    s_pt = array([[ii],[jj],[1]])
#                    d_pt = dot(HH,s_pt)
#                    s_pt = s_pt.flat[:2]
#                    d_pt = (d_pt/float(d_pt[2])).flat[:2]
#                    s_pt = self.PGRstream.unrectifyPixel(xC[0], s_pt[0], s_pt[1])
#                    d_pt = self.PGRstream.unrectifyPixel(xC[0], d_pt[0], d_pt[1])
#                    s = self.disp_images[0].to_disp_pt( s_pt )
#                    d = self.disp_images[0].to_disp_pt( d_pt )
#                    self.canvas.create_line( [s[0],s[1],d[0],d[1]],
#                                            tags='lines',  fill="cyan" )
#
#
#
#
#
#
#            if True:
#                plt.quiver(x1,-y1,x2-x1,-y2-y1)
#                plt.quiver(x1bot,-y1bot,(x2bot-x1bot),-(y2bot-y1bot), color=(1,0,0))
#                plt.quiver(x1[horizon_matches],-y1[horizon_matches],0,-(y2[horizon_matches]-y1[horizon_matches]), color=(0,0,1))
##                points = []
#                for each in matches[bottom_matches]:
#                    dx = each[2]-each[0]
#                    dy = each[3]-each[1]
##                    xset = [each['x1']-10*dx, each['x1']+10*dx]
##                    yset = [-(each['y1']-10*dy), -(each['y1']+10*dy)]
#
##                    plt.plot(xset,yset)
#
#                # TODO: Augment the 2nd image points based on y-axis stabilization
#                X, Y, A = [], [], []
#                count = 0
#                while True:
#                    r1, r2 = random.sample(range(len(bottom_matches)), 2)
#                    l1 = matches[bottom_matches][r1]
#                    l2 = matches[bottom_matches][r2]
#                    retval = intersect_4pt([l1[0],l1[1],l1[2],l1[3],l2[0],l2[1],l2[2],l2[3]])
#                    if retval:
#                        X.append(retval[0])
#                        Y.append(-retval[1])
#                        A.append(retval[2])
#                    if len(A) >=20:
#                        print X
#                        break
#                    count += 1
#                    if count == 100:
#                        break
#                if X:
#                    inds = argsort(A)[::-1]
#                    Xsorted = take(X, inds)
#                    Ysorted = take(Y, inds)
#                    # REMOVE OUTLIERS
#                    inds = where(abs(Xsorted-mean(Xsorted)) < 2*std(Xsorted)) and where(abs(Ysorted-mean(Ysorted)) < 2*std(Ysorted))
#                    Xsorted = Xsorted[inds]
#                    Ysorted = Ysorted[inds]
#                    weights = range(len(Xsorted),0,-1)
#                    try:
#                        print 'mean', mean(Xsorted), mean(Ysorted)
#                        print 'average', average(Xsorted, weights=weights), average(Ysorted, weights=weights)
#                        horizon_est[frameN-1] = -average(Ysorted, weights=weights)
#                    except:
#                        continue
##                    vanishx_est[frameN-1] = average(Xsorted, weights=weights)
##                    plt.plot(X,Y,'+')
#                rx, ry = rectifyPixel(xC[0],[xpixel,crop[0],crop[2]], [horizon_est[frameN-1],crop[3],crop[3]])
#                vx, vy = self.disp_images[0].to_disp_pt([(rx[1]+rx[2])/2,ry[0]])
#                c0, c3 = self.disp_images[0].to_disp_pt([rx[1],ry[1]])
#                c2, c3 = self.disp_images[0].to_disp_pt([rx[2],ry[2]])
#
#                # DISPLAY THE SAMPLING REGION (TRAPEZOID OF GROUND IN FRONT OF VEHICLE)
##                self.canvas.create_line( [vx,vy,c0,c3],
##                              tags='lines',  fill="red" )
##                self.canvas.create_line( [vx,vy,c2,c3],
##                              tags='lines',  fill="red" )
##                self.canvas.create_line( [c0,c3,c2,c3],
##                              tags='lines',  fill="red" )
##                self.canvas.create_line( [vx-(vx-c0)/2,vy+(c3-vy)/2,vx+(c2-vx)/2,vy+(c3-vy)/2],
##                              tags='lines',  fill="red" )
#
#                self.canvas.update()
#
#                ncrop = [int(rx[1]),int(ry[0]+(ry[1]-ry[0])/2),int(rx[2]),int(ry[1])]
#                ttl = [int((rx[1]+rx[2])/2-((rx[1]+rx[2])/2-rx[1])/2-ncrop[0]),int(ry[0]+(ry[1]-ry[0])/2-ncrop[1])]
#                ttr = [int((rx[1]+rx[2])/2+(rx[2]-(rx[1]+rx[2])/2)/2-ncrop[0]),int(ry[0]+(ry[1]-ry[0])/2-ncrop[1])]
#                tbl = [int(rx[1]-ncrop[0]),int(ry[1]-ncrop[1])]
#                tbr = [int(rx[2]-ncrop[0]),int(ry[1]-ncrop[1])]
#                ww = int(rx[2]-rx[1])
#                ptl = [0,0]
##                savediff = [99999]*10
##                bestHH = 10
#                bestDW = ww
##                bestSTD = [99999]*10
##                bestLEN = 0
##                bestANG = 99999
#                sumarr = 99999
##                matches[bottom_matches] = sort(matches[bottom_matches])
##                print matches[bottom_matches][:20]
#                try:
#                    rands = random.sample(range(len(bottom_matches)), 50)
#                except:
#                    continue # PROCESS NEXT FRAME
#                pairs = zip(rands[:25],rands[25:])
##                plt.show()
#                hh = 4*(ncrop[3]-ncrop[1])
#                pbl = [0,hh]
#                pbr = [ww,hh]
#                for dw in xrange(ww-100,ww+100):
#                    '''Testing a range of transforms. Stretching the narrow
#                    trapazoid top for the best fit.
#                    '''
#                    ptr = [dw,0]
#                    transMat = get_transform_data([tbl,ttl,tbr,ttr,pbl,ptl,pbr,ptr])
#                    revtrans = get_transform_data([tbl,ttl,tbr,ttr,pbl,ptl,pbr,ptr][::-1])
#
#
#
##                    if hh == 500:
##                        plt.figure()
##                        for iii in xrange(0,ncrop[2]-ncrop[0],20):
##                            for jjj in xrange(0,ncrop[3]-ncrop[1],20):
##                                nx,ny = transform_pt([iii,jjj], revtrans)
##                                plt.plot([iii],[jjj],'+')
##                                plt.plot([nx],[ny],'o')
##                        plt.show()
##                    if dw in [ww-40,ww,ww+9]:
##                        plt.figure()
##                        for each in matches[bottom_matches]:
##                            ax,ay = transform_pt([each[0]-ncrop[0],each[1]-ncrop[1]], revtrans)
##                            bx,by = transform_pt([each[2]-ncrop[0],each[3]-ncrop[1]], revtrans)
##                            plt.plot([each[0]-ncrop[0],each[2]-ncrop[0]], [-each[1]--ncrop[1],-each[3]--ncrop[1]], 'r:')
##                            plt.plot([ax,bx], [-ay,-by], 'g')
##                        each1 = matches[bottom_matches][0]
##                        ax1,ay1 = transform_pt([each1[0]-ncrop[0],each1[1]-ncrop[1]], revtrans)
##                        bx1,by1 = transform_pt([each1[2]-ncrop[0],each1[3]-ncrop[1]], revtrans)
##                        plt.plot([each[0]-ncrop[0],each1[0]-ncrop[0]], [-each[1]--ncrop[1],-each1[1]--ncrop[1]], 'r')
##                        plt.plot([each[2]-ncrop[0],each1[2]-ncrop[0]], [-each[3]--ncrop[1],-each1[3]--ncrop[1]], 'r')
##                        plt.plot([ax,ax1], [-ay,-ay1], 'g', lw=3)
##                        plt.plot([bx1,bx], [-by1,-by], 'g', lw=3)
##
##                        for ii in xrange(300, 900, 20):
##                            for jj in xrange(800, 1000, 20):
##                                s_pt = array([[ii],[jj],[1]])
##                                d_pt = dot(HH,s_pt)
##                                s_pt = s_pt.flat[:2]
##                                d_pt = (d_pt/float(d_pt[2])).flat[:2]
##                                s_pt = self.PGRstream.unrectifyPixel(xC[0], s_pt[0], s_pt[1])
##                                d_pt = self.PGRstream.unrectifyPixel(xC[0], d_pt[0], d_pt[1])
##                                s = transform_pt( [s_pt[0]-ncrop[0],s_pt[1]-ncrop[1]], revtrans)
##                                d = transform_pt( [d_pt[0]-ncrop[0],d_pt[1]-ncrop[1]], revtrans)
##                                plt.plot( [s[0],d[0]],[-s[1],-d[1]], 'c' )
##                        plt.show()
#
#                    difflist = []
#                    angles = []
##                    midlen = []
##                    midshift = []
#
##                    plt.figure()
#                    for each in pairs:
#                        # REMEMBER TO ADJUST FOR CROPPING
#                        l1 = matches[bottom_matches][each[0]]
#                        l2 = matches[bottom_matches][each[1]]
##                        if l1[1]-ncrop[1] < 0:
##                            print 'skipping'
##                            continue
##                        if l2[1]-ncrop[1] < 0:
##                            print 'skipping'
##                            continue
##                        print '0,0', transform_pt([0,0], transMat)
##                        print '5,5', transform_pt([5,5], transMat)
##                        print '10,10', transform_pt([10,10], transMat)
##                        print '15,15', transform_pt([15,15], transMat)
##                        print '20,20', transform_pt([20,20], transMat)
#                        i1p1 = [l1[0]-ncrop[0],l1[1]-ncrop[1]]
#                        i1p2 = [l2[0]-ncrop[0],l2[1]-ncrop[1]]
#                        i2p1 = [l1[2]-ncrop[0],l1[3]-ncrop[1]]
#                        i2p2 = [l2[2]-ncrop[0],l2[3]-ncrop[1]]
##                        plt.plot([i1p1[0],i1p2[0]], [i1p1[1],i1p2[1]], 'k-.')
##                        plt.plot([i2p1[0],i2p2[0]], [i2p1[1],i2p2[1]], 'k')
#                        i1p1 = transform_pt(i1p1, revtrans)
#                        i1p2 = transform_pt(i1p2, revtrans)
#                        i2p1 = transform_pt(i2p1, revtrans)
#                        i2p2 = transform_pt(i2p2, revtrans)
##                        plt.plot([i1p1[0],i2p1[0]], [i1p1[1],i2p1[1]], 'g')
##                        plt.plot([i1p2[0],i2p2[0]], [i1p2[1],i2p2[1]], 'g')
##                        plt.plot([i1p1[0],i1p2[0]], [i1p1[1],i1p2[1]], 'k')
##                        plt.plot([i2p1[0],i2p2[0]], [i2p1[1],i2p2[1]], 'r')
#                        dist1 = sqrt((i1p2[0]-i1p1[0])**2 + (i1p2[1]-i1p1[1])**2)
#                        dist2 = sqrt((i2p2[0]-i2p1[0])**2 + (i2p2[1]-i2p1[1])**2)
##                        print dist1, dist2
##                        print dw, abs(dist2-dist1)
#                        difflist.append( abs(dist2-dist1) )
##                        if diffim <= savediff:
##                            savediff = diffim
##                            bestHH = hh
##                            print bestHH, diffim
#                        # FIND ANGLE CHANGE
#                        i1m = (i1p2[1]-i1p1[1])/(i1p2[0]-i1p1[0])
#                        i2m = (i2p2[1]-i2p1[1])/(i2p2[0]-i2p1[0])
#
#                        ang1 = arctan(i1m)
#                        ang2 = arctan(i2m)
#                        angles.append((ang1*180/pi-ang2*180/pi))
#
##                        # CREATE MIDPOINT VECTORS AND GET STATS
##                        # (m,b) => mx+b
##                        L1coefs = (i1m, i1p2[1]-i1m*i1p2[0])
##                        L2coefs = (i2m, i2p2[1]-i2m*i2p2[0])
##                        vtop = L1coefs[0]*vx+L1coefs[1]
##                        vbot = L2coefs[0]*vx+L2coefs[1]
#
#                        # FOCUS ON A STATIONARY POINT USING HOMOGRAPHY
#                        vpt = [[(rx[1]+rx[2])/2],[ry[1]],[1.]]
#                        vpt_dest = dot(HH,vpt)
##                        print vpt, vpt_dest
#                        vpt = [(rx[1]+rx[2])/2-ncrop[0], ry[1]-ncrop[1]]
#                        vpt_dest = [vpt_dest[0,0]-ncrop[0], vpt_dest[1,0]-ncrop[1]]
#                        vpt_t = transform_pt(vpt, revtrans)
#                        vpt_dest_t = transform_pt(vpt_dest, revtrans)
#
#
#
##                    plt.show()
#                    subsum = sum(array(difflist))
##                    stdevv = std(array(difflist))
#                    if subsum < sumarr:
#                        sumarr = subsum
##                        bestSTD = stdevv
#                        bestDW = dw
##                        bestLEN = mean(array(difflist))
##                        print 'internal check', len(difflist), sumarr, bestDW, bestSTD
##                        print 'Angle', angles
##                        outtest = vpt, vpt_dest, vpt_t, vpt_dest_t, 'dy', vpt_dest_t[1]-vpt_t[1], 'dx', vpt_dest_t[0]-vpt_t[0]
#                        vpy[frameN-1] = vpt_dest_t[1]-vpt_t[1]
#                        vpx[frameN-1] = vpt_dest_t[0]-vpt_t[0]
#                        angles = array(angles)
##                        anglesFiltered = mean(angles[where(abs(angles-mean(array(angles))) < 1*std(array(angles)))])
##                        bestANG = mean(array(angles)), std(array(angles)), anglesFiltered
#                ptr = [bestDW,0]
##                print 'initWidth', ww, 'best', bestDW, sumarr, 'mean', bestLEN
##                print 'Best Angle', bestANG
##                print outtest
##                plt.show()
#
#                if False:
#                    self.transim = self.PGRstream.image( xC[0] ).crop(ncrop)
#                    self.transim.show()
#                    self.transim2 = perspective_transform(self.transim,
#                                                        [tbl,ttl,tbr,ttr,pbl,ptl,pbr,ptr])
#                    self.transim2.show()
#
#
#
#
##            continue
#
#            dist_est[frameN-1] = moved[1,0]
#            bear_est[frameN-1] = moved[0,0]
#
#
#            # REMOVE OUTLIERS
#            dy = y2bot - y1bot
#            m,s = mean(dy), std(dy)
#            dy = dy[where(dy > m-s*2)]
#            dy = dy[where(dy < m+s*2)]
#
#            # STORE MEAN MINUS VERTICAL INSTABILITY
##            dist_est[frameN-1] = mean(dy) - dy_est[frameN-1]
#
#
#
#            # FIND APPROXIMATED ORIENTATION CHANGE
#            for s in xrange(cry[1], cry[1] - crop_h/2, -1):
#                lower_matches = where(y1 > s)[0]
#                if len(lower_matches) > 100:
#                    break
#            dx = x2[lower_matches] - x1[lower_matches]
#            xpos = x2[lower_matches]
##            dx = matches['x2'] - matches['x1']
##            xpos = matches['x2']
##            middx = interpolate.splev(array(int(wspan)),
##                                    interpolate.splrep(xpos, dx, s=0, k=2 ),
##                                    der=0)
#
#            (a,b) = polyfit(xpos,dx,1)
#            middx = a*int(wspan)+b
##            plt.plot(xpos,dx,'o', xpos,a*xpos+b,'-')
##            plt.show()
##            print (int(wspan), middx)
#            # STORE MEAN
#            print 'middx', -middx
#            bear_est[frameN-1] = -middx # NEGATIVE FOR VEHICLE ROTATION INSTEAD OF IMAGE DISPLACEMENT
#
#            if False:
#                plt.quiver(x1,-y1,x2-x1,-(y2-y1))
#                plt.show()
#                return
#
#            # STORE BEST DATA
#
##        print 'bear_est', bear_est
##        print vanishx_est[:stopat]
##        print horizon_est[:stopat]
##        print 'dy', dy_est[:stopat]
##        print 'dist', dist_est
##        print 'ddist', dist_est - dy_est
##        print 'number of matches for', frameN, len(matches)
##        print 'homo py', vpy[:stopat]
##        print 'homo px', vpx[:stopat]
#
#
#        with open('vis_dist2.txt', 'w') as wfile:
#            wfile.write('[')
#            for each in vpy:
#                wfile.write(str(each) + ',' )
#            wfile.write(']')
#            wfile.close()
#        with open('vis_bear2.txt', 'w') as wfile:
#            wfile.write('[')
#            for each in vpx:
#                wfile.write(str(each) + ',' )
#            wfile.write(']')
#            wfile.close()
#        with open('log_bear2.txt', 'w') as wfile:
#            wfile.write('[')
#            for each in db['bearing']:
#                wfile.write(str(each) + ',' )
#            wfile.write(']')
#            wfile.close()
#
#        # COMPARE GPS LOG DISTANCE WITH ESTIMATED RELATIVE DISTANCE
#        db = ladybug_calc_dist(self.log)
#        for each in zip(db['distance'], dist_est)[:40]:
#            # NO CORRELATION SO FAR
#            print each, ','
#
#
#        for each in zip(db['bearing'], bear_est)[:40]:
#            # CORRELATION FOUND
#            print each, ','
#
##        with open('log_dist.txt', 'w') as wfile:
##            wfile.write('[')
##            for each in db['distance']:
##                wfile.write(str(each) + ',' )
##            wfile.write(']')
##            wfile.close()


    #-----Ladybug stream accessing methods-----
    def open_PGR_stream(self):
        '''User selects *.PGR stream file.

        @TODO: Auto-load last session associated with the selected file. Will
        have to associate last session data with file name and add an option
        to start a new session.
        '''
        pgr_fname = str(askopenfilename(initialdir=os.path.split(self.settings['dir_stream'][0]), filetypes=[("ladybug stream files","*.pgr")]))
        self.settings['dir_stream'] = pgr_fname
        self.PGRstream = Ladybug3stream( self.settings['dir_stream'] )
        self.totalStrVar.set( self.PGRstream.getNumberOfFrames() )
        self.image_manager(0)
        self.get_thumbs()
        self.refresh_display()


    def close_PGR_stream(self):
        try:
            self.PGRstream.closeStream()
            self.disp_images = [None for i in xrange(6)]
        except (AttributeError, Warning):
            pass




    def load_last_session(self):
        '''Load last session settings.

        TODO: Save settings data structure to file on exit and load with this
        method.
        '''
        self.load_session(latest=True)


    def image_manager(self, arg=None):
        '''Manages the loading of 'next', 'prev', or frame index images.

        Pass an integer to load a particular image. This method calls on
        ladybug3stream.load to load frame image set from stream. This does not
        load a particular image.
        '''
        tmpNum = self.frame()
        if isinstance(arg, int):    tmpNum = arg
        elif arg == 'next':         tmpNum = tmpNum+1
        elif arg == 'prev':         tmpNum = tmpNum-1
        else:
            pass

        # TRY OPENING THE NEXT IMAGE SET
        try:
            do_sift = self.SIFTit.get()
            do_flow = self.FLOWit.get()
            successful = self.PGRstream.loadframe( tmpNum,
                                                  ('SIFT' if do_sift else ''),
                                                  FLOW = (self.camNumStrVar.get() if do_flow else None) )
            if not successful:
                print 'Error returned from PGRstream.load'
                return False
        except AttributeError:
            print AttributeError
            return False
        except AssertionError:
            # IGNORE OUT OF INDEX FRAME REQUESTS
            return

#        fdata, gpsdata = self.PGRstream.getFrameInfo()
#        print self.PGRstream.LadybugImage.uiCols, self.PGRstream.LadybugImage.uiRows
#        print fdata.time, fdata.lat
#        print fdata.seqid, gpsdata.bValidData, gpsdata.ucGGAHour, gpsdata.ucGGAMinute, gpsdata.ucGGASecond, gpsdata.wGGASubSecond, fdata.microsec, gpsdata.dGGALatitude

        # IF SUCCESSFUL THEN UPDATE GLOBAL IMAGE REFERENCE NUMBER
        self.frame( tmpNum )



    def get_thumbs(self):
        '''Get set of images from PGRstream based on GUI 'mode'.
        '''
        if self.disp_images[0] != None:
            self.old_image = self.disp_images[0].image(Tk=False)

        imlist = self.disp_images
        imlist[:] = [None for i in xrange(6)]
        try:
            test = self.settings['maxWidth']
            test = self.settings['maxHeight']
        except KeyError:
            self.settings['maxWidth'] = 1000
            self.settings['maxHeight'] = 800



        # 2 CAMERA MODE
        if self.mode.get() == '2 Cameras':
            for i in xrange(2):
                try:
                    imlist[i] = display_image( self.PGRstream.image( (self.camera()+i)%5 ), self.frame()*10+(self.camera()+i)%5,
                                               fit=(self.settings['maxWidth']/2,self.settings['maxHeight'] ) )
                except AttributeError:
                    return False
            # SET POSITIONING OF VIEWS
            imlist[1].anchor = (imlist[0].box_span()[0], 0)
        # 3 CAMERA ROAD VIEW MODE
        if self.mode.get() == 'Road View':
            for i in xrange(3):
                try:
                    imlist[i] = display_image( self.PGRstream.image( (self.camera()+i+4)%5 ),  self.frame()*10+(self.camera()+i+4)%5,
                                               fit=(self.settings['maxWidth'],self.settings['maxHeight']/3 ) )
                    size = imlist[i].size
                    imlist[i].set_box((0,int(size[1]*1/2),size[0],int(size[1]*3.2/4)))
                except AttributeError:
                    return False
            # SET POSITIONING OF VIEWS
            imlist[1].anchor = (0,imlist[0].box_span()[1])
            imlist[2].anchor = (0,imlist[0].box_span()[1]*2)
        # 3 CAMERA MODE
        if self.mode.get() == '3 Cameras':
            for i in xrange(3):
                try:
                    imlist[i] = display_image( self.PGRstream.image( (self.camera()+i+4)%5 ),  self.frame()*10+(self.camera()+i+4)%5,
                                               fit=(self.settings['maxWidth']/3,self.settings['maxHeight'] ) )
                except AttributeError:
                    return False
            # SET POSITIONING OF VIEWS
            imlist[1].anchor = (imlist[0].box_span()[0], 0)
            imlist[2].anchor = (imlist[0].box_span()[0]*2, 0)
        # 1 CAMERA MODE
        if self.mode.get() == '1 CAMERA':
            pass
        # 1 CAMERA 2 TIMES MODE
        if self.mode.get() == '1 CAMERA 2 TIMES':
            pass
        # 2 STREAM MODE
        if self.mode.get() == '2 STREAM':
            pass

        self.new_image = self.disp_images[0].image(Tk=False)

    def save_panorama(self):
        self.PGRstream.save_panorama(carfront=self.settings.get('panorama_forward') )


    def deriveCalibrationData(self):
        '''Run all calibration processes to get spatial data.

        '''
        log = False
        # CREATE THE NAME FOR THE FILE.
        gps_filename = '{0[0]}/Ladybug_GPS_log_{1}'.format(os.path.split(self.settings['dir_stream']), self.PGRstream.getNumberOfFrames())
        print gps_filename
        # CHECK IF FILE ALREADY EXISTS.
        if not os.path.exists( gps_filename + '.pkl'):
            # PROCESS ENTIRE VIDEO AND GET GPS DATA AS STRUCTURED ARRAY
            log = self.PGRstream.getVideoGPSlog()


            # SAVE ARRAY TO PICKLED FILE
            with open( gps_filename + '.pkl', 'w') as wfile:
                pickle.dump(log, wfile)
            wfile.close()
            # ALSO OUTPUT A CSV TEXT FILE
            with open( gps_filename + '.txt', 'w') as wfile:
                for each in log:
                    for name, val in zip(log.dtype.names, each):
                        wfile.write('{0}={1}, '.format(name, val).ljust(20))
                    wfile.write('\n')
            wfile.close()
        # IF FILE ALREADY EXISTS. LOAD IT.
        else:
#            with open('Ladybug_GPS_log_suhua1.pkl', 'r') as rfile:
#                log = pickle.load(rfile)
            with open( gps_filename + '.pkl', 'r') as rfile:
                log = pickle.load(rfile)


#        orilog = log.copy()
        ladybug_interp_data(log)
        db = ladybug_calc_dist(log)

        # TEST FOR GOING TO AND BACK FROM DISTANCE/BEARING
        clog = log.copy()
        clog['lat'] = 0
        clog['lon'] = 0
        clog['lat'][0] = log['lat'][0]
        clog['lon'][0] = log['lon'][0]
        for i in xrange(len(db) - 1):
            nextcoord = calc_latlon(clog['lat'][i],
                                    clog['lon'][i],
                                    db['distance'][i],
                                    db['bearing'][i] )
            clog['lat'][i+1], clog['lon'][i+1] = nextcoord

            print (log['lat'][i], clog['lat'][i]), (log['lon'][i], clog['lon'][i])


        nbound = where(abs(db['bearing']) < 90 )
        print 'greatest distance', max(db['distance'])
        gdd = where(log['valid'] == True)

        plt.plot(log['lon'][3418:3850],log['lat'][3418:3850])
        plt.plot(log['lon'][gdd],log['lat'][gdd], 'x')
#        plt.plot(log['lon'][nbound][3400:3900],log['lat'][nbound][3400:3900])
#        plt.plot(clog['lon'][3400:3900],clog['lat'][3400:3900])
#        x = db['distance'] * sin( db['bearing'] * pi/180 )
#        y = db['distance'] * cos( db['bearing'] * pi/180 )
#        plt.plot(cumsum(x),cumsum(y),'o')
        plt.show()

        self.log = log
        return log



    def endsession(self):
        self.save_session(latest=True)
        self.close_PGR_stream()
        self.quit()
    #-----End of ladybug methods


    def refreshText(self):
        for dimage in self.disp_images:
            if dimage:
                # IF TRANSFORMATION EXISTS FOR AN IMAGE THEN GIVE A GREEN LIGHT
#                key_fname = glob.glob('*' + filename( dimage.ID ) + '.key')
#                keylight = 'green' if key_fname else 'red'
                trans = self.settings.get('translation')
                keylight = 'green' if trans != None else 'red'
                if trans == None:
                    trans = '[Rx, Ry, Rz, Az, El, Sc]'
                else:
                    trans = trans[dimage.ID/10]

                self.canvas.create_oval( [dimage.anchor[0],dimage.anchor[1],10+dimage.anchor[0],10+dimage.anchor[1]],
                                          outline='black', fill=keylight,
                                          tags='keylight' )
                self.canvas.create_text([10+dimage.anchor[0],10+dimage.anchor[1]], text='{0:0>8} CAM{1}  Tr{2}'.format(
                                        dimage.ID/10, dimage.ID%10, trans ), anchor=Tkinter.NW, activefill='yellow')



    def drawOnCanvas(self, event):
        '''When button is released.

        '''
        if event.widget == self.canvas:
            for imN, im in enumerate(self.disp_images):
                if not im == None:
                    if im.point( (event.x, event.y) ):
                        break
            else:
                return # IF NO ASSOCIATED IMAGE IS FOUND

            if self.rb.get() == "Object Selection":
                # GET ASSOCIATED IMAGE
                print 'Drawing on image {0}.'.format(imN)

                im_pt = im.point( (event.x, event.y) )

                if event.num == 1: # LEFT MOUSE CLICK
                    if not self.mouseDrag[0]:
                        # ADD A POINT AT CLICK LOCATION
                        self.settings['polyObjs'][self.polyRef].add( im.ID, im_pt )

                        self.get_drawing()
                    else:
                        # UPDATE POSITION FOR DRAGGING POINT
    #                    dragpt = list(im.point( (event.x, event.y) ))
                        if self.mouseDrag[1] >= 0:
                            self.settings['polyObjs'][self.polyRef].move_pt( im.ID, self.mouseDrag[1], im_pt )
                        self.mouseDrag = [False, -1]
                        self.get_drawing()

                if event.num == 3: # RIGHT MOUSE CLICK
                    self.settings['polyObjs'][self.polyRef].undueAdd()
                    self.get_drawing()
            elif self.rb.get() == "Window Selection":
                cam = im.ID % 10
                imx, imy = im.point( (event.x, event.y) )
                points = self.settings['subwindows'][cam].T
                dif = sqrt((points[0]-imx)**2 + (points[1]-imy)**2)
                i = list(dif == min(dif)).index(True)
                xi = r_[0,1] if i < 2 else r_[2,3]
                self.settings['subwindows'][cam][i] = imx,imy
                self.settings['subwindows'][cam][xi,0] = imx
                self.display_mask()


            self.refreshPolygon()



    def deleteSIFTpgms(self):
        # DELETE ANY *.SIFTpgm FILES IN DIRECTORY
        dirList = os.listdir(os.getcwd())
        for fname in reversed(dirList):
            try:
                if os.path.splitext(fname)[1] == '.SIFTpgm':
                    os.remove(fname)
            except WindowsError:
                continue



    def frame(self, *arg):
        if len(arg) == 1:
            assert isinstance(arg[0], int), 'Invalid frame number!'
            self.imNumStrVar.set(arg[0])
        return int(self.imNumStrVar.get())
    def camera(self, *arg):
        if len(arg) == 1:
            assert isinstance(arg[0], int) and arg[0] in range(6), 'Invalid camera number!'
            self.camNumStrVar.set(arg[0])
        return int(self.camNumStrVar.get())



    def frameID(self, s='CURR'):
        '''Returns the ID number for adjacent frames:
            CURR (default), NEXT, PREV, L, R
        Does not alter any outside variables.
        '''
        imN, camN = self.frame(), self.camera()
        if isinstance(s, int):
            return (imN+s)*10+camN
        if s == 'CURR':
            return imN*10+camN
        if s == 'NEXT':
            return (imN+1)*10+camN
        if s == 'PREV':
            return (imN-1)*10+camN
        if s == 'L':
            return imN*10+(camN+4)%5
        if s == 'R':
            return imN*10+(camN+1)%5



    def sup(self, x):
        if isinstance(x,list):
            for i, each in enumerate(x):
                x[i] = each*1616./self.settings['imagesize'][1]
            return x
        return x*1616./self.settings['imagesize'][1]
    def sdown(self, x):
        if isinstance(x,list):
            for i, each in enumerate(x):
                x[i] = each*self.settings['imagesize'][1]/1616.
            return x
        return x*self.settings['imagesize'][1]/1616.



    def loadLadybugSDKhelp(self):
        print 'Opening SDK help'
        os.startfile(r'C:\Program Files\Point Grey Research\PGR Ladybug\doc\Ladybug SDK Help.chm')
    def openWorkingDir(self):
        print 'Opening current working directory'
        os.startfile(os.getcwd())
    def set_work_dir(self):
        self.settings['dir_work'] = askdirectory(title='Choose a directory to store all session related files')

    def save_session(self, latest=False):
        # UPDATE settings DICT BEFORE SAVING
        self.settings['imNumStrVar'] = self.imNumStrVar.get()
        self.settings['camNumStrVar'] = self.camNumStrVar.get()
        self.settings['geometry'] = self.geometry()
        self.settings['mode'] = self.mode.get()
        if not os.path.exists(self.run_location + '\\sessions_config'):
            os.mkdir(self.run_location + '\\sessions_config')
        if latest:
            sess_fname = self.run_location + '\\sessions_config\\most_recent.pkl'
        else:
            sess_fname = str(asksaveasfilename(initialdir=(self.run_location + '\\sessions_config'), filetypes=[("Python (Pickled) file","*.pkl")]))
        if not sess_fname.endswith('.pkl'):
            sess_fname += '.pkl'
        settingscopy = self.settings.copy()
        del settingscopy['polyObjs']
        self.print_settings( 'Settings on exit:' )
        with open( sess_fname, 'w') as wfile:
            pickle.dump(settingscopy, wfile)
        wfile.close()


    def load_session(self, latest=False):
        print 'items in config', len(self.settings)
        if not os.path.exists(self.run_location + '\\sessions_config'):
            os.mkdir(self.run_location + '\\sessions_config')
        if latest:
            sess_fname = self.run_location + '\\sessions_config\\most_recent.pkl'
        else:
            sess_fname = str(askopenfilename(initialdir=(self.run_location + '\\sessions_config'), filetypes=[("Python (Pickled) file","*.pkl")]))

        try:
            with open( sess_fname, 'r' ) as rfile:
                self.settings = pickle.load(rfile)
            rfile.close()
            self.settings['polyObjs'] = [PO()]
        except IOError:
            print 'Load session cancelled.'
            return

        self.imNumStrVar.set( self.settings.get('imNumStrVar') )
        self.camNumStrVar.set( self.settings.get('camNumStrVar') )
        self.forwardStrVar.set( str(self.settings.get('im_forward')) +
                                ' ' + str(self.settings.get('panorama_forward')) )
        self.geometry( self.settings.get('geometry') )
        self.mode.set( self.settings.get('mode') )
        resizeparam = namedtuple('resizeparam', 'width height')
        resizeparam = resizeparam(width=self.settings.get('maxWidth'), height=self.settings.get('maxHeight'))
        self.resize( resizeparam )
        self.update()
        self.PGRstream = Ladybug3stream( self.settings.get('dir_stream') )
        self.totalStrVar.set( self.PGRstream.getNumberOfFrames() )
        self.image_manager( int(self.settings.get('imNumStrVar')) )
        self.get_thumbs()
        self.refresh_display()


    def print_settings(self, string):
        print string + ':'
        for k in self.settings:
            print '\t', k, ':', self.settings[k]

    def test(self):
        self.PGRstream.test()


#===============================================================================
# DISPLAY_IMAGE CLASS
#===============================================================================
class display_image:
    '''Structure for holding an image and info on how it is displayed on screen.
    '''
    def __init__(self, image, ID, anchor=(0,0), scale=1.0, fit=(0,0)):
        '''Accepts PIL image. 'fit' overrides 'scale' if given as a parameter.
        '''
        self.ID = ID
        self.im = image
        self.size = image.size
        self.scale = scale
        self.fit = fit # SET THE RETURN SCALING BY THE AREA IT MUST FIT INSIDE
        self.anchor = anchor # WHERE TOPLEFT OF IMAGE WILL BE PLACED IN DISPLAY AREA
        self.cropbox = (0, 0, image.size[0], image.size[1]) # See PIL crop

        self.fit_scale() # OVERRIDES SCALE PARAMETER IF FIT IS SET



    def set_box(self, box):
        '''Set the display region of image.

        Arg is a 4-tuple defining the left, upper, right, and lower pixel
        coordinate. Same as in the crop method of PIL Image class.
        '''
        assert box[0] >=0 and box[1] >= 0
        assert box[2] <= self.size[0] and box[3] <= self.size[1]
        self.cropbox = box
        self.fit_scale()



    def set_fit(self, dxdy):
        '''Set desired size in pixels of final return image.

        @arg dxdy: A tuple giving the desired width and height.
        '''
        assert dxdy[0] > 0 and dxdy[1] > 0
        self.fit = tuple(dxdy)
        self.fit_scale()



    def fit_scale(self):
        if self.fit[0] > 0 and self.fit[1] > 0:
            cropsize = (self.cropbox[2] - self.cropbox[0], self.cropbox[3] - self.cropbox[1])
            self.scale = min(self.fit[0] / float(cropsize[0]), self.fit[1] / float(cropsize[1]))



    def point(self, xy):
        '''Translates the point on display window to pixel coordinate of whole
        image. Returns False if point is not within image.

        This method can be used to test if a clicked point was on this image.
        Can use this method to retrieve the image coordinate of a clicked point.
        '''
        axy = self.anchor
        cxy = (self.cropbox[0] * self.scale, self.cropbox[1] * self.scale)
        boxspan = self.box_span()
        for i in xrange(2):
            if xy[i] < self.anchor[i] or xy[i] > self.anchor[i] + boxspan[i]:
                return False
        # SUBTRACT ANCHOR COORD, REVERSE SCALING, AND ADD CROPPED DISTANCE BACK
        retval = ((xy[0] - axy[0] + cxy[0])/self.scale,
                  (xy[1] - axy[1] + cxy[1])/self.scale )
        return retval



    def box_span(self):
        return (int((self.cropbox[2] - self.cropbox[0])*self.scale),
                int((self.cropbox[3] - self.cropbox[1])*self.scale))



    def image(self, Tk=True):
        '''Retrieve a copy of the cropped and resized portion of this image.

        Default is to return a Tkinter compatible image.

        @kwarg Tk: True for Tkinter image, False for PIL
        '''
        self.imcopy = self.im.crop(self.cropbox)
        self.imcopy.thumbnail(tuple([int(each * self.scale) for each in self.size]))
        if Tk == True:  self.imcopy = ImageTk.PhotoImage(self.imcopy)
        return self.imcopy


    def to_disp_pt(self, pt):
        '''Scale down and offset image points for display. Image point -> Disp point.

        '''
        axy = self.anchor
        cxy = (self.cropbox[0], self.cropbox[1])
        return (pt[0]*self.scale - cxy[0]*self.scale + axy[0], pt[1]*self.scale - cxy[1]*self.scale + axy[1])


    def get_texture(self, poly, polydest):
        out_texture = self.im.copy()



        out_texture = perspective_transform(out_texture, poly+polydest )

        mask = Image.new('L', out_texture.size, color=0)
        draw = ImageDraw.Draw(mask)
        draw.polygon(polydest, fill=255)
        out_texture.putalpha(mask)


        out_texture = out_texture.crop(self.cropbox)
        out_texture.thumbnail(tuple([int(each * self.scale) for each in self.size]))

        out_texture = ImageTk.PhotoImage(out_texture)
        return out_texture
#        out_texture.show()




#===============================================================================
# END OF DISPLAY_IMAGE CLASS
#===============================================================================




def filename(*args):
    '''Converts an image ID or the pair of frame & cam into a filename.
    '''
    if len(args) == 1:
        return r'*_Frame{0:0>8}_Cam{1}'.format( args[0]/10, args[0]%10 )
    elif len(args) == 2:
        return r'*_Frame{0:0>8}_Cam{1}'.format( args[0], args[1] )
    else:
        raise TypeError, 'Requires 1 or 2 arguments'


def perspective_transform(image, ptop, cam_rotate = 0, alpha=True):
    '''This method performs a perspective transform on the supplied image.
    Input: image = source image to transform
           ptop = four source and four corresponding destination coordinates
    '''
#    image = image.rotate(cam_rotate)

    # CALCULATE THE TRANSFORMATION MATRIX
    b0,b1,b2,b3,a0,a1,a2,a3 = ptop

    A = array([[a0[0], a0[1], 1,     0,     0, 0, -a0[0]*b0[0], -a0[1]*b0[0]],
               [    0,     0, 0, a0[0], a0[1], 1, -a0[0]*b0[1], -a0[1]*b0[1]],
               [a1[0], a1[1], 1,     0,     0, 0, -a1[0]*b1[0], -a1[1]*b1[0]],
               [    0,     0, 0, a1[0], a1[1], 1, -a1[0]*b1[1], -a1[1]*b1[1]],
               [a2[0], a2[1], 1,     0,     0, 0, -a2[0]*b2[0], -a2[1]*b2[0]],
               [    0,     0, 0, a2[0], a2[1], 1, -a2[0]*b2[1], -a2[1]*b2[1]],
               [a3[0], a3[1], 1,     0,     0, 0, -a3[0]*b3[0], -a3[1]*b3[0]],
               [    0,     0, 0, a3[0], a3[1], 1, -a3[0]*b3[1], -a3[1]*b3[1]]] )
    B = array([b0[0], b0[1], b1[0], b1[1], b2[0], b2[1], b3[0], b3[1]])

    transdata = linalg.solve(A,B)
    H = append(transdata,1)
    H = inv(reshape(H, (3,3))).flat


    # TRANSFORM THE IMAGE WITH SIZE BASED ON DESTINATION COORDINATES
    S = image.size
    tl = (H[2])/(1),(H[5])/(1)
    bl = (H[1]*S[1]+H[2])/(H[7]*S[1]+1),(H[4]*S[1]+H[5])/(H[7]*S[1]+1)
    tr = (H[0]*S[0]+H[2])/(H[6]*S[0]+1),(H[3]*S[0]+H[5])/(H[6]*S[0]+1)
    br = (H[0]*S[0]+H[1]*S[1]+H[2])/(H[6]*S[0]+H[7]*S[1]+1),(H[3]*S[0]+H[4]*S[1]+H[5])/(H[6]*S[0]+H[7]*S[1]+1)

    xmax = max(tl[0],bl[0],tr[0],br[0])
    xmin = min(tl[0],bl[0],tr[0],br[0])
    ymax = max(tl[1],bl[1],tr[1],br[1])
    ymin = min(tl[1],bl[1],tr[1],br[1])
    size = ( int(xmax-xmin), int(ymax-ymin)*2 )
    S = (1000,600)

    transimage = image.transform(S, Image.PERSPECTIVE, transdata)

    # RETURN TRANSFORMED IMAGE
    return transimage



def get_transform_data(pts8, backward=True ):
    '''This method returns a perspective transform 8-tuple (a,b,c,d,e,f,g,h).

    Use to transform an image:
    X = (a x + b y + c)/(g x + h y + 1)
    Y = (d x + e y + f)/(g x + h y + 1)

    Image.transform: Use 4 source coordinates, followed by 4 corresponding
        destination coordinates. Use backward=True (the default)

    To calculate the destination coordinate of a single pixel, either reverse
        the pts (4 dest, followed by 4 source, backward=True) or use the same
        pts but set backward to False.

    @arg pts8: four source and four corresponding destination coordinates
    @kwarg backward: True to return coefficients for calculating an originating
        position. False to return coefficients for calculating a destination
        coordinate. (Image.transform calculates originating position.)
    '''
    assert len(pts8) == 8, 'Requires a tuple of eight coordinate tuples (x,y)'

    b0,b1,b2,b3,a0,a1,a2,a3 = pts8 if backward else pts8[::-1]

    # CALCULATE THE COEFFICIENTS
    A = array([[a0[0], a0[1], 1,     0,     0, 0, -a0[0]*b0[0], -a0[1]*b0[0]],
               [    0,     0, 0, a0[0], a0[1], 1, -a0[0]*b0[1], -a0[1]*b0[1]],
               [a1[0], a1[1], 1,     0,     0, 0, -a1[0]*b1[0], -a1[1]*b1[0]],
               [    0,     0, 0, a1[0], a1[1], 1, -a1[0]*b1[1], -a1[1]*b1[1]],
               [a2[0], a2[1], 1,     0,     0, 0, -a2[0]*b2[0], -a2[1]*b2[0]],
               [    0,     0, 0, a2[0], a2[1], 1, -a2[0]*b2[1], -a2[1]*b2[1]],
               [a3[0], a3[1], 1,     0,     0, 0, -a3[0]*b3[0], -a3[1]*b3[0]],
               [    0,     0, 0, a3[0], a3[1], 1, -a3[0]*b3[1], -a3[1]*b3[1]]] )
    B = array([b0[0], b0[1], b1[0], b1[1], b2[0], b2[1], b3[0], b3[1]])

    return linalg.solve(A,B)


def transform_pt(pt , coeffs ):
    T = coeffs
    x = (T[0]*pt[0] + T[1]*pt[1] + T[2])/(T[6]*pt[0] + T[7]*pt[1] + 1)
    y = (T[3]*pt[0] + T[4]*pt[1] + T[5])/(T[6]*pt[0] + T[7]*pt[1] + 1)
    return x,y



def ladybug_interp_data( data ):
    '''Interpolates between each 'new' GPS coordinate. Repeated coordinates are
    assumed to be incorrect/inaccurate. This method replaces all repetitions
    with interpolated coordinates in place. This method uses cubic spline
    interpolation.
    '''
    for i in reversed(xrange(1,len(data['lon']))):
        if data['lon'][i] == data['lon'][i-1]:
            data['lon'][i] = 1000.0
            data['valid'][i] = False
    select = where(data['lon'] < 999)

    # SPLINE VERSION
    data['alt'] = interpolate.splev(data['seqid'],
                                    interpolate.splrep(data['seqid'][select],
                                                       data['alt'][select],
                                                       s=0, k=2  ),
                                    der=0)
    data['lon'] = interpolate.splev(data['seqid'],
                                    interpolate.splrep(data['seqid'][select],
                                                       data['lon'][select],
                                                       s=0, k=2  ),
                                    der=0)
    data['lat'] = interpolate.splev(data['seqid'],
                                    interpolate.splrep(data['seqid'][select],
                                                       data['lat'][select],
                                                       s=0, k=2  ),
                                    der=0)
    return data


def ladybug_calc_dist( data, keyname='distance'):
    '''This method adds a new key to the data dictionary. Each index contains
    the distance in meters to the next index.
    '''
    lat = data['lat']
    lon = data['lon']

    db = zeros(len(lat), dtype=[('distance', float),('bearing', float)])


    for i in xrange(len(lat) - 1):
        d = calc_dist_haver( lat[i], lon[i], lat[i+1], lon[i+1] )
        b = calc_bearing( lat[i], lon[i], lat[i+1], lon[i+1] )
        db[i] = d,b

    return db


def calc_dist_cos( lat1, lon1, lat2, lon2 ):
    '''Calculates the distance between to coordinates using the 'spherical law
    of cosines'. Distance in meters.
    '''
    R = 6371.0 # EARTH RADIUS km

    d = arccos( sin(lat1 * pi/180)*sin(lat2 * pi/180)
                + cos(lat1 * pi/180)*cos(lat2 * pi/180)
                * cos(lon2 * pi/180-lon1 * pi/180) ) * R

    return d * 1000 # CONVERT KM TO METERS


def calc_dist_haver( lat1, lon1, lat2, lon2 ):
    '''Calculates the distance between to coordinates using the 'haversine'
    formula. Distance is in meters.
    '''
    R = 6371.0 # EARTH RADIUS km

    dLat = (lat2 - lat1) * pi/180
    dLon = (lon2 - lon1) * pi/180
    lat1 = lat1 * pi/180
    lat2 = lat2 * pi/180

    a = (sin(dLat/2) * sin(dLat/2) + sin(dLon/2) * sin(dLon/2) * cos(lat1) * cos(lat2))
    c = 2 * arctan2( sqrt(a),  sqrt(1-a) )
    d = R * c

    return d * 1000 # CONVERT KM TO METERS



def calc_bearing( lat1, lon1, lat2, lon2 ):
    dLon = (lon2 - lon1) * pi/180
    lat1 = lat1 * pi/180
    lat2 = lat2 * pi/180
    y = sin(dLon) * cos(lat2)
    x = cos(lat1)*sin(lat2) - sin(lat1)*cos(lat2)*cos(dLon)
    bearing = arctan2(y, x) * 180/pi
    return (bearing + 360) % 360


def calc_latlon( lat1, lon1, distance, bearing ):
    R = 6371.0 # EARTH RADIUS km
    d = distance / 1000 # Convert to km
    brng = bearing * pi/180 # Convert to rad
    lat1 = lat1 * pi/180
    lon1 = lon1 * pi/180

    lat2 = arcsin( sin(lat1)*cos(d/R) + cos(lat1)*sin(d/R)*cos(brng) )
    lon2 = lon1 + arctan2(sin(brng)*sin(d/R)*cos(lat1), cos(d/R)-sin(lat1)*sin(lat2))
    return lat2 * 180/pi, lon2 * 180/pi


def intersect_4pt(pts ):
    '''Accepts a list: x1, y1, x2, y2, x3, y3, x4, y4
    1 and 2 denote one line, 3 and 4 are the other line.
    '''
    x1, y1, x2, y2, x3, y3, x4, y4 = pts
    m1 = (y2-y1)/float(x2-x1)
    m3 = (y4-y3)/float(x4-x3)

    # SKIP LINES THAT HAVE SIMILAR SLOPES
    # TODO: CONTINUE
    angle = abs(arctan(m1)*180/pi - arctan(m3)*180/pi)
    ydiff = abs(y4-y2)
    if angle < 25: return
    X = (m3*x3 - y3 - m1*x1 + y1)/float(m3 - m1)
    Y = m1*(X - float(x1)) + float(y1)
    if isnan(X) or isnan(Y): return
    return X,Y, angle-ydiff



def hello():
    print 'Please assign this option'





if __name__ == '__main__':
    app = ladybug3D_app(None)
    app.title('Ladybug3 3D')
    app.mainloop()
