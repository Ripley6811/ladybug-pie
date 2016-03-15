Project: ladybug-pie
====================
Author: Jay W Johnson

Description:
Python wrapper for Ladybug3 Spherical Camera API.

Required:
Ladybug3 Spherical Camera API (ladybug.dll) installed which is included with the camera. Many modules and methods could be use with other cameras and projects.

Only the methods that handle pre-recorded *.pgr files have been wrapped. Methods for controlling the camera and recording video have not been wrapped. The software that comes with the camera is good enough for recording video.


***
**Ladybug_3D_mainGUI.py**
* `ladybug3D_app` class

    Main program that sets up the GUI and event handling.
    
    ![alt tag](https://dl.dropboxusercontent.com/u/49722688/images/optic_flow.png)

***
Ladybug package
---------------
**interface.py**
* `Ladybug3stream` class

    Simplifies management of a *.pgr stream file and adds additional methods not included in the Ladybug API.

**API.py**
* `LadybugAPI` class

    Access to pythonified ladybug.dll methods.
    Memory management tasks are handled by the class.
    Data written by the methods are returned by the method instead of returning an error code.

***
SFM package
-----------
**opticflow.py**
* `FeatureMatcher` class

    Implements OpenCV's FeatureDetector_create, Descriptor_create, and flann_index methods to do feature detection and matching over a series of images.
    
    TODO: Still needs some testing and clean-up.

**online_SLAM**
* `SLAM` class

    Based on the SLAM algorithm introduced in Udacity's robot car course.
    
    Changed to make it easy to add positions and measurements. 'Online' SLAM is optional; the removal of old positions is done with a method call.


