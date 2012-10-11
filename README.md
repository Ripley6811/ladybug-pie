Project: ladybug-pie
====================
Author: Jay W Johnson

Description:
Python wrapper for Ladybug3 Spherical Camera API.

### Ladybug (Package)
#### interface.py
#### API.py
* class LadybugAPI
  Access to pythonified ladybug.dll methods
  Memory management tasks are handled by the class
  Data written by the method are returned by the method
  instead of returning an error code
#### enums.py
#### structures.py
    

Only those that handle pre-existing *.pgr files have been wrapped. Methods for controlling the camera and recording video have not been wrapped. The software that comes with the camera is good enough for recording video.



TODO:
-Wrap remaining methods for use in real-time applications.
