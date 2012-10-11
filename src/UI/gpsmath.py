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
:SINCE: Wed Sep 19 17:03:15 2012
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
__date__ = 'Wed Sep 19 17:03:15 2012'
__version__ = '0.1'

#===============================================================================
# IMPORT STATEMENTS
#===============================================================================
from numpy import *  # IMPORTS ndarray(), arange(), zeros(), ones()
from scipy import interpolate
#===============================================================================
# METHODS
#===============================================================================




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
