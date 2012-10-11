#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
(SUMMARY)

(DESCRIPTION)

@SINCE: Wed Aug 08 16:14:54 2012
@VERSION: 0.1
@STATUS: Nascent
@CHANGE: ...
@TODO: ...

@REQUIRES: ...
@PRECONDITION: ...
@POSTCONDITION: ...

@AUTHOR: Ripley6811
@ORGANIZATION: National Cheng Kung University, Department of Earth Sciences
@CONTACT: tastethejava@hotmail.com
"""
#===============================================================================
# PROGRAM METADATA
#===============================================================================
__author__ = 'Ripley6811'
__contact__ = 'tastethejava@hotmail.com'
__copyright__ = ''
__license__ = ''
__date__ = 'Wed Aug 08 16:14:54 2012'
__version__ = '0.1'

#===============================================================================
# IMPORT STATEMENTS
#===============================================================================
from numpy import *
import random
import cv2
from numpy import min,max

#===============================================================================
# METHODS
#===============================================================================

def encode6(P, toDegrees=False):
    '''Encodes a projection matrix into [Rx,Ry,Rz,Tx,Ty,Tz].'''
    R,t = P[:3,:3], P[:3,3]
    chromosome = r_[cv2.Rodrigues(R)[0].flatten(), t.flatten() ]
    if toDegrees:
        chromosome[:3] *= (180./pi)
    return chromosome

def decode6(chromosome, fromDegrees=False):
    '''Returns a 4x4 projection matrix from [Rx,Ry,Rz,Tx,Ty,Tz].'''
    if fromDegrees:
        chromosome[:3] *= (pi/180.)
    [R,t] = cv2.Rodrigues(chromosome[:3])[0], chromosome[3:]
    H = eye(4)
    H[:3,:3] = R
    H[:3,3] = t
    return H

def encode6b(Tr):
    r,t = cv2.decomposeProjectionMatrix(Tr[:3])[1:3]
    return r_[cv2.Rodrigues(r)[0].flatten(), t.flat[:3]/t[3]]

def decode6b(dna):
    t = eye(4)
    t[:3,3] = -dna[3:6]
    r = eye(4)
    r[:3,:3] = cv2.Rodrigues(dna[:3])[0]
    return dot(r,t)

def encode5(P, scale=None):
    '''Encodes a projection matrix into [Rx,Ry,Rz,Taz,Tel,Tscale].'''
    R = P[:3,:3]
    t = getTazel(P[:3,3])
    chromosome = r_[cv2.Rodrigues(R)[0].flat[:], t]
    if scale != None:
        chromosome[5] = scale
    return chromosome

def decode5(chromosome):
    '''Returns a 4x4 projection matrix from [Rx,Ry,Rz,Taz,Tel,Tscale].'''
    [R,t] = cv2.Rodrigues(chromosome[:3])[0], getTxyz(chromosome[3:6])
    H = eye(4)
    H[:3,:3] = R
    H[:3,3] = t
    return H

def encode5s(P, sigma=pi/18.): # sigma = 10 degrees
    '''Encodes a projection matrix into [Rx,Ry,Rz,Taz,Tel,Tscale,Sigma].'''
    R = P[:3,:3]
    t = getTazel(P[:3,3])
    chromosome = r_[cv2.Rodrigues(R)[0].flat[:], t, sigma]
    if sigma != None:
        chromosome[6] = sigma
    return chromosome

def decode5s(chromosome):
    '''Returns a 4x4 projection matrix from [Rx,Ry,Rz,Taz,Tel,Tscale,Sigma].'''
    [R,t] = cv2.Rodrigues(chromosome[:3])[0], getTxyz(chromosome[3:6])
    H = eye(4)
    H[:3,:3] = R
    H[:3,3] = t
    return H

def encode5sb(P, sigma=pi/18.): # sigma = 10 degrees
    '''Encodes a projection matrix into [Rx,Ry,Rz,Taz,Tel,Tscale,Sigma].'''
    dna = ones(7)
    dna[:6] = encode6b(P)
    dna[3:6] = getTazel(dna[3:6])
    if sigma != None:
        dna[6] = sigma
    return dna

def decode5sb(dna):
    '''Returns a 4x4 projection matrix from [Rx,Ry,Rz,Taz,Tel,Tscale,Sigma].'''
    dna = r_[dna[:3], getTxyz(dna[3:6])]

    return decode6b(dna)

def encode3x5s(P): # sigma = 10 degrees
    '''Encodes a projection matrix into [Rx,Ry,Rz,Taz,Tel,Tscale].'''
    dna = r_[[encode5sb(each) for each in P]]
    return dna

def decode3x5s(dna):
    '''Returns a 4x4 projection matrix from [Rx,Ry,Rz,Taz,Tel,Tscale].'''
    P = r_[[decode5sb(each) for each in dna]]

    return P

def getTxyz(az, el=None, r=1.):
    if el == None:
        if len(az) == 2:
            az, el = az
        if len(az) == 3:
            az, el, r = az
    y = r * cos(el) * sin(az)
    x = r * cos(el) * cos(az)
    z = r * sin(el)
    return x,y,z

def getTazel(x, y=None, z=None):
    if y == None:
        x,y,z = x
    r = sqrt(x**2 + y**2 + z**2)
    el = arcsin(z/r)
    az = arccos(x/(r*cos(el)))
    if y < 0:
        az = 2*pi - az
    return az, el, r

def E( individual ):
    return dot(T(individual), R(individual))

def T(individual):
    x,y,z = getTxyz( individual[3:6] )
    return array([[0, -z, y],[z, 0, -x],[-y, x, 0]])

def R(individual):
    return cv2.Rodrigues(individual[:3])[0]



def dist(x0, x1, P=None, F=None):
    '''Summation of the distance between points and corresponding epipolar
    lines in both directions.

    Points near epipole are excluded
    New points are the closest ones on the epipolar line to the old points.
    '''
    if F == None:
        F = E(P)
    epiHole = mask_pts_near_epipole(x0, x1, F=F)

    pts1 = x0[:,epiHole].copy()
    pts2 = x1[:,epiHole].copy()

    L2 = dot(F,pts1)
    L1 = array([-L2[1]/L2[0], -ones(len(L2[0])), L2[1]*pts2[0]/L2[0] + pts2[1]])
    newpts = cross(L2, L1, axis=0)
    newpts /= newpts[2]
    d0 = sum(sqrt((pts2[0]-newpts[0])**2 + (pts2[1]-newpts[1])**2))

    L2 = dot(F.T,pts2)
    L1 = array([-L2[1]/L2[0], -ones(len(L2[0])), L2[1]*pts1[0]/L2[0] + pts1[1]])
    newpts = cross(L2, L1, axis=0)
    newpts /= newpts[2]
    d1 = sum(sqrt((pts1[0]-newpts[0])**2 + (pts1[1]-newpts[1])**2))

    return d0+d1

def mask_pts_near_epipole(pts1, pts2, P=None, cutoff=0.1, F=None):
    if F == None:
        F = E(P)
    epipole = cv2.SVDecomp(F.T)[2][-1]
    epipole /= epipole[2]

    d0 = (pts1.T - epipole).T
    d0 = sqrt(sum(d0**2,0)) > cutoff

    epipole = cv2.SVDecomp(F)[2][-1]
    epipole /= epipole[2]

    d1 = (pts2.T - epipole).T
    d1 = sqrt(sum(d1**2,0)) > cutoff

    return d0 & d1



def test_heading(expected_heading, test_heading):
    '''Test heading must be in Ladybug coordinate system.

    Move to a Ladybug module?'''
    # IF HEADING IS AN INTEGER, THEN ASSUME IT IS CAMERA NUMBER AND CONVERT TO RADIANS
    if isinstance(expected_heading, int):
        expected_heading = 2*pi - (2*pi/5.) * expected_heading

    headings = r_[test_heading, expected_heading]
    headingdiff = max(headings - min(headings))
    if headingdiff > pi: headingdiff = 2*pi - headingdiff
    if headingdiff < pi/5.: # 72 degree span
        return True
    return False

def mean_bearing(b1, b2):
    bs = r_[b1,b2]
    angle = max(bs - min(bs))
    if angle < pi:
        return (angle/2.)+min(bs)
    if angle > pi:
        return ((2*pi + angle)/2. + min(bs))%(2*pi)


def test_triangulation_gdpts(P, x0, x1):
    H = linalg.inv(decode5(P))

    # TRIANGULATE POINTS
    X = cv2.triangulatePoints( eye(4)[:3], H[:3], x0[:2], x1[:2] )
    X /= X[3]

    # TEST REPROJECTION TO IMAGE PLANE
    x0 = dot(eye(4)[:3], X)[2] > 0.
    x1 = dot(H[:3], X)[2] > 0.
    infront = x0 & x1

    return (100*sum(infront))/len(infront), sum(infront), len(infront)

def test_vector_flow(a,b,c,max_angle=pi/32):
    '''Tests a contiguous set of matches. The difference in angle between a-b
    and b-c must be less than 'max_angle'. Default is difference of 36 degrees.
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
    scalings = sqrt(sum(bc[:2]**2,0))/sqrt(sum(ab[:2]**2,0))
#    print 'scales', scalings
    meanscale = mean(sqrt(sum(bc[:2,nonzero]**2,0))/sqrt(sum(ab[:2,nonzero]**2,0)))
#    print 'scale mean', meanscale
    stdscale = std(sqrt(sum(bc[:2,nonzero]**2,0))/sqrt(sum(ab[:2,nonzero]**2,0)))
#    print 'scale std', stdscale
    gdscale = (scalings >= (meanscale-stdscale)) & (scalings <= (meanscale+stdscale))
#    print 'gd scales', gdscale
#    print 'better mean', mean(scalings[gdscale])
#    print 'good vectors', sum(gdvecs), '(', len(gdvecs), ')'

    return gdvecs & gdscale

def mutate(pop, sigma=pi/32.):
    '''Population is an N by 6 array of encoded translations.'''
    i = random.choice(range(5))
    pop.T[i] = random.gauss(pop.T[i], sigma)
#    pop[:5] = random.gauss(pop[:5], sigma)
    return pop

def mutate2(pop, sigma=pi/180.):
    for i in random.sample(arange(5*3)%5,3):
#        print random.gauss(0, sigma), sigma
        pop[i] = random.gauss(pop[i], sigma)
    return pop

def crossover( fu, mu ):
    # SELECT A BREAK POINT
#    i = random.randrange(7)
    i = 3
    # RETURN OFFSPRING
    return mutate2( r_[fu[:i],mu[i:]] )

def crossover2( fu, mu ):
    # SELECT A BREAK POINT
    i = r_[[random.choice((True,False)) for i in range(6)]]
    child = fu.copy()
    child[i] = mu[i]
    # RETURN OFFSPRING
    return mutate2( child, pi/32 )




def crossover_S( fu, mu ):
    # SELECT A BREAK POINT
    i = random.randrange(7)
    # RETURN OFFSPRING
    return mutate_S( r_[fu[:i],mu[i:]])#,min(abs(fu[6]),abs(mu[6]))] )

def mutate_S(pop, number_mutations=2, sigma=pi/450.): # sigma = 0.4 degrees
    # SELECT INDICES FROM FIRST FIVE TO MUTATE
    for i in random.sample(arange(5*number_mutations)%5,number_mutations):
#        print random.gauss(0, sigma), sigma
        pop[i] = random.gauss(pop[i], pop[6])
    # MUTATE SIGMA
    pop[6] = abs(random.gauss(pop[6], sigma))
    return pop

def breed_pop_S( breeders, how_many ):
    N = how_many
    retpop = zeros((N,breeders.shape[1]), float)
    for i in range(N):
        fu,mu = random.sample(breeders, 2)
        retpop[i] = crossover_S( fu, mu )
    return retpop.copy()




def breed_pop( breeders, how_many ):
    N = how_many

    retpop = zeros((N,breeders.shape[1]), float)
    for i in range(N):
        fu,mu = random.sample(breeders, 2)
        retpop[i] = crossover( fu, mu )

    return retpop.copy()


def GA_refine_single_projection(LPA, cam, x3a, x3b, front_cam=None,
                                iters=100, popsize=100, repeat=True,
                                prev=[], fitstop=0.01):
    '''Get ladybug translation from cam point correspondences.

    Repeats once if heading is not in expected range. Set repeat to False to
    only run once.

    Tried removing epipolar points for repeat run but results were often worse.
    Needs the epipolar points for calculating E from points.'''
    pop = add_genes_S(LPA, cam, x3a, x3b, popsize, front_cam=front_cam, prev=prev)
#    popout = array([100-GAP.test_triangulation_gdpts(p, x3a, x3b)[0] for p in pop])
#    for p, bad in zip(pop, popout):
#        if bad > 50: p[3:5] *= -1
#    popout = array([100-GAP.test_triangulation_gdpts(p, x3a, x3b)[0] for p in pop])
    popfit = array([dist(x3a, x3b, p ) for p in pop])

#    low = where(popfit == min(popfit))[0][0]
#    hitlist = zeros(pop.shape[0], bool)
#    hitlist[argsort(popfit)[len(pop)/2:]] = True
#    hitlist[argsort(popout)[len(pop)/2:]] = True
    breeders = r_[argsort(popfit)[:len(pop)/5],
                  argsort(popfit)[:len(pop)/5]]#,
#                  argsort(popout)[:len(pop)/5]]

#    while True:
    for i in range(iters):
        # SORT FOR REPRODUCTION. INDICES OF BEST INDIVIDUALS
        breeders = r_[argsort(popfit)[:len(pop)/5],
                      argsort(popfit)[:len(pop)/5]]#,
#                      argsort(popout)[:len(pop)/5]]
#        hitlist = zeros(pop.shape[0], bool)
#        hitlist[argsort(popfit)[(len(pop)*4)/5:]] = True
#        hitlist[argsort(popout)[len(pop)/2:]] = True
        hitlist = ones(pop.shape[0], bool)
        hitlist[argsort(popfit)[0]] = False
        # REDUCE MUTATION RANGE (SIGMA) OF BEST INDIVIDUAL
        pop[hitlist == False, 6] *= 0.9
        # REPRODUCE
        newpop = breed_pop_S( pop[breeders], sum(hitlist) )
        # FITNESS IS BASED ON TRIPLE MATCH POINTS
        newfit = array([dist(x3a, x3b, p ) for p in newpop])
        # INLIERS IS BASED ON DOUBLE MATCH POINTS
#        newout = array([100-GAP.test_triangulation_gdpts(p, x3a, x3b)[0] for p in newpop])
        improved = (newfit < popfit[hitlist])# & (newout <= popout[hitlist])
        hitlist[hitlist] = improved

        pop[hitlist] = newpop[improved]
        popfit[hitlist] = newfit[improved]
#        popout[hitlist] = newout[improved]
        if min(popfit) < fitstop:
            print 'iters stopped at', i
            break

    best = (popfit == min(popfit))
    print min(popfit)

    H = LPA.H_C2L(cam, decode5sb( pop[best][0] ) )
    print '>', encode5( H )
    if repeat and not test_heading(front_cam, encode5sb( H )[3] ):
        print 'repeating', encode5sb( H )[3]
        return GA_refine_single_projection(LPA, cam, x3a, x3b,
                                               front_cam=front_cam,
                                iters=iters, popsize=popsize, repeat=False)

    return H



def GA_refine_double_projection():
    return

def H_from_Xx(LPA, cam, X, x ):
    '''Get a ladybug translation from a camera's view of the world points.'''
    if X.shape[0] == 4:
        X /= X[3]
    r,t = cv2.solvePnP(X[:3].T, x[:2].T, eye(3), empty(0))[1:3]
    r,t = r.flatten(), t.flatten()
    H = LPA.dot( LPA(cam), decode6(r_[r,t]) )
    return H






def add_genes_S(LPA, cam, Apts, Bpts, pop_size=100, scale=1.,
                prev=[], front_cam=None):
    '''Get a population of test chromosomes by calculating E from point
    correspondences and under Ladybug motion constraints.

    @return: List (array) of encoded camera translation chromosomes
    '''
    genepool = []
    print len(prev)
    for each in prev:
        try:
            print len(each), each
            if len(each) == 6:
                genepool.append( encode5sb(LPA.H_L2C(cam, decode5sb(each))) )
                genepool[-1][5] = 1.0
        except:
            continue
    print 'Genepool initialized with', len(genepool), 'genes'
#    print genepool
    while len(genepool) < pop_size:
        for H in get_H_list(Apts, Bpts):
            Lgene = encode5sb(LPA.H_C2L(cam, H))

            # TEST ROTATION, LESS THAN 22.5 DEGREES
            if sum(abs(Lgene[:3]) < pi/8) == 3:
                # TEST HEADING
                Lheading = Lgene[3]
#                print Lheading, test_heading(front_cam, Lheading)
                if front_cam != None and test_heading(front_cam, Lheading):
                    H[:3,3] *= scale
                    genepool.append( encode5sb(H) )
                elif front_cam == None:
                    H[:3,3] *= scale
                    genepool.append( encode5sb(H) )

    return array(genepool)

def get_H_list(Apts, Bpts, Nsamples=24):
    Npts = len(Apts[0])
    if Npts < Nsamples:
        Nsamples = Npts
    r = random.sample(range(Npts), Nsamples)
    E_mat, gdm = cv2.findFundamentalMat(Apts[:2,r].T, Bpts[:2,r].T)#, cv2.FM_8POINT)#, cv2.RANSAC,1,0.99)
    return H_from_E( E_mat )

def H_from_E(E, RandT=False):
    '''Returns a 4x4x4 matrix of possible H translations.
    Or returns the two rotations and translation vectors when keyword is True.
    '''
    S,U,V = cv2.SVDecomp(E)
    #TIP: Recover E by dot(U,dot(diag(S.flatten()),V))
    W = array([[0,-1,0],[ 1,0,0],[0,0,1]])

    R1 = dot(dot(U,W),V)
    R2 = dot(dot(U,W.T),V)
    if cv2.determinant(R1) < 0:
        R1,R2 = -R1,-R2
    t1 = U[:,2]
    t2 = -t1

    if RandT:
        return R1, R2, t1, t2

    H = zeros((4,4,4))
    H[:2,:3,:3] = R1
    H[2:,:3,:3] = R2
    H[[0,2],:3,3] = t1
    H[[1,3],:3,3] = t2
    H[:,3,3] = 1

    return H

#===============================================================================
# MAIN METHOD AND TESTING AREA
#===============================================================================
#def main():
#    """Description of main()"""
#    az = 3.0
#    el = 1.4
#    print az,el
#    x,y,z = getTxyz(az,el)
#    print x,y,z
#    az2,el2, r = getTazel(x,y,z)
#    print az2,el2, r
#
#    w = r_[.1,.2,.3,pi/2,pi/3,1654752.132]
#    print decode5(w)
#
#if __name__ == '__main__':
#    main()